import pandas as pd
import asyncio
from sqlalchemy.dialects.postgresql import insert
from app.database.session import async_session
from app.models.player import Player
from datetime import date


async def ingest_players_csv(file_path: str):
    # 1. Use 'chunksize' to read the file in batches

    def clean_int(val):
        if pd.isna(val) or val is None:
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None
        
    def parse_atp_date(val):
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        try:
            # 1. Force to string and remove decimals (handles 19860801.0)
            d_str = str(int(float(val)))
            # 2. Slice YYYY-MM-DD
            if len(d_str) == 8:
                return date(int(d_str[:4]), int(d_str[4:6]), int(d_str[6:8]))
            return None
        except (ValueError, TypeError):
            return None

    df = pd.read_csv(file_path)

    # 2. THE CLEANSE (Vectorized - happens to the whole file)
    df["id"] = df["id"].astype(str).str.strip()
    df["player"] = df["player"].astype(str).str.strip()

    initial_count = len(df)
    # Strike out duplicates across the whole dataset
    df = df.drop_duplicates(subset=["id"], keep="first")

    print(
        f"⚠️ Removed {initial_count - len(df)} duplicates. {len(df)} unique players remain."
    )

    # 3. Global NaN to None
    df = df.where(pd.notnull(df), None)

    # 4. CHUNKING the clean data
    chunk_size = 1000
    async with async_session() as session:
        # We loop through the clean DataFrame in slices
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i : i + chunk_size]

            # List Comprehension on the 1000-row slice
            players_data = [
                {
                    "id": str(row["id"]),
                    "player": str(row["player"]),
                    "birthdate": parse_atp_date(row.get("birthdate")),
                    "atpname": str(row.get("atpname")) if row.get("atpname") else None,
                    "hand": str(row["hand"]).upper() if row.get("hand") else "U",
                    "height": clean_int(row.get("height")),
                    "weight": clean_int(row.get("weight")),
                    "ioc": str(row["ioc"])[:3].upper() if row.get("ioc") else None,
                    "backhand": str(row.get("backhand", "Unknown")),
                }
                for _, row in chunk.iterrows()
            ]

            # 5. Bulk Upsert the clean chunk
            stmt = insert(Player).values(players_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "player": stmt.excluded.player,
                    "height": stmt.excluded.height,
                    "hand": stmt.excluded.hand,
                    "birthdate": stmt.excluded.birthdate,
                },
            )

            await session.execute(stmt)
            await session.commit()
            print(f"📦 Progress: {i + len(players_data)} players ingested...")

    print(f"✅ Final Success: {len(df)} players are now in the database.")


if __name__ == "__main__":
    path = "/project/app/tml-data/ATP_Database.csv"
    asyncio.run(ingest_players_csv(path))
