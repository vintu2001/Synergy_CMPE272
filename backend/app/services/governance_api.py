"""
Governance API - Ticket 15
RESTful endpoints for governance log queries and analytics.
"""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import PlainTextResponse
from app.models.schemas import (
    GovernanceQueryRequest, GovernanceQueryResponse,
    GovernanceStatsResponse
)
from app.services.governance import (
    query_governance_logs, get_governance_stats, export_governance_logs
)
import logging

from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Get ADMIN_API_KEY from centralized settings
settings = get_settings()
ADMIN_API_KEY = settings.ADMIN_API_KEY


def verify_admin_key(x_api_key: str = Header(...)):
    """Verify admin API key for governance access."""
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.post("/governance/query", response_model=GovernanceQueryResponse)
async def query_logs(
    query: GovernanceQueryRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """
    Query governance logs with filters.
    
    Requires admin API key authentication.
    
    **Filter Options:**
    - request_id: Filter by specific request ID
    - resident_id: Filter by resident ID
    - category: Filter by issue category
    - urgency: Filter by urgency level
    - escalated_only: Show only escalated decisions
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    - limit: Maximum number of logs to return (1-1000)
    
    **Example Request:**
    ```json
    {
      "resident_id": "RES_1001",
      "category": "Maintenance",
      "escalated_only": false,
      "limit": 50
    }
    ```
    """
    verify_admin_key(x_api_key)
    
    try:
        result = await query_governance_logs(query)
        return result
    except Exception as e:
        logger.error(f"Error querying governance logs: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/governance/stats", response_model=GovernanceStatsResponse)
async def get_stats(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Get aggregate statistics about governance logs.
    
    Requires admin API key authentication.
    
    **Returns:**
    - Total decisions made
    - Total escalations
    - Escalation rate
    - Average cost and time
    - Decisions by category and urgency
    - Threshold violations
    """
    verify_admin_key(x_api_key)
    
    try:
        result = await get_governance_stats()
        return result
    except Exception as e:
        logger.error(f"Error getting governance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats calculation failed: {str(e)}")


@router.get("/governance/export")
async def export_logs(
    format: str = "json",
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """
    Export all governance logs for compliance/audit purposes.
    
    Requires admin API key authentication.
    
    **Query Parameters:**
    - format: Export format ("json" or "csv")
    
    **Returns:**
    - JSON or CSV formatted data
    """
    verify_admin_key(x_api_key)
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    try:
        data = await export_governance_logs(format)
        
        if format == "csv":
            return PlainTextResponse(
                content=data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=governance_logs.csv"}
            )
        else:
            return PlainTextResponse(
                content=data,
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=governance_logs.json"}
            )
    except Exception as e:
        logger.error(f"Error exporting governance logs: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/governance/health")
async def governance_health():
    """
    Health check endpoint for governance service.
    
    No authentication required.
    """
    return {
        "status": "healthy",
        "service": "governance_logger",
        "version": "v1.0",
        "description": "Custom AI Governance Logger (Watsonx.governance Alternative)"
    }

