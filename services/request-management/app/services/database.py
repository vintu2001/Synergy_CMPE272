"""
Database Service - DynamoDB Integration
Provides CRUD operations for resident requests stored in DynamoDB.
"""
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from app.models.schemas import ResidentRequest, Status
import os
import logging

logger = logging.getLogger(__name__)

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-west-2')
)

TABLE_NAME = os.getenv('AWS_DYNAMODB_TABLE_NAME', 'aam_requests')


def get_table():
    return dynamodb.Table(TABLE_NAME)


def convert_floats_to_decimal(obj: Any) -> Any:
    """Recursively convert float values to Decimal and enums to strings for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif hasattr(obj, 'value'):  # Handle Enum types
        return obj.value
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj


def create_request(request: ResidentRequest) -> bool:
    try:
        table = get_table()
        item = request.dict()
        item = convert_floats_to_decimal(item)
        if 'created_at' in item and isinstance(item['created_at'], datetime):
            item['created_at'] = item['created_at'].isoformat()
        if 'updated_at' in item and isinstance(item['updated_at'], datetime):
            item['updated_at'] = item['updated_at'].isoformat()
        if 'resolved_at' in item and isinstance(item['resolved_at'], datetime):
            item['resolved_at'] = item['resolved_at'].isoformat()
        table.put_item(Item=item)
        return True
    except ClientError as e:
        logger.error(f"Error creating request: {e}")
        return False


def get_request(request_id: str) -> Optional[ResidentRequest]:
    try:
        table = get_table()
        response = table.get_item(Key={'request_id': request_id})
        if 'Item' in response:
            return ResidentRequest(**response['Item'])
        return None
    except ClientError as e:
        logger.error(f"Error getting request: {e}")
        return None


def get_request_by_id(request_id: str) -> Optional[Dict]:
    """Get request as dict (for more flexible access without schema validation)"""
    try:
        table = get_table()
        response = table.get_item(Key={'request_id': request_id})
        if 'Item' in response:
            return response['Item']
        return None
    except ClientError as e:
        logger.error(f"Error getting request by ID: {e}")
        return None


def get_requests_by_resident(resident_id: str) -> List[ResidentRequest]:
    try:
        table = get_table()
        response = table.scan(
            FilterExpression=Key('resident_id').eq(resident_id)
        )
        return [ResidentRequest(**item) for item in response.get('Items', [])]
    except ClientError as e:
        logger.error(f"Error getting requests: {e}")
        return []


def get_all_requests() -> List[ResidentRequest]:
    try:
        table = get_table()
        response = table.scan()
        return [ResidentRequest(**item) for item in response.get('Items', [])]
    except ClientError as e:
        logger.error(f"Error getting all requests: {e}")
        return []


async def update_request_status(request_id: str, status: Status) -> bool:
    try:
        table = get_table()
        table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status.value,
                ':updated_at': datetime.now(timezone.utc).isoformat()
            }
        )
        return True
    except ClientError as e:
        logger.error(f"Error updating request: {e}")
        return False

