from fastapi import APIRouter
from app.models.schemas import MessageRequest, ClassificationResponse, RiskPredictionResponse
from app.agents.classification_agent import classify_message
from app.agents.risk_prediction_agent import predict_risk
from app.utils.cloudwatch_logger import log_to_cloudwatch

router = APIRouter()


@router.post("/classify", response_model=ClassificationResponse)
async def classify_endpoint(request: MessageRequest) -> ClassificationResponse:

    result = await classify_message(request)
    
    log_to_cloudwatch('classification_completed', {
        'resident_id': request.resident_id,
        'message_preview': request.message_text[:100],
        'category': result.category.value,
        'urgency': result.urgency.value,
        'intent': result.intent.value,
        'confidence': round(result.confidence, 3),
        'classification_method': 'gemini' if result.confidence < 0.7 else 'rule_based'
    })
    
    return result


@router.post("/predict-risk", response_model=RiskPredictionResponse)
async def predict_risk_endpoint(classification: ClassificationResponse) -> RiskPredictionResponse:

    result = await predict_risk(classification)
    
    log_to_cloudwatch('risk_prediction_completed', {
        'category': classification.category.value,
        'urgency': classification.urgency.value,
        'risk_forecast': round(result.risk_forecast, 3),
        'recurrence_probability': round(result.recurrence_probability, 3) if result.recurrence_probability else None,
        'risk_level': 'high' if result.risk_forecast > 0.7 else 'medium' if result.risk_forecast > 0.4 else 'low'
    })
    
    return result
