"""
Admin API endpoints
Provides admin dashboard functionality with API key authentication.
"""
from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from app.models.schemas import AdminRequestResponse
from app.services.database import get_all_requests
import os

router = APIRouter()

ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'default-admin-key-change-in-production')


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
