"""
Schemas for Execution Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class IssueCategory(str, Enum):
    MAINTENANCE = "Maintenance"
    BILLING = "Billing"
    SECURITY = "Security"
    DELIVERIES = "Deliveries"
    AMENITIES = "Amenities"


class HealthCheck(BaseModel):
    status: str
    service: str


class DecisionResponse(BaseModel):
    chosen_action: str
    chosen_option_id: str
    reasoning: str
    alternatives_considered: List[str]
    policy_scores: Optional[Dict[str, float]] = None
    escalation_reason: Optional[str] = None
    rule_sources: Optional[List[str]] = None
    rule_object: Optional[Dict[str, Any]] = None


class ExecutionRequest(BaseModel):
    chosen_action: str
    chosen_option_id: str
    reasoning: str
    alternatives_considered: List[str]
    category: str
