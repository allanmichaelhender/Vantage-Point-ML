import pandas as pd
import os
import asyncio
from sqlalchemy import select, update, extract
from app.database.session import async_session
from app.models.match import Match


def clean_odds(val):
    if pd.isnull(val) or str(val).strip() == "-":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


async def ingest_bulk_odds(files_config):
    async with async_session() as session:
        for config in files_config:
            path = config["path"]
            year = config["year"]

            if not os.path.exists(path):
                print(f"⚠️ Skipping {path} - File not found.")
                continue

            print(f"📡 Processing {year} odds from {path}...")
            df_odds = pd.read_csv(path)

            # Fetch DB matches for this year
            stmt = select(Match).where(extract("year", Match.tourney_date) == year)
            result = await session.execute(stmt)
            db_matches = result.scalars().all()

            # 2. Build Point-Match Index: (Surface, WPts, LPts) -> Match Object
            # We capitalize Surface to match CSV "Hard" vs DB "Hard"
            db_index = {
                (
                    m.surface.capitalize(),
                    int(m.winner_ranking_points),
                    int(m.loser_ranking_points),
                ): m
                for m in db_matches
                if m.winner_ranking_points is not None
                and m.loser_ranking_points is not None
            }

            updates = []
            for _, row in df_odds.iterrows():
                try:
                    # Create the 'Point Fingerprint'
                    sig = (
                        row["Surface"].capitalize(),
                        int(row["WPts"]),
                        int(row["LPts"]),
                    )
                    target = db_index.get(sig)

                    if target:
                        updates.append(
                            {
                                "id": target.id,
                                "b365_w": clean_odds(row["B365W"]),
                                "b365_l": clean_odds(row["B365L"]),
                                "ps_w": clean_odds(row["PSW"]),
                                "ps_l": clean_odds(row["PSL"]),
                            }
                        )
                except (ValueError, TypeError, KeyError):
                    continue

            # Bulk Update the DB
            if updates:
                await session.execute(update(Match), updates)
                await session.commit()
                print(
                    f"✅ Successfully matched {len(updates)} / {len(df_odds)} matches for {year}"
                )


if __name__ == "__main__":
    configs = [
        {"path": "app/tml-data/betting_odds/2025_odds.csv", "year": 2025},
        {"path": "app/tml-data/betting_odds/2026_odds.csv", "year": 2026},
    ]
    asyncio.run(ingest_bulk_odds(configs))
