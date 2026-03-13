import asyncio
from datetime import datetime, date
from sqlalchemy import select, update
from app.database.session import async_session
from app.models.match import Match

class PlayerHistory:
    def __init__(self):
        self.elo = 1500.0
        self.surface_elo = {"Hard": 1500.0, "Clay": 1500.0, "Grass": 1500.0, "Carpet": 1500.0}
        self.last_match_date = None
        self.last_surface_date = {"Hard": None, "Clay": None, "Grass": None, "Carpet": None}
        self.recent_performance = [] # List of (win_bit, game_win_pct)
        self.recent_matches = [] # Raw stats for efficiency ratios

    def get_snapshots(self, current_date, surface):
        # 1. Rolling Form (Last 10 matches)
        if not self.recent_performance:
            m_win_pct, g_win_pct = 0.0, 0.50
        else:
            m_win_pct = sum(x[0] for x in self.recent_performance) / len(self.recent_performance)
            g_win_pct = sum(x[1] for x in self.recent_performance) / len(self.recent_performance)

        # 2. Timing/Rust
        days_off = (current_date - self.last_match_date).days if self.last_match_date else None
        surf_days_off = (current_date - self.last_surface_date.get(surface)).days if self.last_surface_date.get(surface) else None

        # 3. Efficiency & Fatigue
        def safe_div(n, d, default=0.0):
            return n / d if d and d > 0 else default

        fatigue = sum(m['mins'] for m in self.recent_matches if (current_date - m['date']).days <= 14)

        
        recent_10 = self.recent_matches[-10:]
        tot_ace = sum(m['ace'] for m in recent_10)
        tot_svgms = sum(m['svgms'] for m in recent_10)
        tot_bp_s = sum(m['bp_s'] for m in recent_10)
        tot_bp_f = sum(m['bp_f'] for m in recent_10)

        ace_pg = safe_div(tot_ace, tot_svgms, 0.0)
        bp_save = safe_div(tot_bp_s, tot_bp_f, 1.0) # Default 1.0 if no BP faced

        tot_df = sum(m['df'] for m in recent_10)
        tot_svpt = sum(m['svpt'] for m in recent_10)
        tot_sv_won = sum(m['sv_won'] for m in recent_10)

        sv_won = safe_div(tot_sv_won, tot_svpt, 0.60) # 60% avg serve won
        df_pp = safe_div(tot_df, tot_svpt, 0.03)      # 3% avg DF rate

        return m_win_pct, g_win_pct, days_off, surf_days_off, ace_pg, bp_save, fatigue, sv_won, df_pp

def calculate_elo_change(w_elo, l_elo, k=32):
    expected_w = 1 / (1 + 10 ** ((l_elo - w_elo) / 400))
    change = k * (1 - expected_w)
    return w_elo + change, l_elo - change

async def run_feature_engine():
    async with async_session() as session:
        print("📡 Loading matches from DB...")
        stmt = select(Match).order_by(Match.tourney_date.asc(), Match.id.asc())
        result = await session.execute(stmt)
        matches = result.scalars().all()
        
        tracker = {} 
        update_payload = []

        print(f"🧠 Computing features for {len(matches)} matches...")
        for m in matches:
            if m.winner_id not in tracker: tracker[m.winner_id] = PlayerHistory()
            if m.loser_id not in tracker: tracker[m.loser_id] = PlayerHistory()
            
            w, l = tracker[m.winner_id], tracker[m.loser_id]
            m_date = m.tourney_date.date() if isinstance(m.tourney_date, datetime) else m.tourney_date

            # --- A. SNAPSHOTS (BEFORE MATCH) ---
            w_m_win, w_g_win, w_off, w_s_off, w_ace, w_bp, w_fat, w_sv_won, w_df_pp = w.get_snapshots(m_date, m.surface)
            l_m_win, l_g_win, l_off, l_s_off, l_ace, l_bp, l_fat, l_sv_won, l_df_pp = l.get_snapshots(m_date, m.surface)

            update_payload.append({
                "id": m.id,
                "w_elo_before": w.elo,
                "l_elo_before": l.elo,
                "w_surface_elo_before": w.surface_elo.get(m.surface, 1500.0),
                "l_surface_elo_before": l.surface_elo.get(m.surface, 1500.0),
                "w_days_off": w_off,
                "l_days_off": l_off,
                "w_surface_days_off": w_s_off,
                "l_surface_days_off": l_s_off,
                "w_rolling_match_win_pct": w_m_win,
                "w_rolling_game_win_pct": w_g_win,
                "l_rolling_match_win_pct": l_m_win,
                "l_rolling_game_win_pct": l_g_win,
                
                # These were likely the missing ones:
                "w_rolling_serve_won_pct": w_sv_won,  # ADDED
                "l_rolling_serve_won_pct": l_sv_won,  # ADDED
                "w_rolling_df_per_pt": w_df_pp,       # ADDED (ensure you unpack this from get_snapshots)
                "l_rolling_df_per_pt": l_df_pp,       # ADDED
                
                # Return Won = 1 - Opponent's Serve Won
                "w_rolling_return_won_pct": 1.0 - l_sv_won, # ADDED
                "l_rolling_return_won_pct": 1.0 - w_sv_won, # ADDED
                
                "w_rolling_ace_per_game": w_ace,
                "w_rolling_bp_save_pct": w_bp,
                "w_tournament_fatigue": w_fat,
                "l_rolling_ace_per_game": l_ace,
                "l_rolling_bp_save_pct": l_bp,
                "l_tournament_fatigue": l_fat
            })

            # --- B. UPDATE STATES (AFTER MATCH) ---
            # 1. Elo
            w.elo, l.elo = calculate_elo_change(w.elo, l.elo)
            w.surface_elo[m.surface], l.surface_elo[m.surface] = calculate_elo_change(
                w.surface_elo.get(m.surface, 1500.0), 
                l.surface_elo.get(m.surface, 1500.0)
            )

            # 2. Timing
            w.last_match_date, l.last_match_date = m_date, m_date
            w.last_surface_date[m.surface], l.last_surface_date[m.surface] = m_date, m_date

            # 3. Form/Efficiency Buffers
            w_g_pct = m.game_win_percentage if m.game_win_percentage else 0.5
            w.recent_performance.append((1.0, w_g_pct))
            l.recent_performance.append((0.0, 1.0 - w_g_pct))
            
            # Winner Data
            w.recent_matches.append({
                'date': m_date, 'mins': m.minutes or 0, 'ace': m.w_ace or 0, 
                'df': m.w_df or 0, 'svpt': m.w_svpt or 0, # <--- ADD THESE
                'svgms': m.w_SvGms or 0, 'bp_s': m.w_bpSaved or 0, 'bp_f': m.w_bpFaced or 0,
                'sv_won': (m.w_1stWon or 0) + (m.w_2ndWon or 0)
            })
            # Loser Data
            l.recent_matches.append({
                'date': m_date, 'mins': m.minutes or 0, 'ace': m.l_ace or 0, 
                'df': m.l_df or 0, 'svpt': m.l_svpt or 0, # <--- ADD THESE
                'svgms': m.l_SvGms or 0, 'bp_s': m.l_bpSaved or 0, 'bp_f': m.l_bpFaced or 0,
                'sv_won': (m.l_1stWon or 0) + (m.l_2ndWon or 0)
            })

            # Trim to prevent memory bloat
            w.recent_performance, l.recent_performance = w.recent_performance[-10:], l.recent_performance[-10:]
            w.recent_matches, l.recent_matches = w.recent_matches[-20:], l.recent_matches[-20:]

        # 2. BULK UPDATE
        print(f"💾 Saving {len(update_payload)} snapshots...")
        for i in range(0, len(update_payload), 2000):
            chunk = update_payload[i : i + 2000]
            await session.execute(update(Match), chunk)
            await session.commit()
            print(f"✅ Synced {min(i + 2000, len(update_payload))} snapshots...")

    print("🏁 Feature Engineering Complete.")

if __name__ == "__main__":
    asyncio.run(run_feature_engine())
