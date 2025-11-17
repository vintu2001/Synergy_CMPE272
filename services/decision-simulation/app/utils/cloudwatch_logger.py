import boto3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
LOG_GROUP = os.getenv('AWS_CLOUDWATCH_LOG_GROUP', '/aws/apartment-manager/application')
LOG_STREAM = os.getenv('AWS_CLOUDWATCH_LOG_STREAM', 'backend-api')

try:
    cloudwatch_logs = boto3.client('logs', region_name=AWS_REGION)
    CLOUDWATCH_ENABLED = True
    logger.info("CloudWatch Logs client initialized")
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


def log_to_cloudwatch(event_type: str, data: Dict[str, Any]):
    """Send structured log to CloudWatch"""
    global sequence_token
    
    if not CLOUDWATCH_ENABLED:
        logger.debug(f"CloudWatch disabled - would log: {event_type}")
        return
    
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            **data
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


def log_request_submission(
    request_id: str,
    resident_id: str,
    category: str,
    urgency: str,
    confidence: float,
    message_preview: str = None
):
    """Log request submission"""
    log_to_cloudwatch('request_submitted', {
        'request_id': request_id,
        'resident_id': resident_id,
        'category': category,
        'urgency': urgency,
        'classification_confidence': confidence,
        'message_preview': message_preview[:100] if message_preview else None
    })


def log_repeat_detection(
    request_id: str,
    resident_id: str,
    category: str,
    is_repeat: bool,
    repeat_count: int,
    similarity_scores: list = None,
    method: str = None
):
    """Log repeat issue detection"""
    log_to_cloudwatch('repeat_detection', {
        'request_id': request_id,
        'resident_id': resident_id,
        'category': category,
        'is_repeat': is_repeat,
        'repeat_count': repeat_count,
        'detection_method': method or 'unknown',
        'top_similarity_score': max(similarity_scores) if similarity_scores else None
    })


def log_classification(
    request_id: str,
    category: str,
    urgency: str,
    intent: str,
    confidence: float
):
    """Log classification result"""
    log_to_cloudwatch('classification', {
        'request_id': request_id,
        'category': category,
        'urgency': urgency,
        'intent': intent,
        'confidence': confidence
    })


def log_risk_assessment(
    request_id: str,
    risk_score: float,
    risk_level: str
):
    """Log risk assessment"""
    log_to_cloudwatch('risk_assessment', {
        'request_id': request_id,
        'risk_score': risk_score,
        'risk_level': risk_level
    })


def log_simulation_result(
    request_id: str,
    option_count: int,
    recommended_option_id: str = None,
    is_repeat: bool = False
):
    """Log simulation result"""
    log_to_cloudwatch('simulation', {
        'request_id': request_id,
        'option_count': option_count,
        'recommended_option_id': recommended_option_id,
        'is_repeat_escalation': is_repeat
    })


def log_vector_search(
    request_id: str,
    query_time_ms: float,
    results_count: int,
    threshold: float
):
    """Log vector similarity search"""
    log_to_cloudwatch('vector_search', {
        'request_id': request_id,
        'query_time_ms': query_time_ms,
        'results_count': results_count,
        'similarity_threshold': threshold
    })


def log_error(
    error_type: str,
    error_message: str,
    context: Dict[str, Any] = None
):
    """Log error"""
    log_to_cloudwatch('error', {
        'error_type': error_type,
        'error_message': str(error_message),
        'context': context or {}
    })


def log_governance_decision(
    request_id: str,
    decision_id: str,
    chosen_option: str,
    estimated_cost: float,
    estimated_time: float
):
    """Log governance decision"""
    log_to_cloudwatch('governance_decision', {
        'request_id': request_id,
        'decision_id': decision_id,
        'chosen_option': chosen_option,
        'estimated_cost': estimated_cost,
        'estimated_time': estimated_time
    })


def setup_cloudwatch_logging():
    """Initialize CloudWatch logging on service startup"""
    if CLOUDWATCH_ENABLED:
        ensure_log_stream()
        log_to_cloudwatch('service_startup', {
            'service': 'decision-simulation',
            'message': 'Decision Simulation Service started',
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        })
