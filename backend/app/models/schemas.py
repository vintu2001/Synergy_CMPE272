"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class Urgency(str, Enum):
    """Urgency levels for issues"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IssueCategory(str, Enum):
    """Issue categories"""
    MAINTENANCE = "Maintenance"
    BILLING = "Billing"
    SECURITY = "Security"
    DELIVERIES = "Deliveries"
    AMENITIES = "Amenities"


class Intent(str, Enum):
    """Resident intent types"""
    SOLVE_PROBLEM = "solve_problem"
    HUMAN_ESCALATION = "human_escalation"


class Status(str, Enum):
    """Request status"""
    SUBMITTED = "Submitted"
    PROCESSING = "Processing"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    service: str


class MessageRequest(BaseModel):
    """Incoming message from resident"""
    resident_id: str = Field(..., description="Resident identifier")
    message_text: str = Field(..., description="Freeform text message from resident")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ClassificationResponse(BaseModel):
    """Classification agent response"""
    category: IssueCategory
    urgency: Urgency
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)


class RiskPredictionResponse(BaseModel):
    """Risk prediction agent response"""
    risk_forecast: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    recurrence_probability: Optional[float] = Field(None, ge=0.0, le=1.0)


class SimulatedOption(BaseModel):
    """A simulated resolution option"""
    option_id: str
    action: str = Field(..., description="Description of the action")
    estimated_cost: float
    time_to_resolution: float = Field(..., description="Hours to resolve")
    resident_satisfaction_impact: float = Field(..., ge=0.0, le=1.0)


class SimulationResponse(BaseModel):
    """Simulation agent response"""
    options: List[SimulatedOption]
    issue_id: str


class DecisionResponse(BaseModel):
    """Decision agent response"""
    chosen_action: str
    chosen_option_id: str
    reasoning: str
    alternatives_considered: List[str]


class ResidentRequest(BaseModel):
    """Full resident request record"""
    request_id: str
    resident_id: str
    message_text: str
    category: IssueCategory
    urgency: Urgency
    intent: Intent
    status: Status
    risk_forecast: Optional[float] = None
    classification_confidence: Optional[float] = None
    chosen_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminRequestResponse(BaseModel):
    """Admin dashboard response model"""
    requests: List[ResidentRequest]
    total_count: int

