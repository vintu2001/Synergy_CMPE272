"""
Query resident complaint history from DynamoDB
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
except ImportError:
    print("python-dotenv not installed, using existing environment variables")

from app.services.database import get_resident_complaints_last_month, get_table
from boto3.dynamodb.conditions import Key

def query_resident_history(resident_id: str):
    """Query and display all requests for a resident."""
    try:
        # Get all complaints from last month
        complaints = get_resident_complaints_last_month(resident_id)
        
        print(f"\n{'='*80}")
        print(f"Found {len(complaints)} requests for resident: {resident_id}")
        print(f"{'='*80}\n")
        
        # Sort by created_at
        complaints_sorted = sorted(complaints, key=lambda x: x.get('created_at', ''))
        
        for idx, item in enumerate(complaints_sorted, 1):
            print(f"\n{'-'*80}")
            print(f"Request #{idx}: {item.get('request_id')}")
            print(f"Created: {item.get('created_at', 'N/A')[:19]}")
            print(f"Message: {item.get('message_text', 'N/A')}")
            print(f"Category: {item.get('category', 'N/A')}")
            print(f"Urgency: {item.get('urgency', 'N/A')}")
            print(f"Risk Score: {float(item.get('risk_score', 0)):.4f}" if item.get('risk_score') else "N/A")
            
            # Get recommended option
            options = item.get('options', [])
            recommended_id = item.get('recommended_option_id', 'N/A')
            print(f"Recommended Option: {recommended_id}")
            
            if recommended_id != 'escalation' and options:
                # Find the recommended option
                for opt in options:
                    if opt.get('option_id') == recommended_id:
                        print(f"\n  Recommended Option Details:")
                        print(f"  - Action: {opt.get('action', 'N/A')[:150]}...")
                        print(f"  - Cost: ${float(opt.get('estimated_cost', 0)):.2f}")
                        print(f"  - Time: {float(opt.get('estimated_time', 0) or opt.get('time_to_resolution', 0)):.1f} hours")
                        print(f"  - Satisfaction Impact: {float(opt.get('resident_satisfaction_impact', 0)):.2f}")
                        break
            elif recommended_id == 'escalation':
                print(f"\n  ⚠️  ESCALATED TO HUMAN ADMINISTRATOR")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    resident_id = sys.argv[1] if len(sys.argv) > 1 else "test_user_456"
    query_resident_history(resident_id)
