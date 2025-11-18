"""
Admin API endpoints
Provides admin dashboard functionality with API key authentication.
"""
from fastapi import APIRouter, Header, HTTPException, Body
from typing import Optional
from datetime import datetime, timezone
from app.models.schemas import AdminRequestResponse, UpdateStatusRequest, AddCommentRequest, Status
from app.services.database import get_all_requests, get_table, get_request_by_id
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'your_admin_api_key_here')


def verify_admin_key(x_api_key: Optional[str]):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )


@router.get("/admin/all-requests", response_model=AdminRequestResponse)
async def get_all_requests_admin(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    verify_admin_key(x_api_key)
    
    requests = get_all_requests()
    return AdminRequestResponse(
        requests=requests,
        total_count=len(requests)
    )


@router.post("/admin/update-status")
async def update_request_status(
    update_data: UpdateStatusRequest = Body(...),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    verify_admin_key(x_api_key)
    
    try:
        request = get_request_by_id(update_data.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        table = get_table()
        now = datetime.now(timezone.utc)
        
        table.update_item(
            Key={'request_id': update_data.request_id},
            UpdateExpression='SET #status = :status, updated_at = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': update_data.status.value,
                ':updated': now.isoformat()
            }
        )
        
        logger.info(f"Request {update_data.request_id} status updated to {update_data.status.value} by admin")
        
        return {
            "status": "success",
            "message": f"Request status updated to {update_data.status.value}",
            "request_id": update_data.request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating request status: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating request status: {str(e)}")


@router.post("/admin/add-comment")
async def add_comment(
    comment_data: AddCommentRequest = Body(...),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    verify_admin_key(x_api_key)
    
    try:
        request = get_request_by_id(comment_data.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        table = get_table()
        now = datetime.now(timezone.utc)
        
        # Get existing comments or initialize empty list
        existing_comments = request.get('admin_comments', [])
        if not isinstance(existing_comments, list):
            existing_comments = []
        
        # Add new comment
        new_comment = {
            'comment': comment_data.comment,
            'added_by': comment_data.added_by,
            'added_at': now.isoformat()
        }
        existing_comments.append(new_comment)
        
        table.update_item(
            Key={'request_id': comment_data.request_id},
            UpdateExpression='SET admin_comments = :comments, updated_at = :updated',
            ExpressionAttributeValues={
                ':comments': existing_comments,
                ':updated': now.isoformat()
            }
        )
        
        logger.info(f"Comment added to request {comment_data.request_id} by {comment_data.added_by}")
        
        return {
            "status": "success",
            "message": "Comment added successfully",
            "request_id": comment_data.request_id,
            "comment": new_comment
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")
