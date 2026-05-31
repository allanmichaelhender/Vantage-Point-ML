import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
from datetime import datetime
import os
from sqlalchemy import create_engine
from app.ml.processor import TennisDataProcessor
from app.ml.tennis_encoder import TennisEncoder
import torch
import json
import numpy as np


def create_training_data(processor, NN_model, start_date="2015-01-01", end_date=None):
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    db_url = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2").replace("ssl=require", "sslmode=require")
    sync_engine = create_engine(db_url)

    query = """
            SELECT 
                id,
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
                l_rolling_return_won_pct, l_tournament_fatigue,
                w_embedding, l_embedding
            FROM matches 
            WHERE is_retirement = FALSE
            AND w_matches_played >= 10
            AND l_matches_played >= 10
            AND tourney_date >= %(start)s
            AND tourney_date < %(end)s
            ORDER BY tourney_date ASC, id ASC
        """

    df = pd.read_sql(query, sync_engine, params={"start": start_date, "end": end_date})

    w_cols = [f"w_vec_{i}" for i in range(1, 17)]
    l_cols = [f"l_vec_{i}" for i in range(1, 17)]

    w_list = df["w_embedding"].tolist()
    l_list = [x for x in df["l_embedding"] if x is not None]  # Basic NULL safety

    # Create DataFrames directly from the lists
    w_embedding_df = pd.DataFrame(w_list, index=df.index, columns=w_cols)
    l_embedding_df = pd.DataFrame(l_list, index=df.index, columns=l_cols)

    # Combine and drop raw columns
    df = pd.concat([df, w_embedding_df, l_embedding_df], axis=1)
    df = df.drop(columns=["w_embedding", "l_embedding"])

    regular_map = {
        "winner_id": "p1_id",
        "loser_id": "p2_id",
        "w_elo_before": "p1_elo",
        "l_elo_before": "p2_elo",
        "w_surface_elo_before": "p1_surf_elo",
        "l_surface_elo_before": "p2_surf_elo",
        "w_days_off": "p1_days_off",
        "l_days_off": "p2_days_off",
        "w_surface_days_off": "p1_surf_days_off",
        "l_surface_days_off": "p2_surf_days_off",
        "w_rolling_match_win_pct": "p1_m_win",
        "l_rolling_match_win_pct": "p2_m_win",
        "w_rolling_game_win_pct": "p1_g_win",
        "l_rolling_game_win_pct": "p2_g_win",
        "w_rolling_serve_won_pct": "p1_sv_won",
        "l_rolling_serve_won_pct": "p2_sv_won",
        "w_rolling_ace_per_game": "p1_ace_pg",
        "l_rolling_ace_per_game": "p2_ace_pg",
        "w_rolling_df_per_pt": "p1_df_pp",
        "l_rolling_df_per_pt": "p2_df_pp",
        "w_rolling_bp_save_pct": "p1_bp_s",
        "l_rolling_bp_save_pct": "p2_bp_s",
        "w_rolling_return_won_pct": "p1_ret_won",
        "l_rolling_return_won_pct": "p2_ret_won",
        "w_tournament_fatigue": "p1_fatigue",
        "l_tournament_fatigue": "p2_fatigue",
    }

    for i in range(1, 17):
        regular_map[f"w_vec_{i}"] = f"p1_vec_{i}"
        regular_map[f"l_vec_{i}"] = f"p2_vec_{i}"

    df_1 = df.copy()
    df_1 = df_1.rename(columns=regular_map)
    df_1["target"] = 1.0

    flip_map = {
        "winner_id": "p2_id",
        "loser_id": "p1_id",
        "w_elo_before": "p2_elo",
        "l_elo_before": "p1_elo",
        "w_surface_elo_before": "p2_surf_elo",
        "l_surface_elo_before": "p1_surf_elo",
        "w_days_off": "p2_days_off",
        "l_days_off": "p1_days_off",
        "w_surface_days_off": "p2_surf_days_off",
        "l_surface_days_off": "p1_surf_days_off",
        "w_rolling_match_win_pct": "p2_m_win",
        "l_rolling_match_win_pct": "p1_m_win",
        "w_rolling_game_win_pct": "p2_g_win",
        "l_rolling_game_win_pct": "p1_g_win",
        "w_rolling_serve_won_pct": "p2_sv_won",
        "l_rolling_serve_won_pct": "p1_sv_won",
        "w_rolling_ace_per_game": "p2_ace_pg",
        "l_rolling_ace_per_game": "p1_ace_pg",
        "w_rolling_df_per_pt": "p2_df_pp",
        "l_rolling_df_per_pt": "p1_df_pp",
        "w_rolling_bp_save_pct": "p2_bp_s",
        "l_rolling_bp_save_pct": "p1_bp_s",
        "w_rolling_return_won_pct": "p2_ret_won",
        "l_rolling_return_won_pct": "p1_ret_won",
        "w_tournament_fatigue": "p2_fatigue",
        "l_tournament_fatigue": "p1_fatigue",
    }

    for i in range(1, 17):
        flip_map[f"w_vec_{i}"] = f"p2_vec_{i}"
        flip_map[f"l_vec_{i}"] = f"p1_vec_{i}"

    df_0 = df.copy()
    df_0 = df_0.rename(columns=flip_map)
    df_0["target"] = 0.0

    # Combining the regular and flipped data
    combined_df = pd.concat([df_1, df_0], axis=0).reset_index(drop=True)
    combined_df = combined_df.fillna(0)

    cols_for_scaling = [
        c
        for c in combined_df.columns
        if c.startswith(("p1_", "p2_")) and not c.endswith("_id") and "vec" not in c
    ]
    combined_df[cols_for_scaling] = processor.scaler.transform(
        combined_df[cols_for_scaling]
    )

    with torch.no_grad():
        # This pulls the 4x4 matrix (4 surfaces, 4 dims)
        surf_weights = NN_model.surface_embed.weight.detach().cpu().numpy()

        # 🎯 2. Map weights to names (Hard, Clay, etc.)
        surf_labels = processor.surface_encoder.classes_
        surf_embedding_map = {
            label: surf_weights[i].tolist() for i, label in enumerate(surf_labels)
        }

        # Expand the 4 dimensions into columns: surf_vec_1, 2, 3, 4
        surf_embedding_list = combined_df["surface"].map(surf_embedding_map).tolist()
        surf_cols = [f"surf_vec_{i}" for i in range(1, 5)]
        surf_df = pd.DataFrame(
            surf_embedding_list, index=combined_df.index, columns=surf_cols
        )

        # Join to your main training set
        combined_df = pd.concat([combined_df, surf_df], axis=1)

    # Remember, our data is p1 wins first half, p2 wins second half, this line randomises the order to remove ordering bias
    combined_df = combined_df.sample(frac=1).reset_index(drop=True)

    return combined_df


def train_xgboost():
    processor = TennisDataProcessor()
    processor.player_encoder = joblib.load("app/ml/models/player_encoder.pkl")
    processor.surface_encoder = joblib.load("app/ml/models/surface_encoder.pkl")
    processor.scaler = joblib.load("app/ml/models/scaler.pkl")
    num_players = len(processor.player_encoder.classes_)
    num_surfaces = len(processor.surface_encoder.classes_)

    NN_model = TennisEncoder(
        num_players=num_players, num_surfaces=num_surfaces, input_dim=24
    )

    NN_model.load_state_dict(
        torch.load("app/ml/models/tennis_encoder_initial.pt", weights_only=True)
    )

    df = create_training_data(processor, NN_model)

    # Train on everything before 2025
    train_df = df[df["tourney_date"] < "2024-07-01"]

    test_df = df[
        (df["tourney_date"] >= "2024-07-01") & (df["tourney_date"] < "2025-01-01")
    ]

    # Only for evaluation after training
    excluded_df = df[df["tourney_date"] >= "2025-01-01"]

    # Dropping down to the required features
    features = [
        c
        for c in df.columns
        if c
        not in [
            "id",
            "p1_id",
            "p2_id",
            "p1_id_idx",
            "p2_id_idx",
            "surface",
            "target",
            "tourney_date",
        ]
    ]

    X_train, y_train = train_df[features], train_df["target"]
    X_test, y_test = test_df[features], test_df["target"]
    X_excluded, y_excluded = excluded_df[features], excluded_df["target"]

    # Initialize XGBoost
    XGBoost_model = xgb.XGBClassifier(
        n_estimators=2000,  # Max number of decision trees
        learning_rate=0.02,
        max_depth=6,  # Depth of each tree
        subsample=0.8,  # Every tree can see this proportion of the training data
        colsample_bytree=0.6,  # Every tree can see this proportion of the cols/features
        objective="binary:logistic",  # Sets the type of problem for the model to solve
        early_stopping_rounds=100,  # Smallest number of trees
        random_state=42,  # Locking in a random state to be consistent
        tree_method="hist",  # Faster training
    )

    # 4. Fit with Early Stopping
    XGBoost_model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=100,  # Frequency of updates in terminal, per 100 trees
    )

    # Evaluate
    predictions = XGBoost_model.predict(X_excluded)
    accuracy = accuracy_score(y_excluded, predictions)

    print("\n--- Final Performance ---")
    print(f"✅ Accuracy: {accuracy:.2%}")
    print(classification_report(y_excluded, predictions))

    # Save the Final Model
    joblib.dump(XGBoost_model, "app/ml/models/XGBoost&NN.pkl")
    # Save the list of feature names so the API knows the exact order later
    joblib.dump(features, "app/ml/models/feature_names.pkl")
    print("🏁 Final Model saved to app/ml/models/XGBoost&NN.pkl")

    # Get feature importance
    importance = XGBoost_model.feature_importances_
    feature_names = X_train.columns
    feature_importance_df = pd.DataFrame(
        {"feature": feature_names, "importance": importance}
    ).sort_values(by="importance", ascending=False)

    print("\n--- Top 10 Most Important Features ---")
    print(feature_importance_df)


if __name__ == "__main__":
    train_xgboost()
