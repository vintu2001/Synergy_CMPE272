from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
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


class Status(str, Enum):
    SUBMITTED = "Submitted"
    PROCESSING = "Processing"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"


class HealthCheck(BaseModel):
    status: str
    service: str


class MessageRequest(BaseModel):
    resident_id: str = Field(..., description="Resident identifier")
    message_text: str = Field(..., description="Freeform text message from resident")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    category: Optional[IssueCategory] = Field(None, description="Optional category override")
    urgency: Optional[Urgency] = Field(None, description="Optional urgency override")


class ClassificationResponse(BaseModel):
    category: IssueCategory
    urgency: Urgency
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
    message_text: Optional[str] = Field(None, description="Original message text for risk prediction")



class RiskPredictionResponse(BaseModel):
    risk_forecast: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    recurrence_probability: Optional[float] = Field(None, ge=0.0, le=1.0)


class SimulatedOption(BaseModel):
    option_id: str
    action: str = Field(..., description="Description of the action")
    estimated_cost: float
    time_to_resolution: float = Field(..., description="Hours to resolve")
    resident_satisfaction_impact: float = Field(..., ge=0.0, le=1.0)


class SimulationResponse(BaseModel):
    options: List[SimulatedOption]
    issue_id: str


class DecisionResponse(BaseModel):
    chosen_action: str
    chosen_option_id: str
    reasoning: str
    alternatives_considered: List[str]


class ResidentRequest(BaseModel):
    request_id: str
    resident_id: str
    message_text: str
    category: IssueCategory
    urgency: Urgency
    intent: Intent
    status: Status
    risk_forecast: Optional[float] = None
    classification_confidence: Optional[float] = None
    simulated_options: Optional[List[Dict]] = None  # Store all simulation options
    chosen_action: Optional[str] = None
    chosen_option_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminRequestResponse(BaseModel):
    requests: List[ResidentRequest]
    total_count: int

