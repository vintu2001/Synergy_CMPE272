"""
Decision Agent
Evaluates simulated options, checks for human escalation, and selects optimal action using a policy-based scoring system.
"""
from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.responses import JSONResponse
from app.models.schemas import (
    ClassificationResponse, SimulationResponse, DecisionResponse, Intent,
    PolicyWeights, DecisionReasoning, SimulatedOption, PolicyConfiguration,
    CostAnalysis, TimeAnalysis, DecisionRequest, DecisionResponseWithStatus
)
from app.rag.retriever import retrieve_decision_rules  # RAG integration
from datetime import datetime
import time
import logging
import os
from typing import List, Dict, Tuple, Optional
from statistics import mean

logger = logging.getLogger(__name__)

# Default configurations
DEFAULT_WEIGHTS = PolicyWeights()
DEFAULT_CONFIG = PolicyConfiguration()

router = APIRouter()


def create_escalation_decision(
    classification: ClassificationResponse,
    reason: str = "Resident explicitly requested human contact",
    rule_sources: Optional[List[str]] = None
) -> DecisionResponse:
    """Creates a decision response for human escalation cases."""
    return DecisionResponse(
        chosen_action="Escalate to On-Call Manager",
        chosen_option_id="escalation",
        reasoning=reason,
        alternatives_considered=[],
        escalation_reason=reason,
        policy_scores={"escalation": 1.0},
        rule_sources=rule_sources
    )


def analyze_costs(
    options: List[SimulatedOption],
    config: PolicyConfiguration
) -> List[CostAnalysis]:
    """Analyze costs for all options and generate cost analysis report."""
    # Calculate max actual cost for scaling
    max_actual_cost = max((opt.estimated_cost for opt in options), default=1.0)
    scaling_factor = config.max_cost / max_actual_cost if max_actual_cost > 0 else 1.0
    
    return [
        CostAnalysis(
            option_id=opt.option_id,
            estimated_cost=opt.estimated_cost,
            exceeds_scale=opt.estimated_cost > config.max_cost,
            scaled_cost=opt.estimated_cost * scaling_factor
        )
        for opt in options
    ]

def analyze_times(
    options: List[SimulatedOption],
    config: PolicyConfiguration
) -> List[TimeAnalysis]:
    """Analyze resolution times for all options and generate time analysis report."""
    # Calculate max actual time for scaling
    max_actual_time = max((opt.estimated_time for opt in options), default=1.0)
    scaling_factor = config.max_time / max_actual_time if max_actual_time > 0 else 1.0
    
    return [
        TimeAnalysis(
            option_id=opt.option_id,
            estimated_time=opt.estimated_time,
            exceeds_scale=opt.estimated_time > config.max_time,
            scaled_time=opt.estimated_time * scaling_factor
        )
        for opt in options
    ]

def calculate_raw_score(
    option: SimulatedOption,
    urgency: str,
    max_actual_cost : float,
    max_actual_time : float,
    weights: PolicyWeights = DEFAULT_WEIGHTS,
    config: PolicyConfiguration = DEFAULT_CONFIG
) -> float:
    """
    Calculate an unscaled weighted score for an option.
    """
    # Normalize metrics to 0-1 scale
    urgency_factor = {
        "High": 1.0,
        "Medium": 0.6,
        "Low": 0.3
    }.get(urgency, 0.5)
    
    # Calculate scaling factors and scaled values for both cost and time
    cost_scaling_factor = config.max_cost / max_actual_cost if max_actual_cost > 0 else 1.0
    scaled_cost = option.estimated_cost * cost_scaling_factor
    
    time_scaling_factor = config.max_time / max_actual_time if max_actual_time > 0 else 1.0
    scaled_time = option.estimated_time * time_scaling_factor
    
    # Calculate scores using scaled values
    cost_score = 1.0 - (scaled_cost / config.max_cost)
    time_score = 1.0 - (scaled_time / config.max_time)
    satisfaction_score = 0.7  # Default satisfaction score since field removed

    # Calculate raw weighted score without capping
    raw_score = (
        weights.urgency_weight * urgency_factor +
        weights.cost_weight * cost_score +
        weights.time_weight * time_score +
        weights.satisfaction_weight * satisfaction_score
    )
    
    return raw_score

def generate_factor_breakdown(
    option: SimulatedOption,
    urgency: str,
    max_actual_cost: float,
    max_actual_time: float,
    weights: PolicyWeights,
    config: PolicyConfiguration
) -> Dict[str, float]:
    """Generate a breakdown of how each factor contributed to the score."""
    # Calculate individual factor scores
    urgency_factor = {
        "High": 1.0,
        "Medium": 0.6,
        "Low": 0.3
    }.get(urgency, 0.5)
    
    cost_scaling_factor = config.max_cost / max_actual_cost if max_actual_cost > 0 else 1.0
    scaled_cost = option.estimated_cost * cost_scaling_factor
    cost_score = 1.0 - (scaled_cost / config.max_cost)
    
    time_scaling_factor = config.max_time / max_actual_time if max_actual_time > 0 else 1.0
    scaled_time = option.estimated_time * time_scaling_factor
    time_score = 1.0 - (scaled_time / config.max_time)
    
    return {
        "urgency_contribution": weights.urgency_weight * urgency_factor,
        "cost_contribution": weights.cost_weight * cost_score,
        "time_contribution": weights.time_weight * time_score,
        "satisfaction_contribution": weights.satisfaction_weight * 0.7  # Default satisfaction
    }

def generate_comparative_analysis(
    chosen_option: Tuple[SimulatedOption, float],
    scored_options: List[Tuple[SimulatedOption, float]],
    classification: ClassificationResponse
) -> List[str]:
    """Generate comparative analysis between chosen option and alternatives."""
    option, score = chosen_option
    comparative_insights = []
    
    # Sort options by score for ranking
    sorted_options = sorted(scored_options, key=lambda x: x[1], reverse=True)
    rank = next(i for i, (opt, _) in enumerate(sorted_options) if opt.option_id == option.option_id) + 1
    
    # Add ranking insight
    comparative_insights.append(
        f"Ranked #{rank} out of {len(scored_options)} options based on overall score"
    )
    
    # Compare with alternatives
    if len(scored_options) > 1:
        next_best = next((opt for opt, s in sorted_options if opt.option_id != option.option_id), None)
        if next_best:
            cost_diff = option.estimated_cost - next_best.estimated_cost
            time_diff = option.estimated_time - next_best.estimated_time
            
            if cost_diff < 0:
                comparative_insights.append(
                    f"Saves ${abs(cost_diff):.2f} compared to next best option"
                )
            elif cost_diff > 0:
                comparative_insights.append(
                    f"Costs ${cost_diff:.2f} more than next best option but offers better overall value"
                )
            
            if time_diff < 0:
                comparative_insights.append(
                    f"Faster resolution by {abs(time_diff):.1f}h compared to alternatives"
                )
    
    return comparative_insights

def generate_decision_reasoning(
    chosen_option: Tuple[SimulatedOption, float],
    scored_options: List[Tuple[SimulatedOption, float]],
    all_options: List[SimulatedOption],
    classification: ClassificationResponse,
    weights: PolicyWeights = DEFAULT_WEIGHTS,
    config: PolicyConfiguration = DEFAULT_CONFIG
) -> DecisionReasoning:
    """Generate comprehensive decision reasoning with detailed analysis."""
    option, score = chosen_option
    
    # Get factor breakdown
    max_actual_cost = max((opt.estimated_cost for opt in all_options), default=1.0)
    max_actual_time = max((opt.estimated_time for opt in all_options), default=1.0)
    factor_breakdown = generate_factor_breakdown(
        option, classification.urgency.value,
        max_actual_cost, max_actual_time,
        weights, config
    )
    
    # Generate comparative analysis
    comparative_insights = generate_comparative_analysis(
        chosen_option, scored_options, classification
    )
    
    # Analyze costs and times
    cost_analysis = analyze_costs(all_options, config)
    time_analysis = analyze_times(all_options, config)
    
    # Build detailed considerations
    considerations = []
    
    # Add factor breakdown
    considerations.append(f"Decision Factor Analysis for {option.action}:")
    for factor, contribution in factor_breakdown.items():
        considerations.append(f"- {factor.replace('_', ' ').title()}: {contribution:.2f}")
    
    # Add comparative insights
    considerations.extend([f"Comparative Analysis:", *[f"- {insight}" for insight in comparative_insights]])
    
    # Add alternative options with scores
    considerations.append("\nAlternative Options Considered:")
    for opt, alt_score in scored_options:
        if opt.option_id != option.option_id:
            considerations.append(
                f"- {opt.action} (score: {alt_score:.2f}, "
                f"cost: ${opt.estimated_cost:.2f}, "
                f"time: {opt.estimated_time:.1f}h)"
            )
    
    # Check thresholds
    exceeds_cost_threshold = any(analysis.exceeds_scale for analysis in cost_analysis)
    exceeds_time_threshold = any(analysis.exceeds_scale for analysis in time_analysis)
    
    # Add threshold warnings if applicable
    if exceeds_cost_threshold or exceeds_time_threshold:
        considerations.append("\nThreshold Warnings:")
        if exceeds_cost_threshold:
            considerations.append("- Some options exceed budget threshold")
        if exceeds_time_threshold:
            considerations.append("- Some options exceed time threshold")
    
    return DecisionReasoning(
        chosen_action=option.action,
        policy_scores={opt.option_id: score for opt, score in scored_options},
        considerations=considerations,
        escalation_reason=None,
        cost_analysis=cost_analysis,
        time_analysis=time_analysis,
        total_estimated_cost=option.estimated_cost,
        total_estimated_time=option.estimated_time,
        exceeds_budget_threshold=exceeds_cost_threshold,
        exceeds_time_threshold=exceeds_time_threshold
    )


@router.post(
    "/decide",
    response_model=DecisionResponseWithStatus,
    summary="Make a decision based on classification and simulated options",
    description="""
    Makes an intelligent decision based on:
    - Classification results (category, urgency, intent)
    - Simulated resolution options
    - Policy weights (optional)
    - Cost and time thresholds (optional)
    
    Returns a detailed decision with:
    - Chosen action and reasoning
    - Policy-based scoring
    - Cost and time analysis
    - Comparative insights
    """,
    responses={
        200: {
            "description": "Successful decision",
            "content": {
                "application/json": {
                    "example": {
                        "chosen_action": "Replace AC filter",
                        "chosen_option_id": "opt1",
                        "reasoning": "Selected based on optimal cost-effectiveness",
                        "alternatives_considered": ["Full maintenance", "Replace unit"],
                        "request_id": "dec_20251107120000",
                        "status": "success"
                    }
                }
            }
        },
        400: {"description": "Invalid input or no options provided"},
        500: {"description": "Internal server error during decision making"}
    }
)
async def make_decision(
    request: DecisionRequest = Body(
        ...,
        examples={
            "normal": {
                "summary": "Normal decision request",
                "value": {
                    "classification": {
                        "category": "Maintenance",
                        "urgency": "High",
                        "intent": "solve_problem"
                    },
                    "simulation": {
                        "options": [{
                            "option_id": "opt1",
                            "action": "Replace filter",
                            "estimated_cost": 100.0,
                            "estimated_time": 2.0,
                            "reasoning": "Standard HVAC filter replacement procedure"
                        }],
                        "issue_id": "test_issue"
                    }
                }
            }
        }
    )
) -> DecisionResponseWithStatus:
    """
    Make a decision based on classification results and simulated options.
    Uses policy-based scoring for option selection unless human escalation is needed.
    """
    start_time = time.time()
    
    try:
        # Retrieve decision rules from knowledge base
        rag_context = None
        rule_sources = []
        
        # Check if RAG is enabled
        rag_enabled = os.getenv('RAG_ENABLED', 'false').lower() == 'true'
        
        if rag_enabled:
            try:
                # Build query for policy rules
                query_parts = [
                    f"{request.classification.category.value}",
                    f"{request.classification.urgency.value} urgency",
                    "policy rules thresholds requirements"
                ]
                rule_query = " ".join(query_parts)
                
                # Retrieve policy documents for decision rules
                rag_context = await retrieve_decision_rules(
                    query=rule_query,
                    category=request.classification.category.value,
                    urgency=request.classification.urgency.value,
                    building_id=None,  # Extracted from options when available
                    top_k=3  # Fewer documents for decision agent (higher precision)
                )
                
                if rag_context and rag_context.retrieved_docs:
                    rule_sources = [doc['doc_id'] for doc in rag_context.retrieved_docs if 'doc_id' in doc]
                    logger.info(f"RAG retrieval successful: {len(rule_sources)} policy rules retrieved")
                    
                    # Log retrieved rules for audit trail
                    for doc in rag_context.retrieved_docs:
                        logger.debug(f"Retrieved rule: {doc.get('doc_id', 'N/A')} (score: {doc.get('score', 0):.3f})")
                else:
                    logger.info("RAG retrieval returned no rules")
                    
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}. Continuing with default policy scoring.")
                rag_context = None
                rule_sources = []
        else:
            logger.info("RAG is disabled (RAG_ENABLED=false)")
        
        # Check for human escalation intent
        if request.classification.intent == Intent.HUMAN_ESCALATION:
            response = create_escalation_decision(
                request.classification,
                rule_sources=rule_sources if rule_sources else None
            )
            return DecisionResponseWithStatus(
                decision=response,
                status="escalated",
                timestamp=datetime.now()
            )
        
        if not request.simulation.options:
            raise HTTPException(
                status_code=400,
                detail="No options provided in simulation"
            )
        
        max_actual_cost = max((opt.estimated_cost for opt in request.simulation.options), default=1.0)
        max_actual_time = max((opt.estimated_time for opt in request.simulation.options), default=1.0)

        all_raw_scores = [
            calculate_raw_score(
                opt,
                request.classification.urgency.value,
                max_actual_cost,
                max_actual_time,
                request.weights,
                request.config
            )
            for opt in request.simulation.options
        ]
        max_raw_score = max(all_raw_scores) if all_raw_scores else 1.0

        # Score all options
        scored_options = [
            (opt, calculate_raw_score(
                opt, 
                request.classification.urgency.value,
                max_actual_cost,
                max_actual_time,
                request.weights,
                request.config
            )/max_raw_score) 
            for opt in request.simulation.options
        ]
        
        # Select best option
        best_option = max(scored_options, key=lambda x: x[1])
        option, score = best_option
        
        # Generate enhanced reasoning
        reasoning = generate_decision_reasoning(
            best_option,
            scored_options,
            request.simulation.options,
            request.classification,
            request.weights,
            request.config
        )
        
        # Create a comprehensive response reasoning
        response_parts = [
            f"Selected {option.action} (score: {score:.2f})",
            f"Cost: ${option.estimated_cost:.2f}",
            f"Estimated time: {option.estimated_time:.1f}h"
        ]
        
        # Add urgency context
        if request.classification.urgency.value == "High":
            response_parts.append("Prioritized due to high urgency")
        
        # Add cost-effectiveness insight
        cost_rank = sorted(request.simulation.options, key=lambda x: x.estimated_cost).index(option)
        if cost_rank == 0:
            response_parts.append("Most cost-effective option")
        elif score > 0.8:
            response_parts.append("Optimal balance of cost and effectiveness")
        
        # Add threshold warnings if needed
        warnings = []
        if reasoning.exceeds_budget_threshold:
            warnings.append("Some options exceed budget threshold")
        if reasoning.exceeds_time_threshold:
            warnings.append("Some options exceed time threshold")
        
        if warnings:
            response_parts.append(f"Warning: {' and '.join(warnings)}")
        
        # Add RAG context if rules were used
        if rule_sources:
            response_parts.append(f"Based on {len(rule_sources)} policy rule(s)")
        
        response_reasoning = ". ".join(response_parts)
        
        decision_response = DecisionResponse(
            chosen_action=option.action,
            chosen_option_id=option.option_id,
            reasoning=response_reasoning,
            alternatives_considered=reasoning.considerations,
            policy_scores=reasoning.policy_scores,
            escalation_reason=None,
            rule_sources=rule_sources if rule_sources else None,  # Include RAG sources
            rule_object=None
        )
        
        return DecisionResponseWithStatus(
            decision=decision_response,
            status="decided",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in decision making: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error making decision: {str(e)}"
        )

