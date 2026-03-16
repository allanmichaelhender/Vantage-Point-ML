import asyncio
import sys
import pandas as pd
from app.ml.processor import TennisDataProcessor
from app.ml.train_encoder import train_encoder 
from app.services.ml.hydrate_embeddings import main as hydrate_embeddings 
from app.ml.train_xgboost import train_xgboost
from app.services.quant.pnl_service import PNLService 


async def run_unified_pipeline():
    print("\n" + "="*50)
    print("🎾 VANTAGE POINT: STITCHED EVOLUTION PIPELINE")
    print("="*50)

    try:
        # --- 1. GLOBAL CALIBRATION ---
        # Fits the "Alphabet" (1744 IDs) and "Ruler" (Scaler) on all history
        print("🔠 STEP 1: Global Calibration & Scaling...")
        proc = TennisDataProcessor()
        raw = proc.fetch_raw_data()
        final = proc.process_and_balance(raw, frozen=False)
    
        # Save the processed data for PyTorch
        final.to_pickle('app/ml/data/processed_training_data.pkl')
        proc.save_processors()
        print("✅ Step 1 Complete. Processor locked.")

        # --- 2. TRAIN FOUNDATION (2010-2014) ---
        # Creates the 'Base Brain' that the evolution loop starts from
        print("\n🧠 STEP 2: Training Foundation Brain (2010-2014)...")
        train_encoder() 
        print("✅ Step 2 Complete. Foundation weights saved.")

        # --- 3. HYDRATE EMBEDDINGS (2015-PRESENT) ---
        # Runs the 2-month 'Nudge' loop and stamps the DB
        print("\n🧬 STEP 3: Running 11-Year Evolution & Hydration...")
        hydrate_embeddings() 
        print("✅ Step 3 Complete. Database Stitched with Neural DNA.")

        # --- 4. TRAIN XGBOOST ---
        # Pulls the stitched DNA from the DB and trains the final classifier
        print("\n🚀 STEP 4: Training Final XGBoost Classifier...")
        train_xgboost()
        print("✅ Step 4 Complete. XGBoost model ready.")

        # --- 5. P&L ANALYSIS ---
        # Backtests the 2025/2026 predictions against market odds
        print("\n💰 STEP 5: Calculating Historical P&L Performance...")
        service = PNLService()
        await service.run_backtest()
        print("✅ Step 5 Complete. Performance metrics generated.")

    except Exception as e:
        print(f"\n❌ PIPELINE FAILED at Line {sys.exc_info()[-1].tb_lineno}:")
        print(f"   Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_unified_pipeline())
