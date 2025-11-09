"""
Governance Service - Ticket 15
Custom AI Governance Logger (Watsonx.governance Alternative)

Provides:
- Decision logging with full audit trails
- Query API for governance analytics
- Export capabilities for compliance
- Statistics and metrics tracking

This implementation mimics IBM Watsonx.governance features for academic purposes.
"""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from app.models.schemas import (
    GovernanceLog, GovernanceQueryRequest, GovernanceQueryResponse,
    GovernanceStatsResponse, DecisionResponse, ClassificationResponse,
    IssueCategory, Urgency, Intent
)
import os
import logging
import json

logger = logging.getLogger(__name__)

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

GOVERNANCE_TABLE_NAME = os.getenv('AWS_DYNAMODB_GOVERNANCE_TABLE', 'aam_governance_logs')


def get_governance_table():
    """Get the governance logs DynamoDB table."""
    return dynamodb.Table(GOVERNANCE_TABLE_NAME)


def convert_floats_to_decimal(obj: Any) -> Any:
    """Recursively convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif hasattr(obj, 'value'):  # Handle Enum types
        return obj.value
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj


def convert_decimals_to_float(obj: Any) -> Any:
    """Recursively convert Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    return obj


def generate_log_id() -> str:
    """Generate a unique governance log ID."""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    import uuid
    return f"GOV_{timestamp}_{uuid.uuid4().hex[:8].upper()}"


async def log_decision(
    request_id: str,
    resident_id: str,
    decision: DecisionResponse,
    classification: ClassificationResponse,
    risk_score: Optional[float] = None,
    total_options_simulated: int = 0,
    estimated_cost: float = 0.0,
    estimated_time: float = 0.0,
    exceeds_budget_threshold: bool = False,
    exceeds_time_threshold: bool = False,
    policy_weights: Optional[Dict[str, float]] = None
) -> bool:
    """
    Log a decision to the governance system.
    
    Args:
        request_id: The request ID associated with this decision
        resident_id: The resident who made the request
        decision: The decision response object
        classification: The classification response object
        risk_score: Optional risk score
        total_options_simulated: Number of options simulated
        estimated_cost: Estimated cost of chosen action
        estimated_time: Estimated time to resolution
        exceeds_budget_threshold: Whether cost exceeded threshold
        exceeds_time_threshold: Whether time exceeded threshold
        policy_weights: Policy weights used in decision
        
    Returns:
        bool: True if logging succeeded, False otherwise
    """
    try:
        table = get_governance_table()
        
        # Create governance log entry
        governance_log = GovernanceLog(
            log_id=generate_log_id(),
            request_id=request_id,
            resident_id=resident_id,
            decision_timestamp=datetime.now(timezone.utc),
            chosen_action=decision.chosen_action,
            chosen_option_id=decision.chosen_option_id,
            category=classification.category,
            urgency=classification.urgency,
            intent=classification.intent,
            reasoning=decision.reasoning,
            policy_scores=decision.policy_scores or {},
            alternatives_considered=decision.alternatives_considered,
            risk_score=risk_score,
            total_options_simulated=total_options_simulated,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            exceeds_budget_threshold=exceeds_budget_threshold,
            exceeds_time_threshold=exceeds_time_threshold,
            escalated=decision.escalation_reason is not None,
            escalation_reason=decision.escalation_reason,
            agent_version="v1.0",
            policy_weights=policy_weights or {"urgency": 0.4, "cost": 0.3, "time": 0.2, "satisfaction": 0.1}
        )
        
        # Convert to dict and handle DynamoDB types
        item = governance_log.dict()
        item = convert_floats_to_decimal(item)
        
        # Convert datetime objects to ISO format strings
        if 'decision_timestamp' in item and isinstance(item['decision_timestamp'], datetime):
            item['decision_timestamp'] = item['decision_timestamp'].isoformat()
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        logger.info(f"Governance log created: {governance_log.log_id} for request {request_id}")
        return True
        
    except ClientError as e:
        logger.error(f"Error logging decision to governance: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error logging decision: {e}")
        return False


async def query_governance_logs(query: GovernanceQueryRequest) -> GovernanceQueryResponse:
    """
    Query governance logs with filters.
    
    Args:
        query: Query request with filter parameters
        
    Returns:
        GovernanceQueryResponse with matching logs
    """
    try:
        table = get_governance_table()
        
        # Build filter expression
        filter_expressions = []
        expression_attribute_values = {}
        
        if query.request_id:
            filter_expressions.append(Attr('request_id').eq(query.request_id))
        
        if query.resident_id:
            filter_expressions.append(Attr('resident_id').eq(query.resident_id))
        
        if query.category:
            filter_expressions.append(Attr('category').eq(query.category.value))
        
        if query.urgency:
            filter_expressions.append(Attr('urgency').eq(query.urgency.value))
        
        if query.escalated_only:
            filter_expressions.append(Attr('escalated').eq(True))
        
        if query.start_date:
            filter_expressions.append(Attr('decision_timestamp').gte(query.start_date.isoformat()))
        
        if query.end_date:
            filter_expressions.append(Attr('decision_timestamp').lte(query.end_date.isoformat()))
        
        # Combine filters
        filter_expression = None
        if filter_expressions:
            filter_expression = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expression = filter_expression & expr
        
        # Scan with filters
        scan_kwargs = {'Limit': query.limit}
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
        
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Convert Decimal to float for JSON serialization
        items = [convert_decimals_to_float(item) for item in items]
        
        # Parse items into GovernanceLog objects
        logs = []
        for item in items:
            # Convert ISO strings back to datetime
            if 'decision_timestamp' in item and isinstance(item['decision_timestamp'], str):
                item['decision_timestamp'] = datetime.fromisoformat(item['decision_timestamp'].replace('Z', '+00:00'))
            logs.append(GovernanceLog(**item))
        
        # Build filters_applied dict
        filters_applied = {
            "request_id": query.request_id,
            "resident_id": query.resident_id,
            "category": query.category.value if query.category else None,
            "urgency": query.urgency.value if query.urgency else None,
            "escalated_only": query.escalated_only,
            "start_date": query.start_date.isoformat() if query.start_date else None,
            "end_date": query.end_date.isoformat() if query.end_date else None,
            "limit": query.limit
        }
        # Remove None values
        filters_applied = {k: v for k, v in filters_applied.items() if v is not None}
        
        return GovernanceQueryResponse(
            logs=logs,
            total_count=len(logs),
            query_timestamp=datetime.now(timezone.utc),
            filters_applied=filters_applied
        )
        
    except ClientError as e:
        logger.error(f"Error querying governance logs: {e}")
        return GovernanceQueryResponse(
            logs=[],
            total_count=0,
            query_timestamp=datetime.now(timezone.utc),
            filters_applied={"error": str(e)}
        )


async def get_governance_stats() -> GovernanceStatsResponse:
    """
    Get aggregate statistics about governance logs.
    
    Returns:
        GovernanceStatsResponse with analytics
    """
    try:
        table = get_governance_table()
        
        # Scan all items for statistics
        response = table.scan()
        items = response.get('Items', [])
        
        # Convert Decimal to float
        items = [convert_decimals_to_float(item) for item in items]
        
        if not items:
            return GovernanceStatsResponse(
                total_decisions=0,
                total_escalations=0,
                escalation_rate=0.0,
                average_cost=0.0,
                average_time=0.0,
                decisions_by_category={},
                decisions_by_urgency={},
                cost_threshold_violations=0,
                time_threshold_violations=0
            )
        
        # Calculate statistics
        total_decisions = len(items)
        total_escalations = sum(1 for item in items if item.get('escalated', False))
        escalation_rate = total_escalations / total_decisions if total_decisions > 0 else 0.0
        
        total_cost = sum(item.get('estimated_cost', 0.0) for item in items)
        average_cost = total_cost / total_decisions if total_decisions > 0 else 0.0
        
        total_time = sum(item.get('estimated_time', 0.0) for item in items)
        average_time = total_time / total_decisions if total_decisions > 0 else 0.0
        
        # Count by category
        decisions_by_category = {}
        for item in items:
            category = item.get('category', 'Unknown')
            decisions_by_category[category] = decisions_by_category.get(category, 0) + 1
        
        # Count by urgency
        decisions_by_urgency = {}
        for item in items:
            urgency = item.get('urgency', 'Unknown')
            decisions_by_urgency[urgency] = decisions_by_urgency.get(urgency, 0) + 1
        
        # Count threshold violations
        cost_threshold_violations = sum(1 for item in items if item.get('exceeds_budget_threshold', False))
        time_threshold_violations = sum(1 for item in items if item.get('exceeds_time_threshold', False))
        
        return GovernanceStatsResponse(
            total_decisions=total_decisions,
            total_escalations=total_escalations,
            escalation_rate=escalation_rate,
            average_cost=average_cost,
            average_time=average_time,
            decisions_by_category=decisions_by_category,
            decisions_by_urgency=decisions_by_urgency,
            cost_threshold_violations=cost_threshold_violations,
            time_threshold_violations=time_threshold_violations
        )
        
    except ClientError as e:
        logger.error(f"Error calculating governance stats: {e}")
        return GovernanceStatsResponse(
            total_decisions=0,
            total_escalations=0,
            escalation_rate=0.0,
            average_cost=0.0,
            average_time=0.0,
            decisions_by_category={},
            decisions_by_urgency={},
            cost_threshold_violations=0,
            time_threshold_violations=0
        )


async def export_governance_logs(format: str = "json") -> str:
    """
    Export all governance logs for compliance/audit purposes.
    
    Args:
        format: Export format ("json" or "csv")
        
    Returns:
        str: Exported data as string
    """
    try:
        table = get_governance_table()
        response = table.scan()
        items = response.get('Items', [])
        
        # Convert Decimal to float
        items = [convert_decimals_to_float(item) for item in items]
        
        if format == "json":
            return json.dumps(items, indent=2, default=str)
        elif format == "csv":
            if not items:
                return ""
            
            # Get all keys from first item
            keys = items[0].keys()
            
            # Build CSV
            csv_lines = [",".join(keys)]
            for item in items:
                values = [str(item.get(key, "")) for key in keys]
                csv_lines.append(",".join(values))
            
            return "\n".join(csv_lines)
        else:
            return json.dumps(items, indent=2, default=str)
            
    except ClientError as e:
        logger.error(f"Error exporting governance logs: {e}")
        return json.dumps({"error": str(e)})

