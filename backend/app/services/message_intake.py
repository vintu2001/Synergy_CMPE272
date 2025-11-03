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
    # TODO (Ticket 4): Keep minimal utility; normalize text before enqueueing
    normalized = text.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^a-z0-9\s.,!?]', '', normalized)
    
    return normalized.strip()


@router.post("/submit-request")
async def submit_request(request: MessageRequest):
    # TODO (Ticket 4): Normalize, send to SQS, create DynamoDB record (status=Submitted), return request_id
    
    normalized_text = normalize_text(request.message_text)
    
    return {
        "status": "submitted",
        "message": "Request submitted successfully!",
        "request_id": "placeholder_request_id"
    }

