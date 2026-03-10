import asyncio
import sys
# Import the main functions from your existing scripts
from app.services.data.player_ingestion import main as ingest_players
from app.services.data.match_ingestion import main as ingest_matches
from app.services.data.odds_ingestor import main as ingest_odds
from app.services.ml.feature_engine import main as run_features
from app.services.data.hydrate_player_states import main as hydrate_stats

async def run_pipeline():
    print("🚀 VANTAGE POINT: Starting Full Data Pipeline...")
    
    try:
        print("1/5: Ingesting Players...")
        await ingest_players()
        
        print("2/5: Ingesting Matches...")
        await ingest_matches()
        
        print("3/5: Ingesting Odds...")
        await ingest_odds()
        
        print("4/5: Running Feature Engine (XGBoost Prep)...")
        await run_features()
        
        print("5/5: Hydrating Player States (The Master Pluck)...")
        await hydrate_stats()
        
        print("✅ PIPELINE COMPLETE: Database is fully hydrated.")
    except Exception as e:
        print(f"❌ PIPELINE FAILED at stage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
