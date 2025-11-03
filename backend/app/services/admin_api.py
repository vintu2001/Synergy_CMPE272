"""
Admin API - Ticket 19
API endpoint for admin dashboard to view all requests.

TODO (Ticket 19):
- Create GET /admin/all-requests endpoint
- Require API key authentication in header
- Query DynamoDB for all requests
- Return JSON array of all items
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
    """
    Get all requests for admin dashboard.
    Requires API key authentication.
    
    Args:
        x_api_key: API key in header (X-API-Key)
        
    Returns:
        AdminRequestResponse with all requests
        
    Raises:
        HTTPException: If API key is invalid
    """
    # Simple API key authentication
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

