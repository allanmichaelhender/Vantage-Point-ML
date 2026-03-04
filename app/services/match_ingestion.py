import pandas as pd
import asyncio
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.database.session import async_session
from app.models.match import Match
from app.models.player import Player 
from sqlalchemy import select


async def ingest_csv_file(file_path: str):
    """Processes a single year of ATP data."""
    print(f"🔄 Processing {os.path.basename(file_path)}...")
    chunk_size = 600

    # Load CSV with String IDs to prevent float scientific notation
    reader = pd.read_csv(
        file_path,
        low_memory=False,
        chunksize=chunk_size,
        dtype={"winner_id": str, "loser_id": str},
    )



    def clean_int(val):
        if pd.isna(val) or val is None:
            return None
        try:
            return int(float(val))
        except:
            return None

    total = 0
    async with async_session() as session:
        result = await session.execute(select(Player.id))
        valid_ids = set(result.scalars().all())




        for df_chunk in reader:
            # 2. Vectorized cleaning for the chunk
            df_chunk = df_chunk.where(pd.notnull(df_chunk), None)

            # 3. List Comprehension for the 1,000-row "bite"
            matches_data = [
                {
                    "tourney_id": str(row["tourney_id"]),
                    "tourney_name": str(row["tourney_name"]),
                    "surface": str(row["surface"]),
                    "tourney_level": str(row["tourney_level"]),
                    "tourney_date": datetime.strptime(
                        str(int(float(row["tourney_date"]))), "%Y%m%d"
                    ),
                    "winner_id": str(row["winner_id"]),
                    "loser_id": str(row["winner_id"]),
                    "score": str(row["score"]),
                    "best_of": clean_int(row.get("best_of")) or 3,
                    "round": str(row["round"]),
                    "minutes": clean_int(row.get("minutes")),
                    # Winner Stats
                    "w_ace": clean_int(row.get("w_ace")),
                    "w_df": clean_int(row.get("w_df")),
                    "w_svpt": clean_int(row.get("w_svpt")),
                    "w_1stIn": clean_int(row.get("w_1stIn")),
                    "w_1stWon": clean_int(row.get("w_1stWon")),
                    "w_2ndWon": clean_int(row.get("w_2ndWon")),
                    "w_SvGms": clean_int(row.get("w_SvGms")),
                    "w_bpSaved": clean_int(row.get("w_bpSaved")),
                    "w_bpFaced": clean_int(row.get("w_bpFaced")),
                    "winner_rank": clean_int(row.get("winner_rank")),
                    "winner_ranking_points": clean_int(row.get("winner_rank_points")),

                    # Loser Stats
                    "l_ace": clean_int(row.get("l_ace")),
                    "l_df": clean_int(row.get("l_df")),
                    "l_svpt": clean_int(row.get("l_svpt")),
                    "l_1stIn": clean_int(row.get("l_1stIn")),
                    "l_1stWon": clean_int(row.get("l_1stWon")),
                    "l_2ndWon": clean_int(row.get("l_2ndWon")),
                    "l_SvGms": clean_int(row.get("l_SvGms")),
                    "l_bpSaved": clean_int(row.get("l_bpSaved")),
                    "l_bpFaced": clean_int(row.get("l_bpFaced")),
                    "loser_rank": clean_int(row.get("loser_rank")),
                    "loser_ranking_points": clean_int(row.get("loser_rank_points")),
                }
                for _, row in df_chunk.iterrows()
                if str(row["winner_id"]) in valid_ids 
                and str(row["loser_id"]) in valid_ids
            ]

            if matches_data:
                # 4. Bulk Upsert (Conflict is unlikely for matches, but safe to use)
                stmt = insert(Match).values(matches_data).on_conflict_do_nothing()
                await session.execute(stmt)
                await session.commit()

                total += len(matches_data)
                print(f"📦 {file_path}: {total} matches synced...")

    print(f"✅ Ingestion Complete for {file_path}")



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
