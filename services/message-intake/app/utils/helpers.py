import uuid
from datetime import datetime, timezone


def generate_request_id() -> str:
    return f"REQ_{uuid.uuid4().hex[:12].upper()}"


def get_current_timestamp() -> datetime:
    return datetime.now(timezone.utc)

