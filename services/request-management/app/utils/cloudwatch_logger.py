"""
CloudWatch Logger for Request Management Service
Sends structured logs to AWS CloudWatch Logs
"""
import boto3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
LOG_GROUP = os.getenv('AWS_CLOUDWATCH_LOG_GROUP', '/aws/apartment-manager/application')
LOG_STREAM = os.getenv('AWS_CLOUDWATCH_LOG_STREAM', 'request-management')

try:
    cloudwatch_logs = boto3.client('logs', region_name=AWS_REGION)
    CLOUDWATCH_ENABLED = True
    logger.info("CloudWatch Logs client initialized for Request Management")
except Exception as e:
    logger.warning(f"CloudWatch Logs not available: {e}")
    CLOUDWATCH_ENABLED = False
    cloudwatch_logs = None

sequence_token = None


def ensure_log_stream():
    """Create log group and stream if they don't exist"""
    if not CLOUDWATCH_ENABLED:
        return False
    
    try:
        try:
            cloudwatch_logs.create_log_group(logGroupName=LOG_GROUP)
            logger.info(f"Created log group: {LOG_GROUP}")
        except cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
            pass
        
        try:
            cloudwatch_logs.create_log_stream(
                logGroupName=LOG_GROUP,
                logStreamName=LOG_STREAM
            )
            logger.info(f"Created log stream: {LOG_STREAM}")
        except cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
            pass
        
        return True
    except Exception as e:
        logger.error(f"Failed to ensure log stream: {e}")
        return False


def convert_decimal(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    return obj


def log_to_cloudwatch(event_type: str, data: Dict[str, Any]):
    """Send structured log to CloudWatch"""
    global sequence_token
    
    if not CLOUDWATCH_ENABLED:
        logger.debug(f"CloudWatch disabled - would log: {event_type}")
        return
    
    try:
        # Convert any Decimal objects to float
        clean_data = convert_decimal(data)
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'request-management',
            'event_type': event_type,
            **clean_data
        }
        
        log_event = {
            'logGroupName': LOG_GROUP,
            'logStreamName': LOG_STREAM,
            'logEvents': [{
                'timestamp': int(datetime.now().timestamp() * 1000),
                'message': json.dumps(log_entry)
            }]
        }
        
        if sequence_token:
            log_event['sequenceToken'] = sequence_token
        
        response = cloudwatch_logs.put_log_events(**log_event)
        sequence_token = response.get('nextSequenceToken')
        
    except cloudwatch_logs.exceptions.ResourceNotFoundException:
        if ensure_log_stream():
            sequence_token = None
            log_to_cloudwatch(event_type, data)
    except cloudwatch_logs.exceptions.InvalidSequenceTokenException as e:
        sequence_token = e.response['Error']['Message'].split('is: ')[-1]
        log_to_cloudwatch(event_type, data)
    except Exception as e:
        logger.error(f"CloudWatch logging failed: {e}")


def setup_cloudwatch_logging():
    """Initialize CloudWatch logging on service startup"""
    if CLOUDWATCH_ENABLED:
        ensure_log_stream()
        log_to_cloudwatch('service_startup', {
            'message': 'Request Management Service started',
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        })
