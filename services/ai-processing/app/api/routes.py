"""
AI Processing API routes
Handles message classification and risk prediction.
"""
from fastapi import APIRouter
from app.models.schemas import MessageRequest, ClassificationResponse, RiskPredictionResponse
from app.agents.classification_agent import classify_message
from app.agents.risk_prediction_agent import predict_risk

router = APIRouter()


@router.post("/classify", response_model=ClassificationResponse)
async def classify_endpoint(request: MessageRequest) -> ClassificationResponse:
    """
    Classify a resident message into category, urgency, and intent.
    """
    return await classify_message(request)


@router.post("/predict-risk", response_model=RiskPredictionResponse)
async def predict_risk_endpoint(classification: ClassificationResponse) -> RiskPredictionResponse:
    """
    Predict risk score and recurrence probability for a classified message.
    """
    return await predict_risk(classification)
