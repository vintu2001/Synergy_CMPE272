from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add libs to path for shared models
sys.path.insert(0, '/app/libs')

from shared_models import (
    GovernanceLog, GovernanceQueryRequest, GovernanceQueryResponse,
    GovernanceStatsResponse, DecisionResponse, ClassificationResponse,
    IssueCategory, Urgency, Intent, HealthCheck
)
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
import logging
import json
import uuid
import watchtower

# Configure logging with CloudWatch
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler for local development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Add CloudWatch handler for AWS
try:
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    cloudwatch_handler = watchtower.CloudWatchLogHandler(
        log_group='/synergy/governance-service',
        stream_name='{machine_name}-{strftime:%Y-%m-%d}',
        boto3_client=boto3.client('logs', region_name=AWS_REGION)
    )
    cloudwatch_handler.setLevel(logging.INFO)
    logger.addHandler(cloudwatch_handler)
    logger.info("CloudWatch logging initialized successfully")
except Exception as e:
    logger.warning(f"CloudWatch logging not available: {e}. Using console logging only.")

app = FastAPI(title="governance-service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin_secret_key_12345")
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
GOVERNANCE_TABLE_NAME = os.getenv('AWS_DYNAMODB_GOVERNANCE_TABLE', 'aam_governance_logs')

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)


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
    return f"GOV_{timestamp}_{uuid.uuid4().hex[:8].upper()}"


def verify_admin_key(x_api_key: str = Header(...)):
    """Verify admin API key for governance access."""
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@app.get("/health", response_model=HealthCheck)
async def health():
    """Health check endpoint"""
    return HealthCheck(status="healthy", service="governance")


@app.post("/api/governance/verify")
async def verify_admin(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify admin API key"""
    try:
        verify_admin_key(x_api_key)
        return {"valid": True, "role": "admin"}
    except HTTPException:
        return {"valid": False, "role": None}


@app.post("/api/governance/log")
async def log_decision(log_data: Dict[str, Any]):
    """
    Log a decision to the governance system.
    Called by other services to record AI decisions.
    """
    try:
        log_id = generate_log_id()
        
        request_id = log_data.get("request_id")
        resident_id = log_data.get("resident_id")
        decision = log_data.get("decision", {})
        classification = log_data.get("classification", {})
        risk_score = log_data.get("risk_score")
        total_options_simulated = log_data.get("total_options_simulated", 0)
        estimated_cost = log_data.get("estimated_cost", 0.0)
        estimated_time = log_data.get("estimated_time", 0.0)
        exceeds_budget_threshold = log_data.get("exceeds_budget_threshold", False)
        exceeds_time_threshold = log_data.get("exceeds_time_threshold", False)
        policy_weights = log_data.get("policy_weights")
        
        # Build governance log entry
        governance_log = {
            'log_id': log_id,
            'request_id': request_id,
            'resident_id': resident_id,
            'decision_timestamp': datetime.now(timezone.utc).isoformat(),
            'chosen_action': decision.get('chosen_action', ''),
            'chosen_option_id': decision.get('chosen_option_id', ''),
            'category': classification.get('category', ''),
            'urgency': classification.get('urgency', ''),
            'intent': classification.get('intent', ''),
            'reasoning': decision.get('reasoning', ''),
            'policy_scores': decision.get('policy_scores', {}),
            'alternatives_considered': decision.get('alternatives_considered', []),
            'risk_score': risk_score,
            'total_options_simulated': total_options_simulated,
            'estimated_cost': estimated_cost,
            'estimated_time': estimated_time,
            'exceeds_budget_threshold': exceeds_budget_threshold,
            'exceeds_time_threshold': exceeds_time_threshold,
            'escalated': decision.get('escalation_reason') is not None,
            'escalation_reason': decision.get('escalation_reason'),
            'agent_version': 'v1.0',
            'policy_weights': policy_weights or {}
        }
        
        # Convert floats to Decimal for DynamoDB
        governance_log_db = convert_floats_to_decimal(governance_log)
        
        # Store in DynamoDB
        table = get_governance_table()
        table.put_item(Item=governance_log_db)
        
        logger.info(f"Governance log created: {log_id} for request {request_id}")
        logger.info(f"Log details - Category: {classification.get('category')}, Urgency: {classification.get('urgency')}, Action: {decision.get('chosen_action')}")
        return {"success": True, "log_id": log_id}
        
    except Exception as e:
        logger.error(f"Error logging decision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log decision: {str(e)}")


@app.post("/api/governance/query", response_model=GovernanceQueryResponse)
async def query_logs(
    query: GovernanceQueryRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Query governance logs with filters"""
    verify_admin_key(x_api_key)
    
    try:
        table = get_governance_table()
        
        # Build filter expression
        filter_expression = None
        filters_applied = {}
        
        if query.request_id:
            filter_expression = Attr('request_id').eq(query.request_id)
            filters_applied['request_id'] = query.request_id
        
        if query.resident_id:
            expr = Attr('resident_id').eq(query.resident_id)
            filter_expression = expr if filter_expression is None else filter_expression & expr
            filters_applied['resident_id'] = query.resident_id
        
        if query.category:
            expr = Attr('category').eq(query.category.value)
            filter_expression = expr if filter_expression is None else filter_expression & expr
            filters_applied['category'] = query.category.value
        
        if query.urgency:
            expr = Attr('urgency').eq(query.urgency.value)
            filter_expression = expr if filter_expression is None else filter_expression & expr
            filters_applied['urgency'] = query.urgency.value
        
        if query.escalated_only:
            expr = Attr('escalated').eq(True)
            filter_expression = expr if filter_expression is None else filter_expression & expr
            filters_applied['escalated_only'] = True
        
        # Perform scan with filter
        scan_kwargs = {'Limit': query.limit}
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
        
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Convert Decimals to float
        items = convert_decimals_to_float(items)
        
        # Convert to GovernanceLog objects
        logs = []
        for item in items:
            try:
                log = GovernanceLog(**item)
                logs.append(log)
            except Exception as e:
                logger.warning(f"Could not parse log item: {e}")
        
        return GovernanceQueryResponse(
            logs=logs,
            total_count=len(logs),
            filters_applied=filters_applied
        )
        
    except Exception as e:
        logger.error(f"Error querying governance logs: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/governance/stats", response_model=GovernanceStatsResponse)
async def get_stats(x_api_key: str = Header(..., alias="X-API-Key")):
    """Get aggregate statistics about governance logs"""
    verify_admin_key(x_api_key)
    
    try:
        table = get_governance_table()
        response = table.scan()
        items = response.get('Items', [])
        
        # Convert Decimals
        items = convert_decimals_to_float(items)
        
        # Calculate statistics
        total_decisions = len(items)
        total_escalations = sum(1 for item in items if item.get('escalated', False))
        escalation_rate = total_escalations / total_decisions if total_decisions > 0 else 0.0
        
        costs = [item.get('estimated_cost', 0) for item in items]
        times = [item.get('estimated_time', 0) for item in items]
        average_cost = sum(costs) / len(costs) if costs else 0.0
        average_time = sum(times) / len(times) if times else 0.0
        
        # Group by category and urgency
        decisions_by_category = {}
        decisions_by_urgency = {}
        
        for item in items:
            cat = item.get('category', 'Unknown')
            urg = item.get('urgency', 'Unknown')
            decisions_by_category[cat] = decisions_by_category.get(cat, 0) + 1
            decisions_by_urgency[urg] = decisions_by_urgency.get(urg, 0) + 1
        
        cost_violations = sum(1 for item in items if item.get('exceeds_budget_threshold', False))
        time_violations = sum(1 for item in items if item.get('exceeds_time_threshold', False))
        
        return GovernanceStatsResponse(
            total_decisions=total_decisions,
            total_escalations=total_escalations,
            escalation_rate=escalation_rate,
            average_cost=average_cost,
            average_time=average_time,
            decisions_by_category=decisions_by_category,
            decisions_by_urgency=decisions_by_urgency,
            cost_threshold_violations=cost_violations,
            time_threshold_violations=time_violations
        )
        
    except Exception as e:
        logger.error(f"Error getting governance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats calculation failed: {str(e)}")


@app.get("/api/governance/export")
async def export_logs(
    format: str = "json",
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Export all governance logs for compliance/audit purposes"""
    verify_admin_key(x_api_key)
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    try:
        table = get_governance_table()
        response = table.scan()
        items = response.get('Items', [])
        items = convert_decimals_to_float(items)
        
        if format == "csv":
            # Simple CSV export
            if not items:
                return PlainTextResponse(
                    content="",
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=governance_logs.csv"}
                )
            
            headers = list(items[0].keys())
            csv_lines = [",".join(headers)]
            
            for item in items:
                values = [str(item.get(h, "")) for h in headers]
                csv_lines.append(",".join(values))
            
            csv_content = "\n".join(csv_lines)
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=governance_logs.csv"}
            )
        else:
            # JSON export
            json_content = json.dumps(items, indent=2, default=str)
            return PlainTextResponse(
                content=json_content,
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=governance_logs.json"}
            )
            
    except Exception as e:
        logger.error(f"Error exporting governance logs: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
