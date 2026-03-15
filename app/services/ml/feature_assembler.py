import pandas as pd
pd.set_option('future.no_silent_downcasting', True) # Prevents warning messages

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
        # Load the Artifacts
        self.scaler = joblib.load('app/ml/models/scaler.pkl') # We load in the scalar since its fitted to the whole dataset
        self.player_le = joblib.load('app/ml/models/player_encoder.pkl')
        self.surface_le = joblib.load('app/ml/models/surface_encoder.pkl')
        
        # Creating the Encoder skeleton
        self.encoder = TennisEncoder(
            num_players=len(self.player_le.classes_),
            num_surfaces=len(self.surface_le.classes_),
            input_dim=24 
        )

        # Filling out the skeleton with weights
        self.encoder.load_state_dict(torch.load('app/ml/models/tennis_encoder.pt'))
        self.encoder.eval()

    def assemble_match(self, match, flip=False):
        
        # We have a flip option when we call assemble match, this allows us to make a flipped version of the data then we can take the average to get symmetric predictions
        p1_id = match.loser_id if flip else match.winner_id
        p2_id = match.winner_id if flip else match.loser_id
        
        
        # Grabbing the embedding indexes
        p1_idx = torch.tensor([self.player_le.transform([p1_id])[0]], dtype=torch.long)  # We use [0] because transform() returns a list/array
        p2_idx = torch.tensor([self.player_le.transform([p2_id])[0]], dtype=torch.long) # These must be tensors to later pass into the label encoders
        surf_idx = torch.tensor([self.surface_le.transform([match.surface])[0]], dtype=torch.long)


        # Mapping the continuous features, allowing for flipping if needed
        data = {
            "p1_elo": match.l_elo_before if flip else match.w_elo_before,
            "p2_elo": match.w_elo_before if flip else match.l_elo_before,
            "p1_surf_elo": match.l_surface_elo_before if flip else match.w_surface_elo_before,
            "p2_surf_elo": match.w_surface_elo_before if flip else match.l_surface_elo_before,
            "p1_days_off": match.l_days_off if flip else match.w_days_off,
            "p2_days_off": match.w_days_off if flip else match.l_days_off,
            "p1_surf_days_off": match.l_surface_days_off if flip else match.w_surface_days_off,
            "p2_surf_days_off": match.w_surface_days_off if flip else match.l_surface_days_off,
            
            "p1_m_win": match.l_rolling_match_win_pct if flip else match.w_rolling_match_win_pct,
            "p2_m_win": match.w_rolling_match_win_pct if flip else match.l_rolling_match_win_pct,
            "p1_g_win": match.l_rolling_game_win_pct if flip else match.w_rolling_game_win_pct,
            "p2_g_win": match.w_rolling_game_win_pct if flip else match.l_rolling_game_win_pct,

            "p1_sv_won": match.l_rolling_serve_won_pct if flip else match.w_rolling_serve_won_pct,
            "p1_ace_pg": match.l_rolling_ace_per_game if flip else match.w_rolling_ace_per_game,
            "p1_df_pp": match.l_rolling_df_per_pt if flip else match.w_rolling_df_per_pt,
            "p1_bp_s": match.l_rolling_bp_save_pct if flip else match.w_rolling_bp_save_pct,
            "p1_ret_won": match.l_rolling_return_won_pct if flip else match.w_rolling_return_won_pct,
            "p1_fatigue": match.l_tournament_fatigue if flip else match.w_tournament_fatigue,

            "p2_sv_won": match.w_rolling_serve_won_pct if flip else match.l_rolling_serve_won_pct,
            "p2_ace_pg": match.w_rolling_ace_per_game if flip else match.l_rolling_ace_per_game,
            "p2_df_pp": match.w_rolling_df_per_pt if flip else match.l_rolling_df_per_pt,
            "p2_bp_s": match.w_rolling_bp_save_pct if flip else match.l_rolling_bp_save_pct,
            "p2_ret_won": match.w_rolling_return_won_pct if flip else match.l_rolling_return_won_pct,
            "p2_fatigue": match.w_tournament_fatigue if flip else match.l_tournament_fatigue,
        }

        # Create DataFrame and Scale
        stats_df = pd.DataFrame([data])[EXPECTED_FEATURES].fillna(0) # Expected features forces the column order
        scaled_stats = self.scaler.transform(stats_df)

      
        with torch.no_grad(): # No grad turns off all tracking, allows simple evaluation
            p1_emb = self.encoder.player_embed(p1_idx).numpy()
            p2_emb = self.encoder.player_embed(p2_idx).numpy()
            surf_emb= self.encoder.surface_embed(surf_idx)

        final_vector = np.hstack([scaled_stats, p1_emb, p2_emb, surf_emb]) # hstack = horizontal stack
        
        return final_vector

    def assemble_manual(self, p1_id, p2_id, surface, stats_dict, flip=False):

        import torch
        import numpy as np

        try:
            p1_idx = torch.tensor([self.player_le.transform([p1_id])[0]], dtype=torch.long)
            p2_idx = torch.tensor([self.player_le.transform([p2_id])[0]], dtype=torch.long)
            surf_idx = torch.tensor([self.surface_le.transform([surface])[0]], dtype=torch.long)

            
            with torch.no_grad():
                p1_emb = self.encoder.player_embed(p1_idx).numpy()
                p2_emb = self.encoder.player_embed(p2_idx).numpy()
                surf_emb = self.encoder.surface_embed(surf_idx)

        except (ValueError, KeyError):
            # If a player is too new and not in the Encoder, we use a zero-vector
            p1_emb = np.zeros((1, 16))
            p2_emb = np.zeros((1, 16))

        
        # EXPECTED_FEATURES ensures the order is correct for the Scaler
        stats_df = pd.DataFrame([stats_dict])[EXPECTED_FEATURES].fillna(0)
        scaled_stats = self.scaler.transform(stats_df)

        
        if flip:
            # If flipping, we swap the embeddings
            return np.hstack([scaled_stats, p2_emb, p1_emb, surf_emb])
        
        return np.hstack([scaled_stats, p1_emb, p2_emb, surf_emb])