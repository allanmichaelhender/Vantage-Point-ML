import torch
import pandas as pd
import numpy as np
import joblib
from app.ml.tennis_encoder import TennisEncoder

def generate_final_dataset():
    # 1. Load the Encoders and the Processed Data
    df = pd.read_pickle('app/ml/data/processed_training_data.pkl')
    player_le = joblib.load('app/ml/models/player_encoder.pkl')
    surface_le = joblib.load('app/ml/models/surface_encoder.pkl')
    
    num_players = len(player_le.classes_) # Classes = Unique categories
    num_surfaces = len(surface_le.classes_)
    
    # Extracting the continuous columns and input dimemsion
    cont_cols = [c for c in df.columns if c.startswith(('p1_', 'p2_')) and not c.endswith('_idx')]
    input_dim = len(cont_cols)
    
    # Initialising the model
    model = TennisEncoder(num_players, num_surfaces, input_dim=input_dim) # Creating the model structure
    model.load_state_dict(torch.load('app/ml/models/tennis_encoder.pt')) # Adding in the trained weights
    model.eval() # Evaluation mode
    
    with torch.no_grad():
        # Extracting the all the player embeddings into a numpy array, 1000's of rows and 16 feature columns
        player_embedding_matrix = model.player_embed.weight.data.numpy()

        # Same for 4 feature surface embeddings
        surface_embedding_matrix = model.surface_embed.weight.data.numpy()
        
   
    # p1_embeddings = []
    # for idx in df['p1_id_idx'].values:
    #     row = player_embedding_matrix[idx]
    #     p1_embeddings.append(row)

    # Fancy indexing to make a make an array where each row a player's 16 dim embedding
    p1_embeddings = player_embedding_matrix[df['p1_id_idx'].values]
    p2_embeddings = player_embedding_matrix[df['p2_id_idx'].values]

    surf_embeddings = surface_embedding_matrix[df['surface_idx'].values]
    
    # Create column names: p1_emb_0, p1_emb_1 ...
    p1_emb_cols = [f'p1_emb_{i}' for i in range(16)]
    p2_emb_cols = [f'p2_emb_{i}' for i in range(16)]
    surf_emb_cols = [f'surf_emb_{i}' for i in range(4)]
    
    p1_emb_df = pd.DataFrame(p1_embeddings, columns=p1_emb_cols, index=df.index) # We preserve the index of the initial df
    p2_emb_df = pd.DataFrame(p2_embeddings, columns=p2_emb_cols, index=df.index)
    surf_emb_df = pd.DataFrame(surf_embeddings, columns=surf_emb_cols, index=df.index)
    
    # Quicker to concat that to merge
    final_df = pd.concat([df, p1_emb_df, p2_emb_df, surf_emb_df], axis=1)
    
    # Save as Parquet, Parquets come with a schema which preserve datatypes when loaded back in, they are also more size (MBs) efficient than csv's
    final_df.to_parquet('app/ml/data/final_training_set.parquet')
    print(f"Created Dataset: {final_df.shape[1]} features, {len(final_df)} rows.")

if __name__ == "__main__":
    generate_final_dataset()
