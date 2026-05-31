import pandas as pd
from datetime import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from app.ml.tennis_encoder import TennisEncoder
from app.ml.processor import TennisDataProcessor
from sqlalchemy import create_engine, text
import os
import json
import joblib
import numpy as np


def nudge_encoder_in_memory(model, df, epochs=3, lr=0.0001):
    # 1. Prep Tensors (Same as before)
    p1_idx = torch.tensor(df["p1_id_idx"].values, dtype=torch.long)
    p2_idx = torch.tensor(df["p2_id_idx"].values, dtype=torch.long)
    surf_idx = torch.tensor(df["surface_idx"].values, dtype=torch.long)

    cont_cols = [
        c
        for c in df.columns
        if c.startswith(("p1_", "p2_"))
        and not c.endswith("_id")
        and not c.endswith("_idx")
    ]
    stats = torch.tensor(df[cont_cols].values, dtype=torch.float32)
    target = torch.tensor(df["target"].values, dtype=torch.float32).unsqueeze(1)

    # 2. Setup DataLoader
    dataset = TensorDataset(p1_idx, p2_idx, surf_idx, stats, target)
    loader = DataLoader(dataset, batch_size=256, shuffle=True)

    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    # 🎯 4. The Nudge (1-2 Epochs)
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0
        for b_p1, b_p2, b_surf, b_stats, b_y in loader:
            optimizer.zero_grad()
            outputs = model(b_p1, b_p2, b_surf, b_stats)
            loss = criterion(outputs, b_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()


    return model


def hydrate_nn_probs(processor, model, start_date, end_date):
    db_url = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2").replace("ssl=require", "sslmode=require")
    sync_engine = create_engine(db_url)

    raw_data = processor.fetch_raw_data(start_date, end_date)

    if raw_data.empty:  # Required incase we look into the future
        return

    processed_data = processor.process_and_balance(df=raw_data, frozen=True)

    model.eval()
    with torch.no_grad():
        # 🎯 Ensure these match your train_encoder exactly
        p1_id_idx_list = torch.tensor(
            processed_data["p1_id_idx"].values, dtype=torch.long
        )
        p2_id_idx_list = torch.tensor(
            processed_data["p2_id_idx"].values, dtype=torch.long
        )
        surf_idx_list = torch.tensor(
            processed_data["surface_idx"].values, dtype=torch.long
        )

        cont_cols = [
            c
            for c in processed_data.columns
            if c.startswith(("p1_", "p2_"))
            and not c.endswith("_id")
            and not c.endswith("_idx")
        ]
        stats = torch.tensor(processed_data[cont_cols].values, dtype=torch.float32)

        # Get the raw 0-1 win probability for Player 1
        probs = (
            model(p1_id_idx_list, p2_id_idx_list, surf_idx_list, stats)
            .numpy()
            .flatten()
        )

    processed_data["p1_win_prob"] = [
        p if t == 1.0 else (1.0 - p) for p, t in zip(probs, processed_data["target"])
    ]

    id_to_nn_prob = processed_data.groupby("id")["p1_win_prob"].mean().to_dict()

    params = [{"p": float(p), "m_id": int(mid)} for mid, p in id_to_nn_prob.items()]
    with sync_engine.begin() as conn:
        conn.execute(
            text("UPDATE matches SET nn_p1_prob = :p WHERE id = :m_id"), params
        )


def hydrate_match_embeddings(start_date, end_date, id_to_emb):
    db_url = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2").replace("ssl=require", "sslmode=require")
    sync_engine = create_engine(db_url)

    with sync_engine.begin() as conn:
        # 1. Fetch
        matches = pd.read_sql(
            "SELECT id, winner_id, loser_id FROM matches WHERE tourney_date >= %(start)s AND tourney_date < %(end)s",
            conn,
            params={"start": start_date, "end": end_date},
        )

        # 2. Update
        for _, row in matches.iterrows():
            w_vec = id_to_emb.get(row["winner_id"])
            l_vec = id_to_emb.get(row["loser_id"])

            if w_vec and l_vec is not None:
                conn.execute(
                    text(
                        "UPDATE matches SET w_embedding = :w, l_embedding = :l WHERE id = :id"
                    ),
                    {"w": json.dumps(w_vec), "l": json.dumps(l_vec), "id": row["id"]},
                )


def main():
    # 🎯 THE CONFIG
    START_DATE = pd.to_datetime("2015-01-01")
    END_DATE = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
    LOOKBACK_YEARS = 2
    current_date = START_DATE

    processor = TennisDataProcessor()
    processor.player_encoder = joblib.load("app/ml/models/player_encoder.pkl")
    processor.surface_encoder = joblib.load("app/ml/models/surface_encoder.pkl")
    processor.scaler = joblib.load("app/ml/models/scaler.pkl")
    num_players = len(processor.player_encoder.classes_)
    num_surfaces = len(processor.surface_encoder.classes_)

    model = TennisEncoder(
        num_players=num_players, num_surfaces=num_surfaces, input_dim=24
    )

    model.load_state_dict(
        torch.load("app/ml/models/tennis_encoder_initial.pt", weights_only=True)
    )

    while current_date < END_DATE:
        training_start = current_date - pd.DateOffset(years=LOOKBACK_YEARS)

        stamp_start = current_date
        stamp_end = current_date + pd.DateOffset(months=2)

        raw_train = processor.fetch_raw_data(training_start, current_date)
        processed_train = processor.process_and_balance(df=raw_train, frozen=True)

        model= nudge_encoder_in_memory(model, processed_train)

        hydrate_nn_probs(
            processor=processor, model=model, start_date=stamp_start, end_date=stamp_end
        )

        with torch.no_grad():
            # .cpu() ensures it's off the GPU, .numpy() turns it into a standard array
            player_embedding_matrix = model.player_embed.weight.detach().cpu().numpy()

        # 🎯 2. Get the list of Player IDs in the exact same order
        # Your LabelEncoder.classes_ is the 'Key' to this matrix
        player_ids = processor.player_encoder.classes_

        # 🎯 3. Map the IDs to the Vectors
        # We create a dictionary: { "A0E2": [0.1, -0.5, ...], "RH16": [...] }
        id_to_embedding = {
            player_id: player_embedding_matrix[i].tolist()
            for i, player_id in enumerate(player_ids)
        }

        hydrate_match_embeddings(
            start_date=stamp_start,
            end_date=stamp_end,
            id_to_emb=id_to_embedding,
        )
        # Move to the next 2-month block
        current_date = stamp_end

    torch.save(model.state_dict(), "app/ml/models/tennis_encoder_final.pt")


if __name__ == "__main__":
    main()
