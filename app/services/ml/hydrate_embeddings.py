import pandas as pd
from datetime import datetime, timedelta

# 🎯 THE CONFIG
START_DATE = pd.to_datetime("2012-01-01")
END_DATE = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
STEP_MONTHS = 2
LOOKBACK_YEARS = 2

current_date = START_DATE

while current_date < END_DATE:
    block_end = current_date + pd.DateOffset(months=STEP_MONTHS)
    training_start = current_date - pd.DateOffset(years=LOOKBACK_YEARS)
    
    print(f"\n--- 🔄 PROCESSING BLOCK: {current_date.date()} to {block_end.date()} ---")
    print(f"🧠 Training Brain on: {training_start.date()} to {current_date.date()}")
    print(f"💉 Injecting Embeddings into: {current_date.date()} to {block_end.date()}")

    # 1. FETCH Training Data (Matches between training_start and current_date)
    # 2. TRAIN Encoder (In-Memory, No .pt loading)
    # 3. FETCH Target Data (Matches between current_date and block_end)
    # 4. FORWARD PASS (Generate w_embedding, l_embedding)
    # 5. SQL UPDATE (STAMP the JSONB columns for those Match IDs)

    # Move to the next 2-month block
    current_date = block_end