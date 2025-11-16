"""
Resident API endpoints
Provides endpoints for residents to view their request history and classify messages.
"""
from fastapi import APIRouter, HTTPException
from typing import List
import httpx
import os
import logging
from app.models.schemas import ResidentRequest, MessageRequest, ClassificationResponse
from app.services.database import get_requests_by_resident

logger = logging.getLogger(__name__)
router = APIRouter()

# Service URLs
AI_PROCESSING_URL = os.getenv("AI_PROCESSING_SERVICE_URL", "http://localhost:8002")


@router.get("/get-requests/{resident_id}", response_model=List[ResidentRequest])
async def get_resident_requests(resident_id: str) -> List[ResidentRequest]:
    requests = get_requests_by_resident(resident_id)
    return requests


@router.post("/classify", response_model=ClassificationResponse)
async def classify_message(request: MessageRequest) -> ClassificationResponse:
    """
    Proxy endpoint to classify a message using the AI Processing Service.
    This allows the frontend to call the Request Management Service for all operations.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_PROCESSING_URL}/api/v1/classify",
                json={
                    "resident_id": request.resident_id,
                    "message_text": request.message_text
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Classification service error: {e}")
        raise HTTPException(status_code=503, detail="Classification service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in classify proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Error classifying message: {str(e)}")
