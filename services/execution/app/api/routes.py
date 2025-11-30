"""
Execution API routes
Handles action execution and external system integrations.
"""
from fastapi import APIRouter
from app.models.schemas import ExecutionRequest, IssueCategory
from app.services.execution_layer import execute_decision

router = APIRouter()


@router.post("/execute")
async def execute_endpoint(request: ExecutionRequest):
    """
    Execute a decision based on the issue category.
    Includes resident preferences for technician scheduling.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        category = IssueCategory(request.category)
        
        # Log preferences for admin/technician visibility
        if request.resident_preferences:
            logger.info(f"Resident Preferences for {request.request_id}:")
            logger.info(f"  - Allow entry when absent: {request.resident_preferences.get('allow_entry_when_absent', False)}")
            logger.info(f"  - Preferred time slots: {request.resident_preferences.get('preferred_time_slots', 'Not specified')}")
            logger.info(f"  - Preferred days: {request.resident_preferences.get('preferred_days', 'Not specified')}")
            logger.info(f"  - Avoid days: {request.resident_preferences.get('avoid_days', 'Not specified')}")
            logger.info(f"  - Contact before arrival: {request.resident_preferences.get('contact_before_arrival', True)}")
            logger.info(f"  - Special instructions: {request.resident_preferences.get('special_instructions', 'None')}")
        
        # Log cost and time estimates for admin tracking
        if request.estimated_cost:
            logger.info(f"Estimated cost: ${request.estimated_cost}")
        if request.estimated_time:
            logger.info(f"Estimated completion time: {request.estimated_time} hours")
        
        # Create a DecisionResponse-like object
        from app.models.schemas import DecisionResponse
        decision = DecisionResponse(
            chosen_action=request.chosen_action,
            chosen_option_id=request.chosen_option_id,
            reasoning=request.reasoning,
            alternatives_considered=request.alternatives_considered
        )
        
        return await execute_decision(decision, category)
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Execution failed: {str(e)}"
        }
