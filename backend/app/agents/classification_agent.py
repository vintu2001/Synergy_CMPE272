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
    # TODO (Ticket 5): Implement LLM classification (OpenAI/HF), infer urgency, detect human_escalation intent
    
    # Placeholder implementation
    return ClassificationResponse(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.MEDIUM,
        intent=Intent.SOLVE_PROBLEM,
        confidence=0.85
    )

