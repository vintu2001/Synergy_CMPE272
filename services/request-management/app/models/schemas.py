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


class ResidentPreferences(BaseModel):
    """Resident preferences for service appointments"""
    allow_entry_when_absent: bool = Field(default=False, description="Permission for technician to enter if resident is not home")
    preferred_time_slots: Optional[List[str]] = Field(None, description="Preferred time slots (e.g., 'morning', 'afternoon', 'evening', '9am-12pm')")
    preferred_days: Optional[List[str]] = Field(None, description="Preferred days (e.g., 'Monday', 'Tuesday', 'weekdays', 'weekends')")
    avoid_days: Optional[List[str]] = Field(None, description="Days to avoid (e.g., 'Monday', 'Tuesday')")
    special_instructions: Optional[str] = Field(None, description="Any special instructions for the technician")
    contact_before_arrival: bool = Field(default=True, description="Should technician contact before arriving")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact number if different from resident")
    
    class Config:
        extra = "allow"


class MessageRequest(BaseModel):
    resident_id: str = Field(..., description="Resident identifier")
    message_text: str = Field(..., description="Freeform text message from resident")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    category: Optional[IssueCategory] = Field(None, description="Optional category override")
    urgency: Optional[Urgency] = Field(None, description="Optional urgency override")
    preferences: Optional[ResidentPreferences] = Field(None, description="Resident preferences for service appointments")


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
    admin_comments: Optional[List[Dict]] = None
    recurring_issue_non_escalated: Optional[bool] = None
    is_recurring_issue: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None  # Store resident preferences
    created_at: datetime
    updated_at: datetime
    
    class Config:
        # Allow extra fields from DynamoDB that might not be in the schema
        extra = "allow"


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


class UpdateStatusRequest(BaseModel):
    request_id: str = Field(..., description="Request ID to update")
    status: Status = Field(..., description="New status for the request")


class AddCommentRequest(BaseModel):
    request_id: str = Field(..., description="Request ID to add comment to")
    comment: str = Field(..., description="Comment text to add")
    added_by: str = Field(..., description="Who added the comment: 'admin' or 'resident'")
