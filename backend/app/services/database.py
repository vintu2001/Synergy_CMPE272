"""
Database Service - DynamoDB Integration
Provides CRUD operations for resident requests stored in DynamoDB.
"""
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
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
        print(f"\n🔵 CREATE_REQUEST CALLED 🔵")
        print(f"Resident ID: {request.resident_id}")
        print(f"Category: {request.category}")
        print(f"Message: {request.message_text[:50]}...")
        
        table = get_table()
        # Convert the request to dict and convert floats to Decimal
        item = request.dict()
        print(f"Item keys: {list(item.keys())}")
        logger.info(f"Creating request with keys: {list(item.keys())}")
        logger.info(f"Request data: resident_id={item.get('resident_id')}, category={item.get('category')}")
        
        item = convert_floats_to_decimal(item)
        # Convert datetime objects to ISO format strings
        if 'created_at' in item and isinstance(item['created_at'], datetime):
            item['created_at'] = item['created_at'].isoformat()
        if 'updated_at' in item and isinstance(item['updated_at'], datetime):
            item['updated_at'] = item['updated_at'].isoformat()
        
        print(f"Storing to table: {TABLE_NAME}")
        logger.info(f"Storing item to DynamoDB table: {TABLE_NAME}")
        table.put_item(Item=item)
        print(f"✅ SUCCESS - Stored {item.get('request_id')} to DynamoDB\n")
        logger.info(f"✓ Successfully stored request {item.get('request_id')} to DynamoDB")
        return True
    except ClientError as e:
        print(f"❌ DYNAMODB ERROR: {e}")
        print(f"Error response: {e.response}")
        logger.error(f"✗ ClientError creating request: {e}")
        logger.error(f"Error details: {e.response}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        logger.error(f"✗ Unexpected error creating request: {e}")
        import traceback
        traceback.print_exc()
        logger.error(traceback.format_exc())
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


def find_recurring_issues(category: str, days: int = 7, min_count: int = 2) -> Dict[str, Any]:
    """Find recurring issues by category in the last N days"""
    try:
        table = get_table()
        response = table.scan()
        items = response.get('Items', [])
        
        # Filter by category and date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        similar_requests = []
        
        for item in items:
            if item.get('category') == category:
                created_at = item.get('created_at')
                if created_at:
                    # Parse ISO format datetime
                    request_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if request_date >= cutoff_date:
                        similar_requests.append(item)
        
        return {
            'category': category,
            'count': len(similar_requests),
            'is_recurring': len(similar_requests) >= min_count,
            'requests': similar_requests,
            'time_period_days': days
        }
    except ClientError as e:
        logger.error(f"Error finding recurring issues: {e}")
        return {'category': category, 'count': 0, 'is_recurring': False, 'requests': []}


def check_resident_repeat_issues(resident_id: str, category: str, days: int = 30) -> Dict[str, Any]:
    """Check if a specific resident has repeated issues in the same category"""
    try:
        table = get_table()
        response = table.scan()
        items = response.get('Items', [])
        
        # Convert category to string if it's an enum
        category_str = category.value if hasattr(category, 'value') else str(category)
        
        logger.info(f"Checking repeat issues for resident {resident_id}, category {category_str}")
        logger.info(f"Total items in DB: {len(items)}")
        
        # Filter by resident_id, category, and date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        resident_issues = []
        
        for item in items:
            item_category = item.get('category')
            item_resident = item.get('resident_id')
            
            # Handle category comparison (could be string or enum value)
            if hasattr(item_category, 'value'):
                item_category = item_category.value
            item_category = str(item_category) if item_category else None
            
            logger.debug(f"Comparing: item resident={item_resident} vs {resident_id}, item category={item_category} vs {category_str}")
            
            if item_resident == resident_id and item_category == category_str:
                logger.info(f"Found matching request: {item.get('request_id')}")
                created_at = item.get('created_at')
                if created_at:
                    try:
                        # Parse ISO format datetime
                        request_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if request_date >= cutoff_date:
                            resident_issues.append({
                                'request_id': item.get('request_id'),
                                'message_text': item.get('message_text'),
                                'created_at': created_at,
                                'status': item.get('status')
                            })
                    except (ValueError, AttributeError) as e:
                        logger.error(f"Date parsing error: {e}")
                        continue
        
        is_repeat = len(resident_issues) >= 2  # 2 or more = repeat issue
        logger.info(f"Found {len(resident_issues)} previous issues, is_repeat: {is_repeat}")
        
        return {
            'resident_id': resident_id,
            'category': category_str,
            'repeat_count': len(resident_issues),
            'is_repeat_issue': is_repeat,
            'previous_requests': resident_issues,
            'time_period_days': days,
            'recommendation': 'escalate_to_permanent_solution' if is_repeat else 'standard_process'
        }
    except ClientError as e:
        logger.error(f"Error checking resident repeat issues: {e}")
        return {
            'resident_id': resident_id,
            'category': category_str if 'category_str' in locals() else str(category),
            'repeat_count': 0,
            'is_repeat_issue': False,
            'previous_requests': [],
            'recommendation': 'standard_process'
        }


def get_dashboard_metrics() -> Dict[str, Any]:
    """Get metrics for admin dashboard"""
    try:
        table = get_table()
        response = table.scan()
        items = response.get('Items', [])
        
        # Calculate metrics
        total = len(items)
        by_category = {}
        by_urgency = {}
        by_status = {}
        urgent_count = 0
        
        for item in items:
            category = item.get('category', 'Unknown')
            urgency = item.get('urgency', 'Unknown')
            status = item.get('status', 'Unknown')
            
            by_category[category] = by_category.get(category, 0) + 1
            by_urgency[urgency] = by_urgency.get(urgency, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            
            if urgency == 'High':
                urgent_count += 1
        
        return {
            'total_requests': total,
            'urgent_count': urgent_count,
            'by_category': by_category,
            'by_urgency': by_urgency,
            'by_status': by_status
        }
    except ClientError as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {'total_requests': 0, 'urgent_count': 0, 'by_category': {}, 'by_urgency': {}, 'by_status': {}}

