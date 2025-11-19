"""
Schemas for Decision & Simulation Service
"""
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


class ClassificationResponse(BaseModel):
    category: IssueCategory
    urgency: Urgency
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
    message_text: Optional[str] = None


class SimulatedOption(BaseModel):
    option_id: str
    action: str
    estimated_cost: float = Field(..., ge=0)
    estimated_time: float = Field(..., ge=0)
    reasoning: str
    source_doc_ids: Optional[List[str]] = None
    resident_satisfaction_impact: Optional[float] = Field(None, ge=0.0, le=1.0)
    steps: Optional[List[str]] = None
    model_config = {"exclude_none": False}


class SimulationResponse(BaseModel):
    options: List[SimulatedOption]
    issue_id: str
    is_recurring: bool = False


class PolicyWeights(BaseModel):
    urgency_weight: float = Field(0.3, ge=0.0, le=1.0)
    cost_weight: float = Field(0.20, ge=0.0, le=1.0)
    time_weight: float = Field(0.25, ge=0.0, le=1.0)
    satisfaction_weight: float = Field(0.15, ge=0.0, le=1.0)


class PolicyConfiguration(BaseModel):
    max_cost: float = Field(1000.0, gt=0.0)
    max_time: float = Field(72.0, gt=0.0)


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


class DecisionResponse(BaseModel):
    chosen_action: str
    chosen_option_id: str
    reasoning: str
    alternatives_considered: List[str]
    policy_scores: Optional[Dict[str, float]] = None
    escalation_reason: Optional[str] = None
    rule_sources: Optional[List[str]] = None
    rule_object: Optional[Dict[str, Any]] = None
    recommended_option_id: Optional[str] = None


class DecisionResponseWithStatus(BaseModel):
    decision: DecisionResponse
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


class DecisionRequest(BaseModel):
    classification: ClassificationResponse
    simulation: SimulationResponse
    weights: PolicyWeights = Field(default_factory=lambda: PolicyWeights())
    config: PolicyConfiguration = Field(default_factory=lambda: PolicyConfiguration())


class SimulationRequest(BaseModel):
    category: str
    urgency: str
    message_text: str
    resident_id: str
    risk_score: float = 0.5
    resident_history: Optional[List[Dict]] = None


class RetrievalContext(BaseModel):
    """
    Contains retrieved documents and metadata from RAG retrieval operation.
    Provides context for LLM prompts in simulation and decision agents.
    """
    query: str = Field(..., description="Original query text used for retrieval")
    retrieved_docs: List[Dict[str, Any]] = Field(..., description="List of retrieved documents with text, metadata, and scores")
    total_retrieved: int = Field(..., ge=0, description="Number of documents retrieved")
    retrieval_timestamp: datetime = Field(default_factory=datetime.now, description="When retrieval occurred")
    retrieval_method: str = Field(default="similarity_search", description="Method used (similarity_search, mmr, etc.)")
