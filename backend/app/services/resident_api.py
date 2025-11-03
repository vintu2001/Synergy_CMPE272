"""
Resident API - Ticket 16
API endpoints for residents to submit and view their requests.

TODO (Ticket 16):
- GET /get-requests/{resident_id} - Query DynamoDB for resident's requests
- Integrate with message intake service
- Return list of requests for frontend dashboard
"""
from fastapi import APIRouter
from typing import List
from app.models.schemas import ResidentRequest
from app.services.database import get_requests_by_resident

router = APIRouter()


@router.get("/get-requests/{resident_id}", response_model=List[ResidentRequest])
async def get_resident_requests(resident_id: str) -> List[ResidentRequest]:
    """
    Get all requests for a specific resident.
    
    Args:
        resident_id: Resident identifier
        
    Returns:
        List of ResidentRequest objects
    """
    requests = get_requests_by_resident(resident_id)
    return requests

