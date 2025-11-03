"""
Decision Agent - Ticket 13
Evaluates simulated options, checks for human escalation, and selects optimal action.

TODO (Ticket 13):
- Check if intent == "human_escalation" -> bypass simulation and call alert API
- If not escalation, ingest simulated options from Simulation Agent
- Apply policy-based scoring function (weight urgency highest, then cost)
- Select option with highest score
- Log chosen action and pass to execution layer
"""
from fastapi import APIRouter
from app.models.schemas import ClassificationResponse, SimulationResponse, DecisionResponse, Intent

router = APIRouter()


@router.post("/decide", response_model=DecisionResponse)
async def make_decision(
    classification: ClassificationResponse,
    simulation: SimulationResponse
) -> DecisionResponse:
    """
    Makes the optimal decision based on classification and simulation results.
    
    Args:
        classification: ClassificationResponse with intent and urgency
        simulation: SimulationResponse with available options
        
    Returns:
        DecisionResponse with chosen action and reasoning
    """
    # TODO: Implement decision logic
    # - If intent == Intent.HUMAN_ESCALATION:
    #     -> Call /alert-on-call-manager endpoint
    #     -> Return escalation decision
    # - Else:
    #     -> Apply scoring function (urgency weight highest, then cost, satisfaction)
    #     -> Select best option
    #     -> Log decision reasoning
    
    # Placeholder implementation
    if classification.intent == Intent.HUMAN_ESCALATION:
        return DecisionResponse(
            chosen_action="Escalate to On-Call Manager",
            chosen_option_id="escalation",
            reasoning="Resident explicitly requested human contact",
            alternatives_considered=[]
        )
    
    # Simple scoring: prioritize urgency, then satisfaction, then lower cost
    best_option = max(
        simulation.options,
        key=lambda opt: (
            3.0 if classification.urgency.value == "High" else 1.0,  # Urgency weight
            opt.resident_satisfaction_impact,
            -opt.estimated_cost  # Negative for lower cost = higher score
        )
    )
    
    return DecisionResponse(
        chosen_action=best_option.action,
        chosen_option_id=best_option.option_id,
        reasoning=f"Selected based on urgency ({classification.urgency.value}), cost efficiency, and satisfaction impact",
        alternatives_considered=[opt.action for opt in simulation.options if opt != best_option]
    )

