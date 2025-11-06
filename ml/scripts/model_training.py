"""
Model Training Script
Trains ML model to predict issue recurrence and risk scores.

Usage:
    python ml/scripts/model_training.py
    
Output:
    - ml/models/risk_prediction_model.pkl
    - ml/models/label_encoders.pkl
    - ml/models/feature_columns.pkl
    - ml/models/model_metadata.json
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')


def load_and_prepare_data(data_path: Path) -> pd.DataFrame:
    """Load synthetic messages and extract features."""
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    import ast
    df['metadata_dict'] = df['metadata'].apply(ast.literal_eval)
    df['is_business_hours'] = df['metadata_dict'].apply(lambda x: x.get('is_business_hours', False))
    df['is_weekend'] = df['metadata_dict'].apply(lambda x: x.get('is_weekend', False))
    df['is_escalation'] = df['metadata_dict'].apply(lambda x: x.get('is_escalation', False))
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    
    resident_counts = df.groupby('resident_id').size().to_dict()
    df['resident_request_count'] = df['resident_id'].map(resident_counts)
    df['has_multiple_requests'] = df['resident_request_count'] > 1
    
    resident_category_counts = df.groupby(['resident_id', 'true_category']).size().to_dict()
    df['resident_category_count'] = df.apply(
        lambda row: resident_category_counts.get((row['resident_id'], row['true_category']), 1),
        axis=1
    )
    df['is_recurring_category'] = df['resident_category_count'] > 1
    
    print(f"✓ Loaded {len(df)} messages")
    return df


def calculate_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate risk score target variable."""
    print("Calculating risk scores...")
    
    def calc_risk(row):
        score = 0.0
        urgency_map = {'High': 0.8, 'Medium': 0.5, 'Low': 0.2}
        score += urgency_map.get(row['true_urgency'], 0.5)
        
        if row['is_escalation']:
            score += 0.2
        if row['is_recurring_category']:
            score += 0.15
        if not row['is_business_hours']:
            score += 0.05
        if row['is_weekend']:
            score += 0.05
        
        category_risk = {
            'Maintenance': 0.05,
            'Security': 0.1,
            'Billing': 0.0,
            'Deliveries': 0.0,
            'Amenities': -0.05
        }
        score += category_risk.get(row['true_category'], 0.0)
        
        return min(max(score, 0.0), 1.0)
    
    df['risk_score'] = df.apply(calc_risk, axis=1)
    print(f"✓ Risk scores calculated (mean: {df['risk_score'].mean():.3f})")
    return df


def engineer_features(df: pd.DataFrame) -> tuple:
    """Create features and encode categoricals."""
    print("Engineering features...")
    
    # Text features
    df['message_length'] = df['message_text'].str.len()
    df['word_count'] = df['message_text'].str.split().str.len()
    df['has_urgent_keywords'] = df['message_text'].str.lower().str.contains(
        'urgent|emergency|asap|immediately', regex=True, na=False
    ).astype(int)
    df['has_question_mark'] = df['message_text'].str.contains('\\?', na=False).astype(int)
    df['has_exclamation'] = df['message_text'].str.contains('!', na=False).astype(int)
    
    # Temporal features
    df['is_early_morning'] = ((df['hour'] >= 0) & (df['hour'] < 6)).astype(int)
    df['is_morning'] = ((df['hour'] >= 6) & (df['hour'] < 12)).astype(int)
    df['is_afternoon'] = ((df['hour'] >= 12) & (df['hour'] < 18)).astype(int)
    df['is_evening'] = ((df['hour'] >= 18) & (df['hour'] < 24)).astype(int)
    
    # Encode categoricals
    label_encoders = {}
    
    le_category = LabelEncoder()
    df['category_encoded'] = le_category.fit_transform(df['true_category'])
    label_encoders['category'] = le_category
    
    le_urgency = LabelEncoder()
    df['urgency_encoded'] = le_urgency.fit_transform(df['true_urgency'])
    label_encoders['urgency'] = le_urgency
    
    le_intent = LabelEncoder()
    df['intent_encoded'] = le_intent.fit_transform(df['intent'])
    label_encoders['intent'] = le_intent
    
    # Convert booleans to int
    bool_cols = ['is_business_hours', 'is_weekend', 'has_multiple_requests', 'is_recurring_category', 'is_escalation']
    for col in bool_cols:
        df[col] = df[col].astype(int)
    
    print(f"✓ Features engineered")
    return df, label_encoders


def train_model(df: pd.DataFrame, label_encoders: dict) -> tuple:
    """Train XGBoost model."""
    print("\nTraining XGBoost model...")
    
    feature_columns = [
        'category_encoded', 'urgency_encoded', 'intent_encoded',
        'message_length', 'word_count', 'has_urgent_keywords',
        'has_question_mark', 'has_exclamation',
        'hour', 'is_business_hours', 'is_weekend',
        'is_early_morning', 'is_morning', 'is_afternoon', 'is_evening',
        'resident_request_count', 'has_multiple_requests',
        'resident_category_count', 'is_recurring_category', 'is_escalation'
    ]
    
    X = df[feature_columns]
    y = df['risk_score']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train model
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    # In newer XGBoost versions, use eval_set without eval_metric parameter
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # Evaluate
    y_train_pred = np.clip(model.predict(X_train), 0, 1)
    y_test_pred = np.clip(model.predict(X_test), 0, 1)
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    
    print(f"\n{'='*60}")
    print("MODEL PERFORMANCE")
    print(f"{'='*60}")
    print(f"Training MAE:  {train_mae:.4f}")
    print(f"Test MAE:      {test_mae:.4f}")
    print(f"Training RMSE: {train_rmse:.4f}")
    print(f"Test RMSE:     {test_rmse:.4f}")
    print(f"{'='*60}\n")
    
    return model, feature_columns, (train_mae, test_mae, train_rmse, test_rmse)


def save_model_artifacts(model, feature_columns, label_encoders, metrics, output_dir: Path):
    """Save trained model and metadata."""
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"Saving model artifacts to {output_dir}...")
    
    # Save model
    model_path = output_dir / 'risk_prediction_model.pkl'
    joblib.dump(model, model_path)
    print(f"✓ Model saved: {model_path}")
    
    # Save encoders
    encoders_path = output_dir / 'label_encoders.pkl'
    joblib.dump(label_encoders, encoders_path)
    print(f"✓ Encoders saved: {encoders_path}")
    
    # Save features
    features_path = output_dir / 'feature_columns.pkl'
    joblib.dump(feature_columns, features_path)
    print(f"✓ Features saved: {features_path}")
    
    # Save metadata
    train_mae, test_mae, train_rmse, test_rmse = metrics
    metadata = {
        'model_type': 'XGBRegressor',
        'trained_date': datetime.now().isoformat(),
        'num_features': len(feature_columns),
        'feature_names': feature_columns,
        'metrics': {
            'train_mae': float(train_mae),
            'test_mae': float(test_mae),
            'train_rmse': float(train_rmse),
            'test_rmse': float(test_rmse)
        },
        'hyperparameters': {
            'n_estimators': int(model.n_estimators),
            'max_depth': int(model.max_depth),
            'learning_rate': float(model.learning_rate)
        },
        'category_mapping': {int(k): v for k, v in enumerate(label_encoders['category'].classes_)},
        'urgency_mapping': {int(k): v for k, v in enumerate(label_encoders['urgency'].classes_)},
        'intent_mapping': {int(k): v for k, v in enumerate(label_encoders['intent'].classes_)}
    }
    
    metadata_path = output_dir / 'model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved: {metadata_path}")


def train_risk_prediction_model(data_path: Path, output_dir: Path):
    """
    Main training pipeline.
    
    Args:
        data_path: Path to synthetic_messages.csv
        output_dir: Directory to save model artifacts
    """
    print("="*60)
    print("TICKET 8: RISK PREDICTION MODEL TRAINING")
    print("="*60)
    
    # Load data
    df = load_and_prepare_data(data_path)
    
    # Calculate targets
    df = calculate_risk_scores(df)
    
    # Engineer features
    df, label_encoders = engineer_features(df)
    
    # Train model
    model, feature_columns, metrics = train_model(df, label_encoders)
    
    # Save artifacts
    save_model_artifacts(model, feature_columns, label_encoders, metrics, output_dir)
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE")
    print("="*60)
    print(f"\nNext steps:")
    print("1. Review model performance (MAE < 0.10 is good)")
    print("2. Copy artifacts to backend/app/ml_models/")
    print("3. Update backend/app/agents/risk_prediction_agent.py")
    print("4. Test with: curl -X POST http://localhost:8000/api/v1/predict-risk")
    print("\nSee docs/TICKET_8_9_IMPLEMENTATION_GUIDE.md for details")


if __name__ == "__main__":
    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "ml/data/synthetic_messages.csv"
    output_dir = project_root / "ml/models"
    
    # Check data exists
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        print("\nGenerate synthetic data first:")
        print("  python ml/scripts/synthetic_message_generator.py")
        exit(1)
    
    # Train model
    train_risk_prediction_model(data_path, output_dir)

