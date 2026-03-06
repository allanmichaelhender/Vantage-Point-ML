from fastapi import APIRouter, HTTPException, Security
from sqlalchemy import select, or_
from datetime import datetime, timedelta
import joblib
import pandas as pd
import numpy as np
import torch

from app.api.deps import get_api_key
from app.database.session import async_session
from app.models.match import Match
from app.services.feature_assembler import FeatureAssembler

from app.schemas.predict import ManualPredictRequest, ManualPredictResponse

router = APIRouter()

# Load Models Once
model = joblib.load("app/ml/models/final_xgboost_model.pkl")
assembler = FeatureAssembler()


async def get_player_snapshot(session, player_id, surface):
    """Calculates 'Right Now' stats for a player."""

    # Get all matches to calculate Rust and Fatigue
    stmt = (
        select(Match)
        .where(or_(Match.winner_id == player_id, Match.loser_id == player_id))
        .order_by(Match.tourney_date.desc())
    )

    result = await session.execute(stmt)
    history = result.scalars().all()

    if not history:
        return None

    latest = history[0]
    is_w = latest.winner_id == player_id

    # Calculate Rust & Fatigue
    today = pd.Timestamp.now().normalize()  # Today at 00:00:00

    # ... query ...

    # 3. Force the DB date to a Timestamp and subtract
    days_off = (today - pd.Timestamp(latest.tourney_date).normalize()).days

    # 4. Surface-specific (One-liner)
    last_on_surf = next((m for m in history if m.surface == surface), None)
    surf_days_off = (
        (today - pd.Timestamp(last_on_surf.tourney_date).normalize()).days
        if last_on_surf
        else 365
    )

    recent_14 = [m for m in history if (today - m.tourney_date).days <= 14]
    fatigue = sum((m.minutes or 90) for m in recent_14)

    return {
        "elo": latest.w_elo_before if is_w else latest.l_elo_before,
        "surf_elo": latest.w_surface_elo_before
        if is_w
        else latest.l_surface_elo_before,
        "days_off": max(0, days_off),
        "surf_days_off": max(0, surf_days_off),
        "m_win": latest.w_rolling_match_win_pct
        if is_w
        else latest.l_rolling_match_win_pct,
        "g_win": latest.w_rolling_game_win_pct
        if is_w
        else latest.l_rolling_game_win_pct,
        "sv_won": latest.w_rolling_serve_won_pct
        if is_w
        else latest.l_rolling_serve_won_pct,
        "ace": latest.w_rolling_ace_per_game if is_w else latest.l_rolling_ace_per_game,
        "df": latest.w_rolling_df_per_pt if is_w else latest.l_rolling_df_per_pt,
        "bp_s": latest.w_rolling_bp_save_pct if is_w else latest.l_rolling_bp_save_pct,
        "ret_won": latest.w_rolling_return_won_pct
        if is_w
        else latest.l_rolling_return_won_pct,
        "fatigue": fatigue,
    }


@router.post(
    "/manual-predict",
    response_model=ManualPredictResponse,
    dependencies=[Security(get_api_key)],
)
async def manual_predict(data: ManualPredictRequest):
    async with async_session() as session:
        s1 = await get_player_snapshot(session, data.p1_id, data.surface)
        s2 = await get_player_snapshot(session, data.p2_id, data.surface)

        if not s1 or not s2:
            raise HTTPException(status_code=404, detail="Player history missing")

        # Symmetric Inference
        # We'll use a helper to build the 24-feature dict in the EXACT order
        def get_vec(p1, p2, flip=False):
            # This order must match your Scaler's EXPECTED_FEATURES exactly
            d = {
                "p1_elo": p1["elo"],
                "p2_elo": p2["elo"],
                "p1_surf_elo": p1["surf_elo"],
                "p2_surf_elo": p2["surf_elo"],
                "p1_days_off": p1["days_off"],
                "p2_days_off": p2["days_off"],
                "p1_surf_days_off": p1["surf_days_off"],
                "p2_surf_days_off": p2["surf_days_off"],
                "p1_m_win": p1["m_win"],
                "p2_m_win": p2["m_win"],
                "p1_g_win": p1["g_win"],
                "p2_g_win": p2["g_win"],
                "p1_sv_won": p1["sv_won"],
                "p1_ace_pg": p1["ace"],
                "p1_df_pp": p1["df"],
                "p1_bp_s": p1["bp_s"],
                "p1_ret_won": p1["ret_won"],
                "p1_fatigue": p1["fatigue"],
                "p2_sv_won": p2["sv_won"],
                "p2_ace_pg": p2["ace"],
                "p2_df_pp": p2["df"],
                "p2_bp_s": p2["bp_s"],
                "p2_ret_won": p2["ret_won"],
                "p2_fatigue": p2["fatigue"],
            }
            # Use the assembler to get embeddings and final 61-feature vector
            return assembler.assemble_manual(
                data.p1_id, data.p2_id, data.surface, d, flip=flip
            )

        vec_norm = get_vec(s1, s2, flip=False)
        vec_flip = get_vec(s2, s1, flip=True)

        prob_v1 = model.predict_proba(vec_norm)[0][1]
        prob_v2 = 1.0 - model.predict_proba(vec_flip)[0][1]

        avg_p1_prob = (prob_v1 + prob_v2) / 2

        return {
            "p1_prob": f"{avg_p1_prob:.2%}",
            "p2_prob": f"{(1 - avg_p1_prob):.2%}",
            "p1_stats": s1,
            "p2_stats": s2,
        }
