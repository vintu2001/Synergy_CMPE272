"""
Lambda Function: Update Widget 4 Metrics
Queries governance stats API and pushes metrics to CloudWatch
Trigger: CloudWatch Events (every 5 minutes)
"""
import json
import boto3
import os
import requests
from datetime import datetime, timezone

# Initialize CloudWatch client
cloudwatch = boto3.client('cloudwatch')

# Configuration
GOVERNANCE_API_URL = os.getenv('GOVERNANCE_API_URL', 'http://your-backend-url/api/v1')
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'your_admin_api_key_here')
NAMESPACE = 'AgenticApartmentManager/Widget4'

def lambda_handler(event, context):
    """
    Lambda handler that fetches governance stats and pushes to CloudWatch.
    """
    try:
        # Fetch governance statistics
        response = requests.get(
            f"{GOVERNANCE_API_URL}/governance/stats",
            headers={"X-API-Key": ADMIN_API_KEY},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Error fetching stats: {response.status_code}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to fetch governance stats'})
            }
        
        stats = response.json()
        
        # Extract metrics
        total_requests = stats.get('total_decisions', 0)
        total_escalations = stats.get('total_escalations', 0)
        escalation_rate = stats.get('escalation_rate', 0.0)
        avg_time = stats.get('average_time', 0.0)
        avg_cost = stats.get('average_cost', 0.0)
        cost_violations = stats.get('cost_threshold_violations', 0)
        time_violations = stats.get('time_threshold_violations', 0)
        
        # Calculate derived metrics
        success_rate = (1 - escalation_rate) * 100
        error_rate = escalation_rate * 100
        avg_response_time_sec = avg_time * 3600  # Convert hours to seconds
        
        # Prepare metric data
        metric_data = [
            {
                'MetricName': 'TotalRequests',
                'Value': float(total_requests),
                'Unit': 'Count',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'TotalEscalations',
                'Value': float(total_escalations),
                'Unit': 'Count',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'EscalationRate',
                'Value': escalation_rate,
                'Unit': 'Percent',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'SuccessRate',
                'Value': success_rate,
                'Unit': 'Percent',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'ErrorRate',
                'Value': error_rate,
                'Unit': 'Percent',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'AverageResponseTime',
                'Value': avg_response_time_sec,
                'Unit': 'Seconds',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'AverageCost',
                'Value': avg_cost,
                'Unit': 'None',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'AverageResolutionTime',
                'Value': avg_time,
                'Unit': 'None',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'CostThresholdViolations',
                'Value': float(cost_violations),
                'Unit': 'Count',
                'Timestamp': datetime.now(timezone.utc)
            },
            {
                'MetricName': 'TimeThresholdViolations',
                'Value': float(time_violations),
                'Unit': 'Count',
                'Timestamp': datetime.now(timezone.utc)
            }
        ]
        
        # Push metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=metric_data
        )
        
        print(f"Successfully pushed {len(metric_data)} metrics to CloudWatch")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Metrics updated successfully',
                'metrics_pushed': len(metric_data),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Request failed: {str(e)}'})
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Unexpected error: {str(e)}'})
        }

