import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_xgboost():
    print("📡 Loading Super-Dataset...")
    df = pd.read_parquet('app/ml/data/final_training_set.parquet')
    
    # Train on everything before 2025
    train_df = df[df['tourney_date'] < '2024-07-01']


    test_df = df[(df['tourney_date'] >= '2024-07-01') & (df['tourney_date'] < '2025-01-01')]
    
    # Only for evaluation after training
    excluded_df = df[df['tourney_date'] >= '2025-01-01']

    # Dropping down to the required features
    features = [c for c in df.columns if c not in [
        'p1_id', 'p2_id', 'p1_id_idx', 'p2_id_idx', 'surface', 
        'surface_idx', 'target', 'tourney_date'
    ]]
    
    X_train, y_train = train_df[features], train_df['target']
    X_test, y_test = test_df[features], test_df['target']
    X_excluded, y_excluded = excluded_df[features], excluded_df['target']


    # Initialize XGBoost
    model = xgb.XGBClassifier(
        n_estimators=2000, # Max number of decision trees
        learning_rate=0.02,
        max_depth=6, # Depth of each tree
        subsample=0.8, # Every tree can see this proportion of the training data
        colsample_bytree=0.6, # Every tree can see this proportion of the cols/features
        objective='binary:logistic', # Sets the type of problem for the model to solve
        early_stopping_rounds=100, # Smallest number of trees
        random_state=42, # Locking in a random state to be consistent
        tree_method='hist', # Faster training
    )

    # 4. Fit with Early Stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100 # Frequency of updates in terminal, per 100 trees
    )

    # Evaluate
    predictions = model.predict(X_excluded)
    accuracy = accuracy_score(y_excluded, predictions)
    
    print("\n--- Final Performance ---")
    print(f"✅ Accuracy: {accuracy:.2%}")
    print(classification_report(y_excluded, predictions))

    # Save the Final Model
    joblib.dump(model, 'app/ml/models/final_xgboost_model.pkl')
    # Save the list of feature names so the API knows the exact order later
    joblib.dump(features, 'app/ml/models/feature_names.pkl')
    print("🏁 Final Model saved to app/ml/models/final_xgboost_model.pkl")

    # Get feature importance
    importance = model.feature_importances_
    feature_names = X_train.columns
    feature_importance_df = pd.DataFrame({'feature': feature_names, 'importance': importance}).sort_values(by='importance', ascending=False)

    print("\n--- Top 10 Most Important Features ---")
    print(feature_importance_df.head(10))

if __name__ == "__main__":
    train_xgboost()
