from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
    details: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed step-by-step breakdown for UI dropdown")


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
    recommended_option_id: Optional[str] = None  # AI-recommended option
    user_selected_option_id: Optional[str] = None  # User's actual choice
    chosen_action: Optional[str] = None
    chosen_option_id: Optional[str] = None
    resolution_notes: Optional[str] = None  # Notes when marking resolved
    resolved_by: Optional[str] = None  # Who resolved it (admin/resident)
    resolved_at: Optional[datetime] = None  # When it was resolved
    created_at: datetime
    updated_at: datetime


class AdminRequestResponse(BaseModel):
    requests: List[ResidentRequest]
    total_count: int


class SelectOptionRequest(BaseModel):
    """Request model for resident selecting an option"""
    request_id: str = Field(..., description="Request ID")
    selected_option_id: str = Field(..., description="Option ID chosen by user")


class ResolveRequestModel(BaseModel):
    """Request model for marking a request as resolved"""
    request_id: str = Field(..., description="Request ID to resolve")
    resolution_notes: Optional[str] = Field(None, description="Optional notes about resolution")
    resolved_by: str = Field(..., description="Who resolved it: 'admin' or 'resident'")


# ============================================================================
# GOVERNANCE MODELS (Ticket 15)
# ============================================================================

class GovernanceLog(BaseModel):
    """
    Governance log entry for AI decision tracking and audit trails.
    Mimics IBM Watsonx.governance functionality.
    """
    log_id: str = Field(..., description="Unique governance log identifier")
    request_id: str = Field(..., description="Associated request ID")
    resident_id: str = Field(..., description="Resident who made the request")
    
    # Decision Information
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chosen_action: str = Field(..., description="Action selected by decision agent")
    chosen_option_id: str = Field(..., description="Option ID selected")
    
    # Classification Context
    category: IssueCategory = Field(..., description="Issue category")
    urgency: Urgency = Field(..., description="Issue urgency level")
    intent: Intent = Field(..., description="Request intent")
    
    # Decision Reasoning (Explainability)
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    policy_scores: Dict[str, float] = Field(..., description="Policy scores for all options")
    alternatives_considered: List[str] = Field(..., description="Alternative options evaluated")
    
    # Risk & Simulation Context
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk forecast score")
    total_options_simulated: int = Field(..., description="Number of options simulated")
    
    # Cost & Time Analysis
    estimated_cost: float = Field(..., description="Estimated cost of chosen action")
    estimated_time: float = Field(..., description="Estimated time to resolution (hours)")
    exceeds_budget_threshold: bool = Field(False, description="Whether cost exceeded threshold")
    exceeds_time_threshold: bool = Field(False, description="Whether time exceeded threshold")
    
    # Escalation
    escalated: bool = Field(False, description="Whether decision resulted in human escalation")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation if applicable")
    
    # Metadata
    agent_version: str = Field(default="v1.0", description="Decision agent version")
    policy_weights: Dict[str, float] = Field(..., description="Policy weights used in decision")
    
    class Config:
        json_schema_extra = {
            "example": {
                "log_id": "GOV_20241109123456_ABC123",
                "request_id": "REQ_123456789ABC",
                "resident_id": "RES_1001",
                "decision_timestamp": "2024-11-09T12:34:56.789Z",
                "chosen_action": "Dispatch emergency plumber",
                "chosen_option_id": "opt_1",
                "category": "Maintenance",
                "urgency": "High",
                "intent": "solve_problem",
                "reasoning": "High urgency maintenance issue requires immediate response...",
                "policy_scores": {"opt_1": 0.85, "opt_2": 0.72, "opt_3": 0.60},
                "alternatives_considered": ["Send notification", "Schedule routine maintenance"],
                "risk_score": 0.75,
                "total_options_simulated": 3,
                "estimated_cost": 250.0,
                "estimated_time": 4.0,
                "escalated": False,
                "agent_version": "v1.0",
                "policy_weights": {"urgency": 0.4, "cost": 0.3, "time": 0.2, "satisfaction": 0.1}
            }
        }


class GovernanceQueryRequest(BaseModel):
    """Request model for querying governance logs."""
    request_id: Optional[str] = Field(None, description="Filter by specific request ID")
    resident_id: Optional[str] = Field(None, description="Filter by resident ID")
    category: Optional[IssueCategory] = Field(None, description="Filter by issue category")
    urgency: Optional[Urgency] = Field(None, description="Filter by urgency level")
    escalated_only: Optional[bool] = Field(False, description="Show only escalated decisions")
    start_date: Optional[datetime] = Field(None, description="Filter logs after this date")
    end_date: Optional[datetime] = Field(None, description="Filter logs before this date")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of logs to return")


class GovernanceQueryResponse(BaseModel):
    """Response model for governance log queries."""
    logs: List[GovernanceLog]
    total_count: int
    query_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filters_applied: Dict[str, Any]


class GovernanceStatsResponse(BaseModel):
    """Statistics about governance logs for analytics."""
    total_decisions: int
    total_escalations: int
    escalation_rate: float = Field(..., ge=0.0, le=1.0)
    average_cost: float
    average_time: float
    decisions_by_category: Dict[str, int]
    decisions_by_urgency: Dict[str, int]
    cost_threshold_violations: int
    time_threshold_violations: int

