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


class PolicyWeights(BaseModel):
    urgency_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for urgency in decision scoring")
    cost_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for cost in decision scoring")
    time_weight: float = Field(0.2, ge=0.0, le=1.0, description="Weight for resolution time in decision scoring")
    satisfaction_weight: float = Field(0.1, ge=0.0, le=1.0, description="Weight for resident satisfaction in decision scoring")


class CostAnalysis(BaseModel):
    option_id: str
    estimated_cost: float
    exceeds_scale: bool
    scaled_cost: float

class TimeAnalysis(BaseModel):
    option_id: str
    estimated_time: float
    exceeds_scale: bool
    scaled_time: float

class DecisionReasoning(BaseModel):
    chosen_action: str = Field(..., description="The selected action to take")
    policy_scores: Dict[str, float] = Field(..., description="Scores for each option considered")
    considerations: List[str] = Field(..., description="List of all options considered with their scores")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation if applicable")
    cost_analysis: List[CostAnalysis] = Field(..., description="Cost analysis for business review")
    time_analysis: List[TimeAnalysis] = Field(..., description="Time analysis for business review")
    total_estimated_cost: float = Field(..., description="Total cost of chosen option")
    total_estimated_time: float = Field(..., description="Total time of chosen option")
    exceeds_budget_threshold: bool = Field(..., description="Indicates if any options exceed the cost scale")
    exceeds_time_threshold: bool = Field(..., description="Indicates if any options exceed the time scale")


class PolicyConfiguration(BaseModel):
    max_cost: float = Field(1000.0, gt=0.0, description="Maximum cost threshold for scaling calculations")
    max_time: float = Field(72.0, gt=0.0, description="Maximum resolution time in hours")


class DecisionResponse(BaseModel):
    chosen_action: str
    chosen_option_id: str
    reasoning: str
    alternatives_considered: List[str]
    policy_scores: Optional[Dict[str, float]] = None
    escalation_reason: Optional[str] = None


class DecisionRequest(BaseModel):
    """
    Request model for decision making endpoint.
    """
    classification: ClassificationResponse = Field(
        ...,
        description="Classification results including category, urgency, and intent"
    )
    simulation: SimulationResponse = Field(
        ...,
        description="Simulated options for resolving the issue"
    )
    weights: PolicyWeights = Field(
        default=PolicyWeights(),
        description="Custom weights for decision factors (optional)"
    )
    config: PolicyConfiguration = Field(
        default=PolicyConfiguration(),
        description="Configuration for cost and time thresholds (optional)"
    )


class DecisionResponseWithStatus(DecisionResponse):
    """
    Enhanced decision response with status information.
    """
    request_id: str = Field(default_factory=lambda: f"dec_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="success")
    processing_time: float = Field(default=0.0)


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

