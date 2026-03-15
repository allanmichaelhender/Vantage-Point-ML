import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from app.ml.tennis_encoder import TennisEncoder

def train_encoder():
    # Loading in the data, remember we use pkl to load in DF more seamlessly
    df = pd.read_pickle('app/ml/data/processed_training_data.pkl')

    df['tourney_date'] = pd.to_datetime(df['tourney_date'])
    df = df[
    #(df['tourney_date'] >= '2023-01-01') & 
    (df['tourney_date'] < '2025-01-01')
].copy()
    
    print(f"📅 Training NN Encoder on matches BEFORE 2025. Rows: {len(df)}")
    
    # Categorical Indexes
    p1_idx = torch.tensor(df['p1_id_idx'].values, dtype=torch.long)
    p2_idx = torch.tensor(df['p2_id_idx'].values, dtype=torch.long)
    surf_idx = torch.tensor(df['surface_idx'].values, dtype=torch.long)
    
    # Continuous Features
    cont_cols = [c for c in df.columns if c.startswith(('p1_', 'p2_')) and not c.endswith('_id') and not c.endswith('_idx')]

    
    # Converting to floats and dealing with nulls, coerce fills unknowns with Nan and those get 0'd
    for col in cont_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    # Preparing the performance stats
    performance_stats = torch.tensor(df[cont_cols].values, dtype=torch.float32)

    input_dim = performance_stats.shape[1] # Number of input features
    
    # Target setup, unsqueeze turns it into a column to match dimensions
    target = torch.tensor(df['target'].values, dtype=torch.float32).unsqueeze(1)

    # Grouping/associating all the data together
    dataset = TensorDataset(p1_idx, p2_idx, surf_idx, performance_stats, target)
    train_size = int(0.8 * len(dataset))
    validation_set_size = len(dataset) - train_size

    # Creating our training and validation set
    train_db, validation_set_db = torch.utils.data.random_split(dataset, [train_size, validation_set_size])

    train_loader = DataLoader(train_db, batch_size=256, shuffle=True)
    validation_set_loader = DataLoader(validation_set_db, batch_size=256)

    # Initialize the Encoder
    num_players = len(joblib.load('app/ml/models/player_encoder.pkl').classes_) # Uniqueness of players is preserved
    num_surfaces = len(joblib.load('app/ml/models/surface_encoder.pkl').classes_)
    
    model = TennisEncoder(num_players, num_surfaces, input_dim=input_dim)
    criterion = nn.BCELoss() # Binary Cross Entropy for Win/Loss
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training Loop, Epoch equals a fill pars through the dataset
    for epoch in range(10): 
        model.train() # Turns on learning mode
        total_loss = 0
        for p1, p2, surf, stats, y in train_loader: # Loading in a batch size of data
            optimizer.zero_grad() # zero's the optimizer from the last batch
            outputs = model(p1, p2, surf, stats) # runs the model
            loss = criterion(outputs, y) # compares the model output to expected and calculates the loss over the batch
            loss.backward() # assigns gradients to every weight
            optimizer.step() # enacting the changes
            total_loss += loss.item() # adding on the loss of this batch
        
        # Validation Check
        model.eval() # Puts model in evaluation mode
        correct = 0
        with torch.no_grad(): # Tells torch not to save any data
            for p1, p2, surf, stats, y in validation_set_loader:
                outputs = model(p1, p2, surf, stats)
                predicted = (outputs > 0.5).float()
                correct += (predicted == y).sum().item()
        
        accuracy = correct / validation_set_size
        print(f"Epoch {epoch+1}/10 | Loss: {total_loss/len(train_loader):.4f} | Val Acc: {accuracy:.2%}") # Thats loss per bastch size here

    # Saving the encoder
    torch.save(model.state_dict(), 'app/ml/models/tennis_encoder.pt')
    print("Encoder trained and saved to app/ml/models/tennis_encoder.pt")

if __name__ == "__main__":
    train_encoder()
