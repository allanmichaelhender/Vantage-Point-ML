import torch
import torch.nn as nn

class TennisEncoder(nn.Module):
    def __init__(self, num_players, num_surfaces, input_dim, embedding_dim=16):
        super(TennisEncoder, self).__init__() # Running the parent init
        
        # Creating our lookup table to go from players to respective embedding value
        self.player_embed = nn.Embedding(num_players, embedding_dim)

        # We are going to embed every surface as a 4D vector to allow for complex interactions
        self.surface_embed = nn.Embedding(num_surfaces, 4)
        
        # Performance Tower (Continuous Features)
        # Processes Elo, Form, Fatigue, etc metrics
        self.performance_head = nn.Sequential(
            nn.Linear(input_dim, 64), # Creating 64 smart features
            nn.ReLU(),
            nn.BatchNorm1d(64), # Normalising the features
            nn.Dropout(0.2) # Kills 20% of the neurons every prediction to prevent overfitting
        )
        
        # Decision Maker logic
        # Concatenates: [P1_Vec (16), P2_Vec (16), Surf_Vec (4), Perf_Vec (64)] = 100 input features
        self.fusion = nn.Sequential(
            nn.Linear(100, 128), # Expanding to 128 smart features
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid() # Collapses down to a 0 - 1 probablity
        )

    # Defininng forward to run on our forward passes
    def forward(self, p1_idx, p2_idx, surface_idx, performance_stats):
        # Generate Player & Surface Vectors
        p1_vec = self.player_embed(p1_idx)
        p2_vec = self.player_embed(p2_idx)
        surf_vec = self.surface_embed(surface_idx)
        
        # Process Stats into performance vector
        perf_vec = self.performance_head(performance_stats)
        
        # Concatenate vectors
        combined = torch.cat([p1_vec, p2_vec, surf_vec, perf_vec], dim=1)
        
        return self.fusion(combined) # run prediction engine

    # Extracts the player vector to give is a 16 dim embedding to use in XGBoost
    def get_player_vector(self, player_idx):
        return self.player_embed(player_idx).detach() # Turns off pytorch tracking and just outputs the values