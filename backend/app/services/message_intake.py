"""
Message Intake Service - Ticket 4
Ingests raw messages, cleans them, and queues them for classification.

TODO (Ticket 4):
- Create SQS queue for incoming messages
- Configure AWS Lambda function to trigger on new messages
- Normalize text (lowercase, remove special characters)
- Pass processed message to Classification Agent
"""
from fastapi import APIRouter, FastAPI
from app.models.schemas import MessageRequest
from dotenv import load_dotenv
import boto3
import json
import uuid
import re
import os

app = FastAPI()

# Load environment variables from .env
load_dotenv()


router = APIRouter()

# Read from .env
REGION = os.getenv("AWS_REGION")
SQS_URL = os.getenv("AWS_SQS_QUEUE_URL")
DYNAMO_TABLE = os.getenv("AWS_DYNAMODB_TABLE_NAME")

# AWS clients
sqs = boto3.client("sqs", region_name=REGION)


@router.post("/submit-request")
async def submit_request(request: MessageRequest):
    # Generate a unique request ID
    request_id = str(uuid.uuid4())

    # Send to SQS
    payload = {"request_id": request_id, "message_text": request.message_text}
    sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))

    return {
        "status": "submitted",
        "message": "Request submitted successfully!",
        "request_id": request_id,
    }
    
app.include_router(router)