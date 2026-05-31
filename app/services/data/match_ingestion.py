import pandas as pd
import asyncio
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.database.session import async_session
from app.models.match import Match
from app.models.player import Player
from sqlalchemy import select
import re
from sqlalchemy import text


def parse_atp_score(score_str):
    if not score_str or pd.isna(score_str):
        return True, 0, 0, 0.0, 0, 0

    s = str(score_str).strip()

    is_retirement = "RET" in s.upper() or not re.match(r"^\d", s) or "W/O" in s.upper()

    sets = re.sub(r"\(.*?\)", "", s).replace("RET", "").replace("W/O", "").split()

    w_games, l_games, tb_played, tb_won = 0, 0, 0, 0

    for set_score in sets:
        try:
            w, l = map(int, set_score.split("-"))
            w_games += w
            l_games += l

            # Identify Tiebreaks (Professional Standard is 7-6 or 6-7)
            if (w == 7 and l == 6) or (w == 6 and l == 7):
                tb_played += 1
                if w == 7:
                    tb_won += 1
        except:
            continue

    total_games = w_games + l_games
    games_diff = w_games - l_games
    win_pct = round(w_games / total_games, 3) if total_games > 0 else 0.0

    return is_retirement, total_games, games_diff, win_pct, tb_played, tb_won


def clean_int(val):
    if pd.isna(val) or val is None:
        return None
    try:
        return int(float(val))
    except:
        return None


async def ingest_csv_file(file_path: str):
    print(f"🔄 Processing {os.path.basename(file_path)}...")
    chunk_size = 600

    reader = pd.read_csv(
        file_path,
        low_memory=False,  # Safer to do this since we are chunking anyway
        chunksize=chunk_size,
        dtype={
            "winner_id": str,
            "loser_id": str,
        },  # Better to force the dtypes rather than auto generate
    )

    total = 0
    async with async_session() as session:
        # Query the db to get a set of calie player id's, set ensures uniqueness
        player_ids = await session.execute(select(Player.id))
        valid_ids = set(player_ids.scalars().all())

        for df_chunk in reader:
            true_false_df = pd.notnull(
                df_chunk
            )  # Non null values assigned true, nulls to false
            df_chunk = df_chunk.where(
                true_false_df, None
            )  # Peserves the trues and maps the falses to none, postgres likes none over np.nan

            # Making a list comprehension of every match in the chunk, fast way to put our data into a good form
            matches_data = [
                {
                    "tourney_id": str(row["tourney_id"]),
                    "tourney_name": str(row["tourney_name"]),
                    "surface": str(row["surface"]),
                    "tourney_level": str(row["tourney_level"]),
                    "tourney_date": datetime.strptime(
                        str(int(float(row["tourney_date"]))), "%Y%m%d"
                    ),
                    "match_num": clean_int(row["match_num"]),
                    "winner_id": str(row["winner_id"]),
                    "loser_id": str(row["loser_id"]),
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
                    # Accessing the unpacked tuple results
                    "is_retirement": res[0],
                    "total_games": res[1],
                    "games_diff": res[2],
                    "game_win_percentage": res[3],
                    "tiebreaks_played": res[4],
                    "tiebreaks_won": res[5],
                }
                for _, row in df_chunk.iterrows()
                for res in [parse_atp_score(row.get("score"))]
                if str(row["winner_id"]) in valid_ids
                and str(row["loser_id"]) in valid_ids
            ]

            if matches_data:
                # 4. Bulk Upsert (Conflict is unlikely for matches, but safe to use)
                stmt = insert(Match).values(matches_data).on_conflict_do_nothing()
                await session.execute(stmt)

                # We use these two queries to add in the player names, leaning on our players table
                await session.execute(
                    text("""
UPDATE matches 
SET winner_name = players.player
FROM players
WHERE matches.winner_id = players.id 
  AND matches.winner_name IS NULL;""")
                )
                await session.execute(
                    text("""
UPDATE matches 
SET loser_name = players.player
FROM players
WHERE matches.loser_id = players.id 
  AND matches.loser_name IS NULL;
    """)
                )
                await session.commit()

                total += len(matches_data)
                # print(f"📦 {file_path}: {total} matches synced...")

    # print(f"✅ Ingestion Complete for {file_path}")
    return total


async def main():
    DATA_DIR = "/project/app/tml-data"
    years = [f"{year}.csv" for year in range(2010, 2027)]

    grand_total = 0

    for filename in years:
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            # 🎯 Capture the count from the function
            count = await ingest_csv_file(file_path)
            grand_total += count

    print("\n" + "=" * 30)
    print(f"🏁 ALL-TIME INGESTION COMPLETE")
    print(f"📊 Total Matches in Database: {grand_total}")
    print("=" * 30)


if __name__ == "__main__":
    asyncio.run(main())
