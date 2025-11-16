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
    """
    try:
        category = IssueCategory(request.category)
        
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
        return {
            "status": "error",
            "message": f"Execution failed: {str(e)}"
        }
