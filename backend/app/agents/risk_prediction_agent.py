"""
Risk Prediction Agent
Uses trained ML model to predict issue recurrence and risk scores.
"""
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.schemas import ClassificationResponse, RiskPredictionResponse

router = APIRouter()

_model_cache = {
    'model': None,
    'encoders': None,
    'features': None,
    'metadata': None
}

def load_model_artifacts():
    """Load trained model artifacts on first request."""
    if _model_cache['model'] is not None:
        return
    
    try:
        models_dir = Path(__file__).parent.parent / 'ml_models'
        
        _model_cache['model'] = joblib.load(models_dir / 'risk_prediction_model.pkl')
        _model_cache['encoders'] = joblib.load(models_dir / 'label_encoders.pkl')
        _model_cache['features'] = joblib.load(models_dir / 'feature_columns.pkl')
        
        import json
        with open(models_dir / 'model_metadata.json', 'r') as f:
            _model_cache['metadata'] = json.load(f)
        
        print(f"✅ ML Model loaded: Test MAE = {_model_cache['metadata']['metrics']['test_mae']:.4f}")
    except Exception as e:
        raise RuntimeError(f"Failed to load ML model artifacts: {e}")


def engineer_features(classification: ClassificationResponse) -> pd.DataFrame:
    """
    Convert classification response to feature vector for ML model.
    Feature engineering pipeline matches the training data format.
    """
    encoders = _model_cache['encoders']
    
    message_text = classification.message_text or "Default maintenance request"
    
    category_encoded = encoders['category'].transform([classification.category])[0]
    urgency_encoded = encoders['urgency'].transform([classification.urgency])[0]
    intent_encoded = encoders['intent'].transform([classification.intent])[0]
    
    message_length = len(message_text)
    word_count = len(message_text.split())
    has_urgent_keywords = 1 if any(kw in message_text.lower() for kw in 
                                    ['urgent', 'emergency', 'asap', 'immediately', 'critical']) else 0
    has_question_mark = 1 if '?' in message_text else 0
    has_exclamation = 1 if '!' in message_text else 0
    
    now = datetime.now()
    hour = now.hour
    is_business_hours = 1 if 9 <= hour < 18 else 0
    is_weekend = 1 if now.weekday() >= 5 else 0
    is_early_morning = 1 if 0 <= hour < 6 else 0
    is_morning = 1 if 6 <= hour < 12 else 0
    is_afternoon = 1 if 12 <= hour < 18 else 0
    is_evening = 1 if 18 <= hour < 24 else 0
    
    resident_request_count = 3
    has_multiple_requests = 1 if resident_request_count > 1 else 0
    resident_category_count = 2
    is_recurring_category = 1 if resident_category_count > 1 else 0
    
    is_escalation = 0
    
    features = {
        'category_encoded': category_encoded,
        'urgency_encoded': urgency_encoded,
        'intent_encoded': intent_encoded,
        'message_length': message_length,
        'word_count': word_count,
        'has_urgent_keywords': has_urgent_keywords,
        'has_question_mark': has_question_mark,
        'has_exclamation': has_exclamation,
        'hour': hour,
        'is_business_hours': is_business_hours,
        'is_weekend': is_weekend,
        'is_early_morning': is_early_morning,
        'is_morning': is_morning,
        'is_afternoon': is_afternoon,
        'is_evening': is_evening,
        'resident_request_count': resident_request_count,
        'has_multiple_requests': has_multiple_requests,
        'resident_category_count': resident_category_count,
        'is_recurring_category': is_recurring_category,
        'is_escalation': is_escalation
    }
    
    feature_columns = _model_cache['features']
    df = pd.DataFrame([features], columns=feature_columns)
    
    return df


@router.post("/predict-risk", response_model=RiskPredictionResponse)
async def predict_risk(classification: ClassificationResponse) -> RiskPredictionResponse:
    """
    Predict risk score and recurrence probability for a classified message.
    Returns risk_forecast ∈ [0,1] and recurrence_probability.
    """
    try:
        load_model_artifacts()
        
        feature_df = engineer_features(classification)
        
        model = _model_cache['model']
        risk_forecast = float(model.predict(feature_df)[0])
        
        risk_forecast = np.clip(risk_forecast, 0.0, 1.0)
        
        recurrence_probability = risk_forecast * 0.7
        
        return RiskPredictionResponse(
            risk_forecast=risk_forecast,
            recurrence_probability=recurrence_probability
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction failed: {str(e)}"
        )


