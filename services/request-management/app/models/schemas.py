"""
Schemas for Request Management Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
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
    simulated_options: Optional[List[Dict]] = None
    recommended_option_id: Optional[str] = None
    user_selected_option_id: Optional[str] = None
    chosen_action: Optional[str] = None
    chosen_option_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AdminRequestResponse(BaseModel):
    requests: List[ResidentRequest]
    total_count: int


class SelectOptionRequest(BaseModel):
    request_id: str = Field(..., description="Request ID")
    selected_option_id: str = Field(..., description="Option ID chosen by user")


class ResolveRequestModel(BaseModel):
    request_id: str = Field(..., description="Request ID to resolve")
    resolution_notes: Optional[str] = Field(None, description="Optional notes about resolution")
    resolved_by: str = Field(..., description="Who resolved it: 'admin' or 'resident'")
