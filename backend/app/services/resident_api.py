"""
Resident API
Provides endpoints for residents to view their request history.
"""
from fastapi import APIRouter
from typing import List
from app.models.schemas import ResidentRequest
from app.services.database import get_requests_by_resident

router = APIRouter()


@router.get("/get-requests/{resident_id}", response_model=List[ResidentRequest])
async def get_resident_requests(resident_id: str) -> List[ResidentRequest]:
    requests = get_requests_by_resident(resident_id)
    return requests

