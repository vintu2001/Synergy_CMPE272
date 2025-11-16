"""
Schemas for AI Processing Service
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Urgency(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IssueCategory(str, Enum):
    MAINTENANCE = "Maintenance"
    BILLING = "Billing"
    SECURITY = "Security"
    DELIVERIES = "Deliveries"
    AMENITIES = "Amenities"


class Intent(str, Enum):
    SOLVE_PROBLEM = "solve_problem"
    HUMAN_ESCALATION = "human_escalation"
    ANSWER_QUESTION = "answer_a_question"


class HealthCheck(BaseModel):
    status: str
    service: str


class MessageRequest(BaseModel):
    resident_id: str = Field(..., description="Resident identifier")
    message_text: str = Field(..., description="Freeform text message from resident")


class ClassificationResponse(BaseModel):
    category: IssueCategory
    urgency: Urgency
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
    message_text: Optional[str] = Field(None, description="Original message text for risk prediction")


class RiskPredictionResponse(BaseModel):
    risk_forecast: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    recurrence_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
