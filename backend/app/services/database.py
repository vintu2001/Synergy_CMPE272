"""
Database Service - Ticket 6
DynamoDB integration for storing and retrieving requests.

TODO (Ticket 6):
- Create DynamoDB table with primary key (request_id)
- Store: original message, classification, urgency, intent, risk score, status
- Implement CRUD operations for requests
"""
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional, List
from datetime import datetime
from app.models.schemas import ResidentRequest, Status
import os

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-west-2')
)

TABLE_NAME = os.getenv('AWS_DYNAMODB_TABLE_NAME', 'aam_requests')


def get_table():
    """Get DynamoDB table instance"""
    return dynamodb.Table(TABLE_NAME)


def create_request(request: ResidentRequest) -> bool:
    """
    Create a new request in DynamoDB.
    
    Args:
        request: ResidentRequest object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table = get_table()
        table.put_item(Item=request.dict())
        return True
    except ClientError as e:
        print(f"Error creating request: {e}")
        return False


def get_request(request_id: str) -> Optional[ResidentRequest]:
    """
    Get a request by ID.
    
    Args:
        request_id: Request identifier
        
    Returns:
        ResidentRequest if found, None otherwise
    """
    try:
        table = get_table()
        response = table.get_item(Key={'request_id': request_id})
        if 'Item' in response:
            return ResidentRequest(**response['Item'])
        return None
    except ClientError as e:
        print(f"Error getting request: {e}")
        return None


def get_requests_by_resident(resident_id: str) -> List[ResidentRequest]:
    """
    Get all requests for a resident.
    
    Args:
        resident_id: Resident identifier
        
    Returns:
        List of ResidentRequest objects
    """
    try:
        table = get_table()
        response = table.scan(
            FilterExpression=Key('resident_id').eq(resident_id)
        )
        return [ResidentRequest(**item) for item in response.get('Items', [])]
    except ClientError as e:
        print(f"Error getting requests: {e}")
        return []


def get_all_requests() -> List[ResidentRequest]:
    """
    Get all requests (for admin dashboard).
    
    Returns:
        List of all ResidentRequest objects
    """
    try:
        table = get_table()
        response = table.scan()
        return [ResidentRequest(**item) for item in response.get('Items', [])]
    except ClientError as e:
        print(f"Error getting all requests: {e}")
        return []


def update_request_status(request_id: str, status: Status) -> bool:
    """
    Update request status.
    
    Args:
        request_id: Request identifier
        status: New status
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table = get_table()
        table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status.value,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        return True
    except ClientError as e:
        print(f"Error updating request: {e}")
        return False

