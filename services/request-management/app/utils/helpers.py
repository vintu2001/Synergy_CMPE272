"""
Helper utilities
"""
from datetime import datetime
import random
import string


def generate_request_id() -> str:
    """Generate a unique request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"REQ_{timestamp}_{random_suffix}"

