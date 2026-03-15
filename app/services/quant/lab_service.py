import pandas as pd
import numpy as np


class LabService:
    def __init__(self, file_path: str = "app/ml/data/betting_results.csv"):
        self.file_path = file_path

    async def get_model_performance(self):
        df = pd.read_csv(self.file_path)
        df["date"] = pd.to_datetime(df["date"])

        # Global results
        brier_df = df.dropna(subset=["p1_prob"])
        global_brier = np.mean((brier_df["p1_prob"] - 1.0) ** 2)

        # Filter down to only bets made
        bet_df = df[df["bet_on"].isin(["P1", "P2"])].copy()

        total_wagered = bet_df["bet_amount"].sum()
        total_pnl = bet_df["pnl"].sum()

        summary = {
            "roi": total_pnl / total_wagered if total_wagered > 0 else 0,
            "total_profit": total_pnl,
            "win_rate": bet_df["is_win"].mean() if not bet_df.empty else 0,
            "brier_score": global_brier,
            "total_bets": len(bet_df),
        }

        # Creating a weekly snapshot of profit and loss
        weekly = (
            bet_df.set_index("date")["balance"]
            .resample("W")
            .last()
            .ffill()
            .reset_index()
        )

        # Final date in eevry week + finishing balance for that week
        equity_curve = [
            {"date": row.date.strftime("%Y-%m-%d"), "balance": row.balance}
            for row in weekly.itertuples()  # Coverts df into named tuples, much easier to work with
        ]

        # Looking at monthly results
        monthly_df = (
            bet_df.set_index("date")
            .resample("ME")
            .agg({"pnl": "sum", "bet_amount": "sum"})
            .reset_index()
        )

        monthly_breakdown = [
            {
                "month": row.date.strftime("%b %Y"),
                "roi": row.pnl / row.bet_amount if row.bet_amount > 0 else 0,
                "profit": row.pnl,
            }
            for row in monthly_df.itertuples()
        ]

        return {
            "summary": summary,
            "equity_curve": equity_curve,
            "monthly_breakdown": monthly_breakdown,
        }

    async def get_edge_analysis(self):
        df = pd.read_csv(self.file_path)

        bet_df = df[df["bet_on"].isin(["P1", "P2"])].copy()

        if bet_df.empty:
            return []

        # Creating bet prob (model prob) and bet odds columns
        bet_df["bet_prob"] = np.where(
            bet_df["bet_on"] == "P1", bet_df["p1_prob"], bet_df["p2_prob"]
        )  # Saying if true, use p1 prob, if false, p2_prob
        bet_df["bet_odds"] = np.where(
            bet_df["bet_on"] == "P1", bet_df["p1_odds"], bet_df["p2_odds"]
        )

        # Making edge column
        bet_df["edge"] = bet_df["bet_prob"] - (1 / bet_df["bet_odds"])

        # Defining the buckets
        bins = [0, 0.029, 0.049, 0.07, 0.10, 0.15, 1.0]
        labels = [
            "0-3% (Smallest)",
            "3-5% (Small)",
            "5-7% (Thin)",
            "7-10% (Value)",
            "10-15% (Strong)",
            "15%+ (Elite)",
        ]
        bet_df["bucket"] = pd.cut(bet_df["edge"], bins=bins, labels=labels)

        # Metrics
        analysis = (
            bet_df.groupby("bucket", observed=True)
            .apply(  # Apply maps every bucketed selection of data to two metrics: roi and match count
                lambda x: pd.Series(
                    {
                        "roi": x["pnl"].sum() / x["bet_amount"].sum()
                        if x["bet_amount"].sum() > 0
                        else 0,
                        "match_count": int(len(x)),
                    }
                )
            )
            .reset_index()
        )

        return analysis.to_dict(orient="records") # tells python to create a list of dics (rows)

    async def get_calibration(self):
        df = pd.read_csv(self.file_path)

        # Find the probability of the favourite
        df["fav_prob"] = np.where(df["p1_prob"] >= 0.5, df["p1_prob"], df["p2_prob"])

        # Remember p1 is always the winner, so we just need to check if p1 was our favourite
        df["fav_won"] = np.where(df["p1_prob"] >= 0.5, 1.0, 0.0) # 1 if p1 was favoured, 0 if p2 was favoured

        # Creating bins
        bins = np.arange(0.5, 1.05, 0.05)
        labels = [f"{int(i * 100)}-{int((i + 0.05) * 100)}%" for i in bins[:-1]]

        df["prob_bucket"] = pd.cut(
            df["fav_prob"], bins=bins, labels=labels, include_lowest=True
        ) # Include lowest ensures an exact 0.5 odds is included in first bucket

        # Aggregates
        calibration = (
            df.groupby("prob_bucket", observed=True)
            .apply(
                lambda x: pd.Series(
                    {
                        "avg_predicted": x["fav_prob"].mean(),
                        "actual_win_rate": x["fav_won"].mean(),
                        "match_count": int(len(x)),
                    }
                )
            )
            .reset_index()
        )

        df.to_csv("app/ml/data/calibration_results.csv", index=False)

        return calibration.to_dict(orient="records")


lab_service = LabService()
