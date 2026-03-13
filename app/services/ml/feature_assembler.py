import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

import torch
import numpy as np
import joblib
from app.ml.tennis_encoder import TennisEncoder

EXPECTED_FEATURES = [
            'p1_elo', 'p2_elo', 'p1_surf_elo', 'p2_surf_elo', 
            'p1_days_off', 'p2_days_off', 'p1_surf_days_off', 'p2_surf_days_off',
            'p1_m_win', 'p2_m_win', 'p1_g_win', 'p2_g_win',
            'p1_sv_won', 'p1_ace_pg', 'p1_df_pp', 'p1_bp_s', 'p1_ret_won', 'p1_fatigue',
            'p2_sv_won', 'p2_ace_pg', 'p2_df_pp', 'p2_bp_s', 'p2_ret_won', 'p2_fatigue'
        ]

class FeatureAssembler:
    def __init__(self):
        # 1. Load the Artifacts
        self.scaler = joblib.load('app/ml/models/scaler.pkl')
        self.player_le = joblib.load('app/ml/models/player_encoder.pkl')
        self.surface_le = joblib.load('app/ml/models/surface_encoder.pkl')
        
        # 2. Initialize and Load the Encoder
        # Use the same input_dim from your training (likely 24)
        self.encoder = TennisEncoder(
            num_players=len(self.player_le.classes_),
            num_surfaces=len(self.surface_le.classes_),
            input_dim=26 
        )
        self.encoder.load_state_dict(torch.load('app/ml/models/tennis_encoder.pt'))
        self.encoder.eval()

    def assemble_match(self, m, flip=False):
        """Turns a Match DB object into a 61-feature vector with optional flipping."""
        
        # 1. ORCHESTRATE THE IDENTITY SWAP
        # This ensures the Neural Network 'identifies' the right player
        p1_id = m.loser_id if flip else m.winner_id
        p2_id = m.winner_id if flip else m.loser_id
        
        # 2. MAP CATEGORICAL INDEXES
        try:
            # We use [0] because transform() returns a list/array
            p1_idx = torch.tensor([self.player_le.transform([p1_id])[0]], dtype=torch.long)
            p2_idx = torch.tensor([self.player_le.transform([p2_id])[0]], dtype=torch.long)
            # Surface and Level don't flip (they are shared by both players)
            surf_idx = torch.tensor([self.surface_le.transform([m.surface])[0]], dtype=torch.long)
        except (ValueError, KeyError):
            return None

        # 3. MAP CONTINUOUS STATS (The "Flip" applies here too)
        data = {
            # Elo/Days Off
            "p1_elo": m.l_elo_before if flip else m.w_elo_before,
            "p2_elo": m.w_elo_before if flip else m.l_elo_before,
            "p1_surf_elo": m.l_surface_elo_before if flip else m.w_surface_elo_before,
            "p2_surf_elo": m.w_surface_elo_before if flip else m.l_surface_elo_before,
            "p1_days_off": m.l_days_off if flip else m.w_days_off,
            "p2_days_off": m.w_days_off if flip else m.l_days_off,
            "p1_surf_days_off": m.l_surface_days_off if flip else m.w_surface_days_off,
            "p2_surf_days_off": m.w_surface_days_off if flip else m.l_surface_days_off,
            
            # Form
            "p1_m_win": m.l_rolling_match_win_pct if flip else m.w_rolling_match_win_pct,
            "p2_m_win": m.w_rolling_match_win_pct if flip else m.l_rolling_match_win_pct,
            "p1_g_win": m.l_rolling_game_win_pct if flip else m.w_rolling_game_win_pct,
            "p2_g_win": m.w_rolling_game_win_pct if flip else m.l_rolling_game_win_pct,

            # P1 Efficiency (Loser data if flipped)
            "p1_sv_won": m.l_rolling_serve_won_pct if flip else m.w_rolling_serve_won_pct,
            "p1_ace_pg": m.l_rolling_ace_per_game if flip else m.w_rolling_ace_per_game,
            "p1_df_pp": m.l_rolling_df_per_pt if flip else m.w_rolling_df_per_pt,
            "p1_bp_s": m.l_rolling_bp_save_pct if flip else m.w_rolling_bp_save_pct,
            "p1_ret_won": m.l_rolling_return_won_pct if flip else m.w_rolling_return_won_pct,
            "p1_fatigue": m.l_tournament_fatigue if flip else m.w_tournament_fatigue,

            # P2 Efficiency (Winner data if flipped)
            "p2_sv_won": m.w_rolling_serve_won_pct if flip else m.l_rolling_serve_won_pct,
            "p2_ace_pg": m.w_rolling_ace_per_game if flip else m.l_rolling_ace_per_game,
            "p2_df_pp": m.w_rolling_df_per_pt if flip else m.l_rolling_df_per_pt,
            "p2_bp_s": m.w_rolling_bp_save_pct if flip else m.l_rolling_bp_save_pct,
            "p2_ret_won": m.w_rolling_return_won_pct if flip else m.l_rolling_return_won_pct,
            "p2_fatigue": m.w_tournament_fatigue if flip else m.l_tournament_fatigue,
        }

        # 3. Create DataFrame and Scale
        stats_df = pd.DataFrame([data])[EXPECTED_FEATURES].infer_objects(copy=False).fillna(0)
        scaled_stats = self.scaler.transform(stats_df)

      
        
        with torch.no_grad():
            p1_emb = self.encoder.player_embed(p1_idx).numpy()
            p2_emb = self.encoder.player_embed(p2_idx).numpy()
            surf_emb= self.encoder.surface_embed(surf_idx)

        final_vector = np.hstack([scaled_stats, p1_emb, p2_emb, surf_emb])
        
        return final_vector
    
    def assemble_manual(self, p1_id, p2_id, surface, stats_dict, flip=False):

        import torch
        import numpy as np

        # 1. Get Neural Style Vectors (Embeddings)
        try:
            # We use the LabelEncoder to get the 'Seat Number' for the NN
            p1_idx = torch.tensor([self.player_le.transform([p1_id])[0]], dtype=torch.long)
            p2_idx = torch.tensor([self.player_le.transform([p2_id])[0]], dtype=torch.long)
            surf_idx = torch.tensor([self.surface_le.transform([m.surface])[0]], dtype=torch.long)

            
            with torch.no_grad():
                p1_emb = self.encoder.player_embed(p1_idx).numpy()
                p2_emb = self.encoder.player_embed(p2_idx).numpy()
                surf_emb = self.encoder.surface_embed(surf_idx)
        except (ValueError, KeyError):
            # If a player is too new and not in the Encoder, we use a Zero-vector
            p1_emb = np.zeros((1, 16))
            p2_emb = np.zeros((1, 16))

        # 2. Scale the 24 Continuous Stats
        # EXPECTED_FEATURES ensures the order is 100% correct for the Scaler
        stats_df = pd.DataFrame([stats_dict])[self.scaler.feature_names_in_].infer_objects(copy=False).fillna(0)
        scaled_stats = self.scaler.transform(stats_df)

        # 3. Concatenate into the final 61-feature row
        if flip:
            # If flipping, we swap the stats AND the style vectors
            return np.hstack([scaled_stats, p2_emb, p1_emb, surf_emb])
        
        return np.hstack([scaled_stats, p1_emb, p2_emb, surf_emb])
