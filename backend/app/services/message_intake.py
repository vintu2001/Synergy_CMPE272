"""
Message Intake Service - Ticket 4
Ingests raw messages, cleans them, and queues them for classification.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import MessageRequest, Status, ResidentRequest
from app.services.database import create_request
from app.agents.classification_agent import classify_message as classify_message_endpoint
from app.utils.helpers import generate_request_id
from datetime import datetime, timezone
import re
import os
import json
import boto3

router = APIRouter()

# Environment
REGION = os.getenv("AWS_REGION")
SQS_URL = os.getenv("AWS_SQS_QUEUE_URL")
sqs = boto3.client("sqs", region_name=REGION) if SQS_URL else None


def normalize_text(text: str) -> str:
    """Normalize text before processing."""
    normalized = text.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^a-z0-9\s.,!?]', '', normalized)
    return normalized.strip()


@router.post("/submit-request")
async def submit_request(request: MessageRequest):
    """
    Submit a resident request:
    - Normalize message text
    - Classify using classification agent
    - Create DynamoDB record with status=Submitted
    - Enqueue to SQS if configured
    - Return request_id
    """
    try:
        # Normalize text (kept for future processing hooks)
        _normalized_text = normalize_text(request.message_text)
        
        # Classify the message (only if no overrides provided)
        classification = await classify_message_endpoint(request)
        
        # Use user overrides if provided, otherwise use AI classification
        final_category = request.category if request.category else classification.category
        final_urgency = request.urgency if request.urgency else classification.urgency
        
        # Generate request ID
        request_id = generate_request_id()
        now = datetime.now(timezone.utc)
        
        # Create ResidentRequest object
        resident_request = ResidentRequest(
            request_id=request_id,
            resident_id=request.resident_id,
            message_text=request.message_text,
            category=final_category,
            urgency=final_urgency,
            intent=classification.intent,  # Intent is always from AI
            status=Status.SUBMITTED,
            classification_confidence=classification.confidence,
            created_at=now,
            updated_at=now
        )
        
        # Save to DynamoDB
        success = create_request(resident_request)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save request to database")
        
        # Enqueue event to SQS (optional)
        if sqs and SQS_URL:
            payload = {
                "request_id": request_id,
                "resident_id": request.resident_id,
                "message_text": request.message_text,
                "category": final_category.value,
                "urgency": final_urgency.value,
                "intent": classification.intent.value,
                "submitted_at": now.isoformat(),
            }
            sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
        
        return {
            "status": "submitted",
            "message": "Request submitted successfully!",
            "request_id": request_id,
            "classification": {
                "category": final_category.value,
                "urgency": final_urgency.value,
                "intent": classification.intent.value,
                "confidence": classification.confidence
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
