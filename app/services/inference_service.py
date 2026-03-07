from datetime import datetime, timezone
from sqlalchemy import select
from app.models.player_state import PlayerState
from fastapi import HTTPException
from app.services.feature_assembler import FeatureAssembler
import joblib

assembler = FeatureAssembler()
model = joblib.load("app/ml/models/final_xgboost_model.pkl")


class InferenceService:
    def __init__(self):
        self.model = model
        self.assembler = assembler

    async def get_player_state(
        self, session, p_id: str, surface: str, commence_time: str
    ):
        # 1. Fetch the row from Postgres
        stmt = select(PlayerState).where(PlayerState.player_id == p_id)
        result = await session.execute(stmt)
        p = result.scalar_one_or_none()

        if not p:
            return None

        # 2. UTC Lockdown: Normalise the API match time
        # Convert 'Z' to offset, parse to UTC, and strip to a Date object
        dt_aware = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        match_date_utc = dt_aware.astimezone(timezone.utc).date()

        # 3. Dynamic Surface Routing
        # Logic: 'Hard' -> p.current_hard_elo | 'Clay' -> p.current_clay_elo
        surf_key = surface.lower()
        surf_elo = getattr(p, f"current_{surf_key}_elo", p.current_elo)
        surf_date = getattr(p, f"last_{surf_key}_match_date", p.last_match_date)

        # 4. Calculate Rust (Days Off) relative to Match Start
        # Fallback to 30 days if no history exists (prevents NaN in XGBoost)
        days_off = (
            (match_date_utc - p.last_match_date).days if p.last_match_date else 30
        )
        surf_days_off = (match_date_utc - surf_date).days if surf_date else 30

        # 5. Build the 12-feature snapshot for the Assembler
        return {
            "elo": p.current_elo,
            "surf_elo": surf_elo or p.current_elo,
            "days_off": max(0, days_off),
            "surf_days_off": max(0, surf_days_off),
            "m_win": p.rolling_match_win_pct,
            "g_win": p.rolling_game_win_pct,
            "sv_won": p.rolling_serve_won_pct,
            "ace": p.rolling_ace_per_game,
            "df": p.rolling_df_per_pt,
            "bp_s": p.rolling_bp_save_pct,
            "ret_won": p.rolling_return_won_pct,
            "fatigue": p.current_tournament_fatigue,
        }

    async def predict(
        self, session, p1_row: str, p2_row: str, surface: str, commence_time: str
    ):
        p1_stats = p1_row
        p2_stats = p2_row

        def get_vec(p1_stats, p2_stats, flip=False):
            # This order must match your Scaler's EXPECTED_FEATURES exactly
            data = {
                "p1_elo": p1_stats.current_elo,
                "p2_elo": p2_stats.current_elo,
                "p1_surf_elo": getattr(
                    p1_stats, f"current_{surface.lower()}_elo", p1_stats.current_elo
                ),
                "p2_surf_elo": getattr(
                    p2_stats, f"current_{surface.lower()}_elo", p2_stats.current_elo
                ),
                "p1_days_off": (
                    datetime.fromisoformat(commence_time.replace("Z", "+00:00")).date()
                    - p1_stats.last_match_date
                ).days
                if p1_stats.last_match_date
                else 30,
                "p2_days_off": (
                    datetime.fromisoformat(commence_time.replace("Z", "+00:00")).date()
                    - p2_stats.last_match_date
                ).days
                if p2_stats.last_match_date
                else 30,
                "p1_surf_days_off": (
                    datetime.fromisoformat(commence_time.replace("Z", "+00:00")).date()
                    - getattr(
                        p1_stats,
                        f"last_{surface.lower()}_match_date",
                        p1_stats.last_match_date,
                    )
                ).days
                if p1_stats.last_match_date
                else 30,
                "p2_surf_days_off": (
                    datetime.fromisoformat(commence_time.replace("Z", "+00:00")).date()
                    - getattr(
                        p2_stats,
                        f"last_{surface.lower()}_match_date",
                        p2_stats.last_match_date,
                    )
                ).days
                if p2_stats.last_match_date
                else 30,
                "p1_m_win": p1_stats.rolling_match_win_pct,
                "p2_m_win": p2_stats.rolling_match_win_pct,
                "p1_g_win": p1_stats.rolling_game_win_pct,
                "p2_g_win": p2_stats.rolling_game_win_pct,
                "p1_sv_won": p1_stats.rolling_serve_won_pct,
                "p1_ace_pg": p1_stats.rolling_ace_per_game,
                "p1_df_pp": p1_stats.rolling_df_per_pt,
                "p1_bp_s": p1_stats.rolling_bp_save_pct,
                "p1_ret_won": p1_stats.rolling_return_won_pct,
                "p1_fatigue": p1_stats.current_tournament_fatigue,
                "p2_sv_won": p2_stats.rolling_serve_won_pct,
                "p2_ace_pg": p2_stats.rolling_ace_per_game,
                "p2_df_pp": p2_stats.rolling_df_per_pt,
                "p2_bp_s": p2_stats.rolling_bp_save_pct,
                "p2_ret_won": p2_stats.rolling_return_won_pct,
                "p2_fatigue": p2_stats.current_tournament_fatigue,
            }
            # Use the assembler to get embeddings and final 61-feature vector
            return assembler.assemble_manual(
                p1_row.player_id, p2_row.player_id, surface, data, flip=flip
            )

        vec_norm = get_vec(p1_stats, p2_stats, flip=False)
        vec_flip = get_vec(p1_stats, p2_stats, flip=True)

        prob_v1 = model.predict_proba(vec_norm)[0][1]
        prob_v2 = 1.0 - model.predict_proba(vec_flip)[0][1]

        avg_p1_prob = (prob_v1 + prob_v2) / 2

        return {"p1_prob": avg_p1_prob, "p2_prob": (1 - avg_p1_prob)}


inference_service = InferenceService()
