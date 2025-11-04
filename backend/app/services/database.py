"""
Database Service - DynamoDB Integration
Provides CRUD operations for resident requests stored in DynamoDB.
"""
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional, List
from datetime import datetime, timezone
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


def create_request(request: ResidentRequest) -> bool:
    try:
        table = get_table()
        table.put_item(Item=request.dict())
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


def update_request_status(request_id: str, status: Status) -> bool:
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

