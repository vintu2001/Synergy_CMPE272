"""
Admin API
Provides admin dashboard functionality with API key authentication.
"""
from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from app.models.schemas import AdminRequestResponse
from app.services.database import get_all_requests

from app.config import get_settings

router = APIRouter()

# Get ADMIN_API_KEY from centralized settings
settings = get_settings()
ADMIN_API_KEY = settings.ADMIN_API_KEY


@router.get("/admin/all-requests", response_model=AdminRequestResponse)
async def get_all_requests_admin(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    
    requests = get_all_requests()
    return AdminRequestResponse(
        requests=requests,
        total_count=len(requests)
    )

