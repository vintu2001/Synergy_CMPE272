"""
Helper utility functions
"""
import uuid
from datetime import datetime


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return f"REQ_{uuid.uuid4().hex[:12].upper()}"


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()

