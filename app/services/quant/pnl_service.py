import pandas as pd
import joblib
import asyncio
from sqlalchemy import select
from app.database.session import async_session
from app.models.match import Match
from app.services.ml.feature_assembler import FeatureAssembler
from datetime import date


class PNLService:
    def __init__(
        self,
        initial_bankroll=1000.0,
        kelly_fraction=0.05,
        model=joblib.load("app/ml/models/XGBoost&NN.pkl"),
        model_name="XGBoost&NN",
    ):
        self.bankroll = initial_bankroll
        self.fraction = kelly_fraction
        self.max_bet_pct = 0.02
        self.model = model
        self.model_name = model_name
        self.assembler = FeatureAssembler()

    def get_bet_size(self, model_prob, odds):
        b = odds - 1
        p = model_prob
        q = 1 - p
        kelly = (b * p - q) / b
        suggested_pct = max(0, kelly * self.fraction)
        return min(suggested_pct, self.max_bet_pct)

    # Method to convert bookie odds to fair odds
    def calculate_fair_odds(self, p1_odds, p2_odds):
        if not p1_odds or not p2_odds:
            return None, None

        # 1. Get Implied Probabilities
        implied_p1 = 1 / p1_odds
        implied_p2 = 1 / p2_odds

        # 2. Calculate Total Market Juice (The Overround)
        total_implied = implied_p1 + implied_p2

        # 3. Calculate Fair Probabilities (Normalized to 100%)
        fair_prob_p1 = implied_p1 / total_implied
        fair_prob_p2 = implied_p2 / total_implied

        # 4. Convert back to Fair Decimal Odds
        fair_p1_odds = 1 / fair_prob_p1
        fair_p2_odds = 1 / fair_prob_p2

        return fair_p1_odds, fair_p2_odds

    async def run_backtest(self):
        cutoff_date = date(2025, 1, 1)
        print(f"💰 Starting Full-Tour Backtest from {cutoff_date}...")

        async with async_session() as session:
            # Fetch matches with any odds (PS preferred, B365 fallback)
            stmt = (
                select(Match)
                .where(
                    (Match.ps_w.isnot(None)) | (Match.b365_w.isnot(None)),
                    Match.w_elo_before.isnot(None),
                    Match.tourney_date >= cutoff_date,
                    Match.w_matches_played >= 10,
                    Match.l_matches_played >= 10,
                    Match.is_retirement == False
                )
                .order_by(Match.tourney_date, Match.match_num)
            )

            result = await session.execute(stmt)
            matches = result.scalars().all()

            history = []
            current_balance = self.bankroll

            for m in matches:
                # We use symmetric inference
                x_norm = self.assembler.assemble_match(m, flip=False)
                x_flip = self.assembler.assemble_match(m, flip=True)

                if x_norm is None or x_flip is None:
                    continue

                if self.model_name == "XGBoost&NN":
                    # Probability P1 wins from both perspectives
                    p1_v1 = self.model.predict_proba(x_norm)[0][1]
                    p1_v2 = 1.0 - self.model.predict_proba(x_flip)[0][1]

                elif self.model_name in ["XGBoost", "Logistic"]:
                    features = [
                        "p1_elo",
                        "p2_elo",
                        "p1_surf_elo",
                        "p2_surf_elo",
                        "p1_days_off",
                        "p2_days_off",
                        "p1_surf_days_off",
                        "p2_surf_days_off",
                        "p1_m_win",
                        "p2_m_win",
                        "p1_g_win",
                        "p2_g_win",
                        "p1_sv_won",
                        "p1_ace_pg",
                        "p1_df_pp",
                        "p1_bp_s",
                        "p1_ret_won",
                        "p1_fatigue",
                        "p2_sv_won",
                        "p2_ace_pg",
                        "p2_df_pp",
                        "p2_bp_s",
                        "p2_ret_won",
                        "p2_fatigue",
                    ]
                    x_norm = self.assembler.assemble_match(m, flip=False)
                    x_norm = x_norm[features]
                    x_flip = self.assembler.assemble_match(m, flip=True)
                    x_flip = x_flip[features]

                    if x_norm[features].isnull().values.any():
                        # Find the specific column names that contain the NaNs
                        nan_columns = x_norm.columns[x_norm.isna().any()].tolist()
                        
                        print(f"\n❌ NaN detected in Match ID: {m.id} ({m.winner_name} vs {m.loser_name})")
                        print(f"Affected Features: {nan_columns}")
                        
                        # 🎯 2. Print the actual values for those columns to see what's happening
                        # Using .to_dict() often makes it easier to read in the terminal
                        print("Row Data:", x_norm[nan_columns].to_dict(orient='records'))

                    p1_v1 = self.model.predict_proba(x_norm)[0][1]
                    p1_v2 = 1.0 - self.model.predict_proba(x_flip)[0][1]

                elif self.model_name == "NN":
                    p1_v1 = m.nn_p1_prob # NN is already symmetric
                    p1_v2 = m.nn_p1_prob

                p1_prob = (p1_v1 + p1_v2) / 2
                p2_prob = 1.0 - p1_prob

                # Selecting market odds
                p1_odds = m.ps_w if m.ps_w else m.b365_w
                p2_odds = m.ps_l if m.ps_l else m.b365_l

                p1_market, p2_market = self.calculate_fair_odds(p1_odds, p2_odds)

                # Betting logic
                bet_placed = False
                is_win = False
                pnl = 0
                bet_on = "None"
                bet_amount = 0

                if p1_prob > (1 / p1_market):
                    bet_amount = (
                        current_balance * self.get_bet_size(p1_prob, p1_market)
                    )
                    pnl = (p1_market - 1) * bet_amount
                    is_win = True
                    bet_on = "P1"
                    bet_placed = True
                elif p2_prob > (1 / p2_market):
                    bet_amount = (
                        current_balance * self.get_bet_size(p2_prob, p2_market)
                    )
                    pnl = -bet_amount
                    is_win = False
                    bet_on = "P2"
                    bet_placed = True

                # Update balance
                if bet_placed:
                    current_balance += pnl

                # We record every game regarless of whether we bet or not
                history.append(
                    {
                        "date": m.tourney_date,
                        "match_id": m.id,
                        "p1_name": m.winner_name,
                        "p2_name": m.loser_name,
                        "bet_on": bet_on,  # Will be "None", "P1", or "P2"
                        "bet_amount": bet_amount,  # Will be 0 if no bet
                        "is_win": is_win,  # Only meaningful if bet_placed
                        "actual_winner": "P1",  # In the DB, P1 is always the winner
                        "p1_prob": p1_prob,
                        "p2_prob": p2_prob,
                        "p1_market": p1_market,
                        "p2_market": p2_market,
                        "pnl": pnl,
                        "balance": current_balance,
                        "surface": m.surface,
                    }
                )

            # Results
            results_df = pd.DataFrame(history)
            results_df.to_csv(
                f"app/ml/data/betting_results_{self.model_name}.csv", index=False
            )

            print(f"🏁 Backtest Finished. for {self.model_name}")
            print(f"📈 Final Bankroll: £{current_balance:.2f}")

            total_wagered = sum(h["bet_amount"] for h in history)
            total_profit = current_balance - self.bankroll

            # 1. Yield (The Model's Edge)
            yield_pct = (total_profit / total_wagered) if total_wagered > 0 else 0

            # 2. ROC (The Bankroll Growth)
            roc_pct = total_profit / self.bankroll

            print(f"📈 Bankroll Growth (ROC): {roc_pct:.2%}")
            print(f"🚀 Model Yield (ROI): {yield_pct:.2%}")


xgboost_nn_service = PNLService()
xg_boost_service = PNLService(
        model=joblib.load("app/ml/models/XGBoost.pkl"),
        model_name="XGBoost",
    )
nn_service = PNLService(model_name="NN")
logistic_service = PNLService(
        model=joblib.load("app/ml/models/LogisticRegression.pkl"),
        model_name="Logistic",
    )


async def main():
    # 🎯 1. Run the Hybrid Model
    # XGBoost_NN_service = PNLService() # Defaults to XGBoost&NN
    # await XGBoost_NN_service.run_backtest()

    # # 🎯 2. Run the Baseline Model
    # # Re-init inside the same async context
    # XGBoost_service = PNLService(
    #     model=joblib.load("app/ml/models/XGBoost.pkl"),
    #     model_name="XGBoost",
    # )
    # await XGBoost_service.run_backtest()

    # NN_service = PNLService(model_name="NN")
    # await NN_service.run_backtest()

    logistic_service = PNLService(
        model=joblib.load("app/ml/models/LogisticRegression.pkl"),
        model_name="Logistic",
    )
    await logistic_service.run_backtest()



if __name__ == "__main__":
    asyncio.run(main())
