import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.match import Match

# 1. Setup Sync Connection (Using your .env logic)
DATABASE_URL = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def ingest_slam_odds(csv_path: str, slam_name: str, year: int):
    print(f"📡 Processing {slam_name} {year} from {csv_path}...")
    
    if not os.path.exists(csv_path):
        print(f"⚠️ Skipping {csv_path} - File not found.")
        return

    try:
        df_odds = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    session = SessionLocal()
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        matches = session.query(Match).filter(
            Match.tourney_name.ilike(f"%{slam_name}%"),
            Match.tourney_date >= start_date,
            Match.tourney_date <= end_date
        ).all()

        print(f"🔍 Found {len(matches)} matches in DB for this tournament.")
        
        
        def clean_odds(val):
            if pd.isnull(val) or str(val).strip() == '-':
                return None
            try:
                return float(val)
            except ValueError:
                return None


        matched_count = 0
        for _, row in df_odds.iterrows():
            # Handle potential NaNs or non-numeric ranks in CSV
            try:
                csv_w_rank = int(row['WRank'])
                csv_l_rank = int(row['LRank'])
            except (ValueError, TypeError):
                continue

            # RANK-MATCH: DB vs CSV
            target_match = next((m for m in matches if 
                                 m.winner_rank == csv_w_rank and 
                                 m.loser_rank == csv_l_rank), None)
            
            if target_match:
                target_match.b365_w = clean_odds(row['B365W']) if pd.notnull(row['B365W']) else None
                target_match.b365_l = clean_odds(row['B365L']) if pd.notnull(row['B365L']) else None
                target_match.ps_w = clean_odds(row['PSW']) if pd.notnull(row['PSW']) else None
                target_match.ps_l = clean_odds(row['PSL']) if pd.notnull(row['PSL']) else None
                matched_count += 1

        session.commit()
        print(f"✅ Successfully updated {matched_count} matches.")

    except Exception as e:
        session.rollback()
        print(f"❌ Transaction failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Updated paths to project/app/tml-data/
    slams_to_process = [
        {"path": "app/tml-data/betting_odds/aus_open_2025.csv", "name": "Australian Open", "year": 2025},
        {"path": "app/tml-data/betting_odds/french_open_2025.csv", "name": "Roland Garros", "year": 2025},
        {"path": "app/tml-data/betting_odds/wimbledon_2025.csv", "name": "Wimbledon", "year": 2025},
        {"path": "app/tml-data/betting_odds/us_open_2025.csv", "name": "US Open", "year": 2025},
        {"path": "app/tml-data/betting_odds/aus_open_2026.csv", "name": "Australian Open", "year": 2026},
    ]

    for slam in slams_to_process:
        ingest_slam_odds(slam["path"], slam["name"], slam["year"])

    print("\n🏁 All odds ingestion tasks attempted.")
