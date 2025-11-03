"""
Message Intake Service - Ticket 4
Ingests raw messages, cleans them, and queues them for classification.

TODO (Ticket 4):
- Create SQS queue for incoming messages
- Configure AWS Lambda function to trigger on new messages
- Normalize text (lowercase, remove special characters)
- Pass processed message to Classification Agent
"""
from fastapi import APIRouter
from app.models.schemas import MessageRequest
import re

router = APIRouter()


def normalize_text(text: str) -> str:
    """
    Normalizes text for processing.
    
    Args:
        text: Raw message text
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    normalized = text.lower()
    
    # Remove excessive whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove special characters (keep letters, numbers, spaces, basic punctuation)
    normalized = re.sub(r'[^a-z0-9\s.,!?]', '', normalized)
    
    return normalized.strip()


@router.post("/submit-request")
async def submit_request(request: MessageRequest):
    """
    Receives a message from resident and queues it for processing.
    
    Args:
        request: MessageRequest with resident_id and message_text
        
    Returns:
        Confirmation with request_id
    """
    # TODO: Implement message intake
    # - Normalize the message text
    # - Put message in SQS queue
    # - Create initial entry in DynamoDB with status "Submitted"
    # - Return request_id to user
    
    normalized_text = normalize_text(request.message_text)
    
    # Placeholder: In real implementation, this would:
    # 1. Send to SQS queue
    # 2. Create DynamoDB entry
    # 3. Trigger Lambda function
    
    return {
        "status": "submitted",
        "message": "Request submitted successfully!",
        "request_id": "placeholder_request_id"
    }

