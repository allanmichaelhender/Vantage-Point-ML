import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from app.database.session import engine # We can use the sync engine for a one-time pull
import os
from sqlalchemy import create_engine

class TennisDataProcessor:
    def __init__(self):
        # Encoding player id's
        self.player_encoder = LabelEncoder()

        # Encoding surfaces
        self.surface_encoder = LabelEncoder()

        # Our scalar
        self.scaler = StandardScaler()
        
    # Fetching data from db function
    def fetch_raw_data(self):
        db_url = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2") # We swap to psycopg2 because we are using syncronous
        
        # Creating a syncronous engine
        sync_engine = create_engine(db_url)
        
        # We select every game where both players have 10 recorded games (helps elo calculations and rolling stats) and remove retirments
        query = """
            SELECT 
                tourney_date,
                surface, winner_id, loser_id,
                w_elo_before, l_elo_before,
                w_surface_elo_before, l_surface_elo_before,
                w_days_off, l_days_off,
                w_surface_days_off, l_surface_days_off,
                w_rolling_match_win_pct, l_rolling_match_win_pct,
                w_rolling_game_win_pct, l_rolling_game_win_pct,
                w_rolling_serve_won_pct, w_rolling_ace_per_game,
                w_rolling_df_per_pt, w_rolling_bp_save_pct,
                w_rolling_return_won_pct, w_tournament_fatigue,
                l_rolling_serve_won_pct, l_rolling_ace_per_game,
                l_rolling_df_per_pt, l_rolling_bp_save_pct,
                l_rolling_return_won_pct, l_tournament_fatigue
            FROM matches 
            WHERE is_retirement = FALSE
            AND w_matches_played >= 10
            AND l_matches_played >= 10
        """
        
        return pd.read_sql(query, sync_engine)

    def process_and_balance(self, df):
        print(f"📊 Original matches: {len(df)}")
        
        # Converting to python datetime
        df['tourney_date'] = pd.to_datetime(df['tourney_date'])

        # regular map = map winner to p1
        regular_map = {
            'winner_id': 'p1_id', 'loser_id': 'p2_id',
            'w_elo_before': 'p1_elo', 'l_elo_before': 'p2_elo',
            'w_surface_elo_before': 'p1_surf_elo', 'l_surface_elo_before': 'p2_surf_elo',
            'w_days_off': 'p1_days_off', 'l_days_off': 'p2_days_off',
            'w_surface_days_off': 'p1_surf_days_off', 'l_surface_days_off': 'p2_surf_days_off',
            'w_rolling_match_win_pct': 'p1_m_win', 'l_rolling_match_win_pct': 'p2_m_win',
            'w_rolling_game_win_pct': 'p1_g_win', 'l_rolling_game_win_pct': 'p2_g_win',
            'w_rolling_serve_won_pct': 'p1_sv_won', 'l_rolling_serve_won_pct': 'p2_sv_won',
            'w_rolling_ace_per_game': 'p1_ace_pg', 'l_rolling_ace_per_game': 'p2_ace_pg',
            'w_rolling_df_per_pt': 'p1_df_pp', 'l_rolling_df_per_pt': 'p2_df_pp',
            'w_rolling_bp_save_pct': 'p1_bp_s', 'l_rolling_bp_save_pct': 'p2_bp_s',
            'w_rolling_return_won_pct': 'p1_ret_won', 'l_rolling_return_won_pct': 'p2_ret_won',
            'w_tournament_fatigue': 'p1_fatigue', 'l_tournament_fatigue': 'p2_fatigue'
        }

        # Create the "Winner = P1" half (Target 1)
        df_1 = df.copy()
        df_1 = df_1.rename(columns=regular_map)
        df_1['target'] = 1.0

        # This maps 'winner_id' to 'p2_id' and 'loser_id' to 'p1_id'
        flip_map = {
            'winner_id': 'p2_id', 'loser_id': 'p1_id',
            'w_elo_before': 'p2_elo', 'l_elo_before': 'p1_elo',
            'w_surface_elo_before': 'p2_surf_elo', 'l_surface_elo_before': 'p1_surf_elo',
            'w_days_off': 'p2_days_off', 'l_days_off': 'p1_days_off',
            'w_surface_days_off': 'p2_surf_days_off', 'l_surface_days_off': 'p1_surf_days_off',
            'w_rolling_match_win_pct': 'p2_m_win', 'l_rolling_match_win_pct': 'p1_m_win',
            'w_rolling_game_win_pct': 'p2_g_win', 'l_rolling_game_win_pct': 'p1_g_win',
            'w_rolling_serve_won_pct': 'p2_sv_won', 'l_rolling_serve_won_pct': 'p1_sv_won',
            'w_rolling_ace_per_game': 'p2_ace_pg', 'l_rolling_ace_per_game': 'p1_ace_pg',
            'w_rolling_df_per_pt': 'p2_df_pp', 'l_rolling_df_per_pt': 'p1_df_pp',
            'w_rolling_bp_save_pct': 'p2_bp_s', 'l_rolling_bp_save_pct': 'p1_bp_s',
            'w_rolling_return_won_pct': 'p2_ret_won', 'l_rolling_return_won_pct': 'p1_ret_won',
            'w_tournament_fatigue': 'p2_fatigue', 'l_tournament_fatigue': 'p1_fatigue'
        }

        # Create the "Loser = P1" half (Target 0)
        df_0 = df.copy()
        df_0 = df_0.rename(columns=flip_map)
        df_0['target'] = 0.0

        # Combining the regular and flipped data
        combined_df = pd.concat([df_1, df_0], axis=0).reset_index(drop=True)
        combined_df = combined_df.fillna(0)

        # Label Encoding Categorical features
        all_ids = pd.concat([df['winner_id'], df['loser_id']]).unique()
        self.player_encoder.fit(all_ids)
        
        combined_df['p1_id_idx'] = self.player_encoder.transform(combined_df['p1_id'])
        combined_df['p2_id_idx'] = self.player_encoder.transform(combined_df['p2_id'])
        combined_df['surface_idx'] = self.surface_encoder.fit_transform(combined_df['surface'])
        
        # Scaling Continuous Features
        cont_cols = [c for c in combined_df.columns if c.startswith(('p1_', 'p2_')) and not c.endswith('_id') and not c.endswith('_idx')]
        print(len(cont_cols))
        combined_df[cont_cols] = self.scaler.fit_transform(combined_df[cont_cols])

        # Remember, our data is p1 wins first half, p2 wins second half, this line randomises the order to remove ordering bias
        combined_df = combined_df.sample(frac=1).reset_index(drop=True)
        
        return combined_df

    # Saving our encoders/python objects
    def save_processors(self):
        joblib.dump(self.player_encoder, 'app/ml/models/player_encoder.pkl')
        joblib.dump(self.surface_encoder, 'app/ml/models/surface_encoder.pkl')
        joblib.dump(self.scaler, 'app/ml/models/scaler.pkl')

if __name__ == "__main__":
    proc = TennisDataProcessor()
    raw = proc.fetch_raw_data()
    final = proc.process_and_balance(raw)
    
    # Save the processed data for PyTorch
    final.to_pickle('app/ml/data/processed_training_data.pkl')
    proc.save_processors()
    print(f"✅ Preprocessing Complete. Dataset size: {len(final)}")
