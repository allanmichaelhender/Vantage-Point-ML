import asyncio
import sys

# Import the main functions from your existing scripts
from app.services.data.match_ingestion import main as ingest_matches
from app.services.data.player_ingestion import ingest_players_csv as ingest_players
from app.services.data.odds_ingestor import ingest_bulk_odds as ingest_odds
from app.services.ml.feature_engine import run_feature_engine as run_features


async def run_pipeline():
    print("🚀 VANTAGE POINT: Starting Full Data Pipeline...")

    try:
        path = "/project/app/tml-data/ATP_Database.csv"
        print("1/5: Ingesting Players...")
        await ingest_players(path)

        print("2/5: Ingesting Matches...")
        await ingest_matches()

        configs = [
            {"path": "app/tml-data/betting_odds/2025_odds.csv", "year": 2025},
            {"path": "app/tml-data/betting_odds/2026_odds.csv", "year": 2026},
        ]
        print("3/5: Ingesting Odds...")
        await ingest_odds(configs)

        print("4/5: Running Feature Engine (XGBoost Prep) and Hyrdrating Player States")
        await run_features()

        print("✅ PIPELINE COMPLETE: Database is fully hydrated.")
    except Exception as e:
        print(f"❌ PIPELINE FAILED at stage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
