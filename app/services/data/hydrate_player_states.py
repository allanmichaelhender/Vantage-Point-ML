import asyncio
from sqlalchemy import text
from app.database.session import async_session
from datetime import datetime, timedelta

class StateHydrator:
    def __init__(self):
        self.surfaces = ['Hard', 'Clay', 'Grass']

    async def run_master_pluck(self, session):
        print("📊 Phase 1: Plucking Global Stats & Identity...")
        query = text("""
            INSERT INTO player_states (
                player_id, player_name, current_elo, last_match_date,
                rolling_match_win_pct, rolling_game_win_pct, 
                rolling_serve_won_pct, rolling_ace_per_game, 
                rolling_df_per_pt, rolling_bp_save_pct, rolling_return_won_pct
            )
            SELECT DISTINCT ON (p_id)
                p_id, p_name, elo_snap, m_date, 
                r_m_w, r_g_w, r_s_w, r_ace, r_df, r_bp, r_ret
            FROM (
                SELECT 
                    winner_id as p_id, winner_name as p_name, w_elo_before as elo_snap, tourney_date as m_date,
                    w_rolling_match_win_pct as r_m_w, w_rolling_game_win_pct as r_g_w,
                    w_rolling_serve_won_pct as r_s_w, w_rolling_ace_per_game as r_ace,
                    w_rolling_df_per_pt as r_df, w_rolling_bp_save_pct as r_bp,
                    w_rolling_return_won_pct as r_ret
                FROM matches
                UNION ALL
                SELECT 
                    loser_id as p_id, loser_name as p_name, l_elo_before as elo_snap, tourney_date as m_date,
                    l_rolling_match_win_pct as r_m_w, l_rolling_game_win_pct as r_g_w,
                    l_rolling_serve_won_pct as r_s_w, l_rolling_ace_per_game as r_ace,
                    l_rolling_df_per_pt as r_df, l_rolling_bp_save_pct as r_bp,
                    l_rolling_return_won_pct as r_ret
                FROM matches
            ) AS combined
            ORDER BY p_id, m_date DESC
            ON CONFLICT (player_id) DO UPDATE SET
                current_elo = EXCLUDED.current_elo,
                last_match_date = EXCLUDED.last_match_date;
        """)
        await session.execute(query)
        await session.commit()


    async def run_surface_paint(self, session):
        print("🎾 Phase 2: Setting Surface Defaults and Painting Data...")
        
        for surf in self.surfaces:
            column_name = f"current_{surf.lower()}_elo"
            date_column = f"last_{surf.lower()}_match_date"
            
            # 1. THE "BLANKET": Set every single row to 1500 first
            # This ensures NO nulls exist before we even look at the matches
            print(f"   -> Setting all {column_name} to 1500.0...")
            await session.execute(text(f"UPDATE player_states SET {column_name} = 1500.0"))

            # 2. THE "PAINT": Update only those who HAVE match history on this surface
            print(f"   -> Plucking real {surf} data from history...")
            query = text(f"""
                WITH surf_latest AS (
                    SELECT p_id, s_elo, m_date
                    FROM (
                        SELECT winner_id as p_id, w_surface_elo_before as s_elo, tourney_date as m_date,
                            ROW_NUMBER() OVER (PARTITION BY winner_id ORDER BY tourney_date DESC) as rn 
                        FROM matches WHERE surface = :surf
                        UNION ALL
                        SELECT loser_id as p_id, l_surface_elo_before as s_elo, tourney_date as m_date,
                            ROW_NUMBER() OVER (PARTITION BY loser_id ORDER BY tourney_date DESC) as rn 
                        FROM matches WHERE surface = :surf
                    ) sub
                    WHERE rn = 1
                )
                UPDATE player_states
                SET 
                    {column_name} = surf_latest.s_elo,
                    {date_column} = surf_latest.m_date
                FROM surf_latest
                WHERE player_states.player_id = surf_latest.p_id;
            """)
            await session.execute(query, {"surf": surf})
            await session.commit()


    async def run_fatigue_calc(self, session):
        # 1. Calculate the dynamic 14-day window
        today = datetime.now()
        fourteen_days_ago = today - timedelta(days=14)
        
        print(f"🔋 Phase 3: Calculating Rolling Fatigue (Since {fourteen_days_ago.date()})")

        # 2. Use Bind Parameters (:window_start) instead of f-strings for SQL safety
        query = text("""
        WITH player_mins AS (
            SELECT p_id, SUM(minutes) as total_mins
            FROM (
                SELECT winner_id as p_id, minutes, tourney_date as m_date FROM matches
                UNION ALL
                SELECT loser_id as p_id, minutes, tourney_date as m_date FROM matches
            ) sub
            WHERE m_date >= :window_start AND m_date <= :today
            GROUP BY p_id
        )
        UPDATE player_states
        SET current_tournament_fatigue = COALESCE(player_mins.total_mins, 0)
        FROM player_states AS ps
        LEFT JOIN player_mins ON ps.player_id = player_mins.p_id
        WHERE player_states.player_id = ps.player_id;
    """)

        await session.execute(query, {
            "window_start": fourteen_days_ago,
            "today": today
        })
        await session.commit()

    async def execute_all(self):
        async with async_session() as session:
            await self.run_master_pluck(session)
            await self.run_surface_paint(session)
            await self.run_fatigue_calc(session)
            print("🚀 Hydration Complete. PlayerState is Quant-Ready.")

if __name__ == "__main__":
    hydrator = StateHydrator()
    asyncio.run(hydrator.execute_all())
