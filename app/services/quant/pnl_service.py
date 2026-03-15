import pandas as pd
import joblib
import asyncio
from sqlalchemy import select
from app.database.session import async_session
from app.models.match import Match
from app.services.ml.feature_assembler import FeatureAssembler
from datetime import date


class PNLService:
    def __init__(self, initial_bankroll=1000.0, kelly_fraction=0.05):
        self.bankroll = initial_bankroll
        self.fraction = kelly_fraction
        self.max_bet_pct = 0.02

        self.xgb = joblib.load("app/ml/models/final_xgboost_model.pkl")
        self.assembler = FeatureAssembler()

    def get_bet_size(self, model_prob, odds):
        b = odds - 1
        p = model_prob
        q = 1 - p
        kelly = (b * p - q) / b
        suggested_pct = max(0, kelly * self.fraction)
        return min(suggested_pct, self.max_bet_pct)

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
                    Match.l_matches_played >= 10
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

                # Probability P1 wins from both perspectives
                p1_v1 = self.xgb.predict_proba(x_norm)[0][1]
                p1_v2 = 1.0 - self.xgb.predict_proba(x_flip)[0][1]

                p1_prob = (p1_v1 + p1_v2) / 2
                p2_prob = 1.0 - p1_prob

                # Selecting market odds
                p1_odds = m.ps_w if m.ps_w else m.b365_w
                p2_odds = m.ps_l if m.ps_l else m.b365_l

                # Betting logic
                bet_placed = False
                is_win = False
                pnl = 0
                bet_on = "None"
                bet_amount = 0

                if p1_prob > (1 / p1_odds): # + 0.05:
                    bet_amount = current_balance * self.get_bet_size(p1_prob, p1_odds)
                    pnl = (p1_odds - 1) * bet_amount
                    is_win = True
                    bet_on = "P1"
                    bet_placed = True
                elif p2_prob > (1 / p2_odds): # + 0.05:
                    bet_amount = current_balance * self.get_bet_size(p2_prob, p2_odds)
                    pnl = -bet_amount
                    is_win = False
                    bet_on = "P2"
                    bet_placed = True

                # Update balance
                if bet_placed:
                    current_balance += pnl

                # We record every game regarless of whether we bet or not
                history.append({
                    "date": m.tourney_date,
                    "match_id": m.id,
                    "p1_name": m.winner_name, 
                    "p2_name": m.loser_name, 
                    "bet_on": bet_on,        # Will be "None", "P1", or "P2"
                    "bet_amount": bet_amount, # Will be 0 if no bet
                    "is_win": is_win,         # Only meaningful if bet_placed
                    "actual_winner": "P1",    # In the DB, P1 is always the winner
                    "p1_prob": p1_prob,       
                    "p2_prob": p2_prob,
                    "p1_odds": p1_odds,
                    "p2_odds": p2_odds,
                    "pnl": pnl,
                    "balance": current_balance,
                    "surface": m.surface
                })
         
            # Results
            results_df = pd.DataFrame(history)
            results_df.to_csv("app/ml/data/betting_results.csv", index=False)

            print("🏁 Backtest Finished.")
            print(f"📈 Final Bankroll: £{current_balance:.2f}")

            total_wagered = sum(h["bet_amount"] for h in history)
            total_profit = current_balance - self.bankroll

            # 1. Yield (The Model's Edge)
            yield_pct = (total_profit / total_wagered) if total_wagered > 0 else 0

            # 2. ROC (The Bankroll Growth)
            roc_pct = total_profit / self.bankroll

            print(f"📈 Bankroll Growth (ROC): {roc_pct:.2%}")
            print(f"🚀 Model Yield (ROI): {yield_pct:.2%}")


if __name__ == "__main__":
    service = PNLService()
    asyncio.run(service.run_backtest())
