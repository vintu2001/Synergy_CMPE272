"""
Structured output schemas for LLM responses using with_structured_output().

These Pydantic models enforce type safety and automatic validation
when using LangChain's with_structured_output() feature.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any


class SimulatedOptionStructured(BaseModel):
    """
    Structured schema for a single simulated option.
    Used with with_structured_output() for type-safe responses.
    """
    option_id: str = Field(..., description="Unique identifier for this option")
    action: str = Field(..., description="Description of the action to take")
    estimated_cost: float = Field(..., ge=0, description="Estimated cost in dollars")
    estimated_time: float = Field(..., ge=0, description="Estimated time to resolution in hours")
    reasoning: str = Field(..., description="Explanation for why this option was simulated")
    sources: List[str] = Field(
        default_factory=list,
        description="KB document IDs used to generate this option (RAG Phase 1)"
    )
    escalations: List[str] = Field(
        default_factory=list,
        description="Escalation conditions for this option"
    )
    
    @field_validator('estimated_cost', 'estimated_time')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure cost and time are non-negative."""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class SimulationOutputSchema(BaseModel):
    """
    Structured schema for simulation agent output.
    Contains a list of simulated resolution options.
    
    Allows 1 option for escalation-only responses (when no KB docs available),
    or 2-5 options for normal responses with KB context.
    """
    options: List[SimulatedOptionStructured] = Field(
        ...,
        min_length=1,
        description="List of simulated resolution options (minimum 1 for escalation, 2-5 for normal responses)"
    )
    
    @field_validator('options')
    @classmethod
    def validate_minimum_options(cls, v: List[SimulatedOptionStructured]) -> List[SimulatedOptionStructured]:
        """Ensure at least 1 option is provided (escalation) or 2-5 for normal responses."""
        if len(v) < 1:
            raise ValueError(f"At least 1 option required, got {len(v)}")
        return v


class PolicyWeightsStructured(BaseModel):
    """
    Structured schema for policy weights.
    All weights must be between 0-1 and sum to 1.0.
    """
    urgency_weight: float = Field(..., ge=0.0, le=1.0, description="Weight for urgency in decision scoring")
    cost_weight: float = Field(..., ge=0.0, le=1.0, description="Weight for cost in decision scoring")
    time_weight: float = Field(..., ge=0.0, le=1.0, description="Weight for resolution time in decision scoring")
    satisfaction_weight: float = Field(..., ge=0.0, le=1.0, description="Weight for resident satisfaction in decision scoring")
    
    @field_validator('urgency_weight', 'cost_weight', 'time_weight', 'satisfaction_weight')
    @classmethod
    def validate_weight_range(cls, v: float) -> float:
        """Ensure weights are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = self.urgency_weight + self.cost_weight + self.time_weight + self.satisfaction_weight
        if not (0.95 <= total <= 1.05):  # Allow small floating point tolerance
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")


class ThresholdCapsStructured(BaseModel):
    """
    Structured schema for cost and time thresholds/caps.
    """
    max_cost: float = Field(..., gt=0.0, description="Maximum allowable cost (dollars)")
    max_time: float = Field(..., gt=0.0, description="Maximum allowable time (hours)")


class EscalationRulesStructured(BaseModel):
    """
    Structured schema for escalation rules.
    """
    cost_threshold: float = Field(..., gt=0.0, description="Cost above which human approval needed")
    time_threshold: float = Field(..., gt=0.0, description="Time above which human approval needed")
    conditions: List[str] = Field(
        default_factory=list,
        description="Array of text conditions from policies that trigger escalation"
    )


class RulesOutputSchema(BaseModel):
    """
    Structured schema for rules extraction output.
    Contains weights, caps, escalation criteria, and source citations.
    """
    weights: PolicyWeightsStructured = Field(..., description="Decision-making weights")
    caps: ThresholdCapsStructured = Field(..., description="Maximum thresholds for filtering options")
    escalation: EscalationRulesStructured = Field(..., description="When to escalate to human")
    sources: List[str] = Field(..., min_length=1, description="Array of doc_ids from retrieved context (REQUIRED)")
    explicit_values: List[str] = Field(
        default_factory=list,
        description="Field names that were explicitly found in context"
    )
    inferred_values: List[str] = Field(
        default_factory=list,
        description="Field names that were inferred from general patterns"
    )
    
    @field_validator('sources')
    @classmethod
    def validate_sources_present(cls, v: List[str]) -> List[str]:
        """Ensure at least one source is cited."""
        if not v or len(v) == 0:
            raise ValueError("At least one source document ID must be cited")
        return v


class ComplexityAnalysisSchema(BaseModel):
    """
    Structured schema for complexity analysis output from reasoning engine.
    """
    complexity_level: str = Field(
        ...,
        description="Complexity level: 'simple', 'moderate', or 'complex'"
    )
    reasoning_required: bool = Field(..., description="Whether multi-step reasoning is needed")
    factors: List[str] = Field(..., description="Factors contributing to complexity assessment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in complexity assessment")
    
    @field_validator('complexity_level')
    @classmethod
    def validate_complexity_level(cls, v: str) -> str:
        """Ensure complexity level is valid."""
        valid_levels = {'simple', 'moderate', 'complex'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Complexity level must be one of {valid_levels}, got '{v}'")
        return v.lower()


class ReasoningChainSchema(BaseModel):
    """
    Structured schema for multi-step reasoning chain output.
    """
    steps: List[Dict[str, str]] = Field(
        ...,
        min_length=1,
        description="List of reasoning steps, each with 'step' and 'rationale'"
    )
    final_recommendation: str = Field(..., description="Final recommendation based on reasoning chain")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in reasoning")
    
    @field_validator('steps')
    @classmethod
    def validate_steps_format(cls, v: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Ensure each step has required fields."""
        for idx, step in enumerate(v):
            if 'step' not in step or 'rationale' not in step:
                raise ValueError(f"Step {idx+1} must have 'step' and 'rationale' fields")
        return v
