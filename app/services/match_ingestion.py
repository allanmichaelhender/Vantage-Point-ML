import pandas as pd
import asyncio
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.database.session import async_session
from app.models.match import Match

async def ingest_csv_file(file_path: str):
    """Processes a single year of ATP data."""
    print(f"🔄 Processing {os.path.basename(file_path)}...")
    
    # Load CSV with String IDs to prevent float scientific notation
    df = pd.read_csv(file_path, low_memory=False, dtype={'winner_id': str, 'loser_id': str})
    df = df.where(pd.notnull(df), None)

    async with async_session() as session:
        matches_data = []
        for _, row in df.iterrows():
            try:
                # Convert YYYYMMDD to datetime
                date_val = str(row['tourney_date']).split('.')[0] # Handle floats
                match_date = datetime.strptime(date_val, '%Y%m%d')

                matches_data.append({
                    "tourney_id": str(row['tourney_id']),
                    "tourney_name": str(row['tourney_name']),
                    "surface": str(row['surface']),
                    "tourney_level": str(row['tourney_level']),
                    "tourney_date": match_date,
                    "winner_id": row['winner_id'],
                    "loser_id": row['loser_id'],
                    "score": str(row['score']),
                    "best_of": int(row['best_of']) if row['best_of'] else 3,
                    "round": str(row['round']),
                    "w_ace": row['w_ace'],
                    "w_df": row['w_df'],
                    "w_svpt": row['w_svpt'],
                    "w_1stIn": row['w_1stIn'],
                    "w_1stWon": row['w_1stWon'],
                    "w_2ndWon": row['w_2ndWon'],
                    "w_bpSaved": row['w_bpSaved'],
                    "w_bpFaced": row['w_bpFaced'],
                    "l_ace": row['l_ace'],
                    "l_df": row['l_df'],
                    "l_svpt": row['l_svpt'],
                    "l_1stIn": row['l_1stIn'],
                    "l_1stWon": row['l_1stWon'],
                    "l_2ndWon": row['l_2ndWon'],
                    "l_bpSaved": row['l_bpSaved'],
                    "l_bpFaced": row['l_bpFaced'],
                    "minutes": row['minutes']
                })
            except Exception as e:
                continue # Skip malformed rows

        if matches_data:
            stmt = insert(Match).values(matches_data).on_conflict_do_nothing()
            await session.execute(stmt)
            await session.commit()

async def main():
    DATA_DIR = "/project/app/tml-data"
    # Filter for files like 2010.csv, 2011.csv ... 2026.csv
    years = [f"{year}.csv" for year in range(2010, 2027)]
    
    for filename in years:
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            await ingest_csv_file(file_path)
    
    print("🏁 Bulk Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())
