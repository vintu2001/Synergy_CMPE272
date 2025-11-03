"""
Classification Agent - Ticket 5
Categorizes messages, detects urgency, and identifies resident intent.

TODO (Ticket 5):
- Implement LLM-based classification using OpenAI API or Hugging Face
- Create /classify endpoint
- Handle emergency detection (e.g., "water leak" -> High urgency)
- Detect human escalation intent (e.g., "I need to speak to a manager")
"""
from fastapi import APIRouter
from app.models.schemas import MessageRequest, ClassificationResponse, IssueCategory, Urgency, Intent

router = APIRouter()


@router.post("/classify", response_model=ClassificationResponse)
async def classify_message(request: MessageRequest) -> ClassificationResponse:
    """
    Classifies a resident message into category, urgency, and intent.
    
    Args:
        request: MessageRequest containing resident_id and message_text
        
    Returns:
        ClassificationResponse with category, urgency, intent, and confidence
    """
    # TODO: Implement LLM-based classification
    # - Use OpenAI API or Hugging Face for classification
    # - Detect urgency based on keywords and context
    # - Identify intent (solve_problem vs human_escalation)
    
    # Placeholder implementation
    return ClassificationResponse(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.MEDIUM,
        intent=Intent.SOLVE_PROBLEM,
        confidence=0.85
    )

