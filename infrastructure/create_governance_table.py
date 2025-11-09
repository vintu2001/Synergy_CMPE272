#!/usr/bin/env python3
"""
Create DynamoDB Governance Logs Table - Ticket 15
Creates a table for storing AI decision governance logs.
"""
import boto3
from botocore.exceptions import ClientError
import os
import sys

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Using environment variables.")

REGION = os.getenv('AWS_REGION', 'us-west-2')
TABLE_NAME = os.getenv('AWS_DYNAMODB_GOVERNANCE_TABLE', 'aam_governance_logs')


def create_governance_table():
    """Create the governance logs DynamoDB table."""
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        # Check if table already exists
        existing_tables = list(dynamodb.tables.all())
        if any(table.name == TABLE_NAME for table in existing_tables):
            print(f"✅ Table '{TABLE_NAME}' already exists!")
            return True
        
        # Create table
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'log_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'log_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'request_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'decision_timestamp',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'RequestIdIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'request_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'TimestampIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'decision_timestamp',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            },
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'AgenticApartmentManager'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'AIGovernanceLogs'
                },
                {
                    'Key': 'Ticket',
                    'Value': 'Ticket15'
                }
            ]
        )
        
        # Wait for table to be created
        print(f"⏳ Creating table '{TABLE_NAME}'...")
        table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)
        print(f"✅ Table '{TABLE_NAME}' created successfully!")
        
        # Print table details
        print(f"\n📊 Table Details:")
        print(f"   Table Name: {table.table_name}")
        print(f"   Table ARN: {table.table_arn}")
        print(f"   Table Status: {table.table_status}")
        print(f"   Item Count: {table.item_count}")
        print(f"   Table Size: {table.table_size_bytes} bytes")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error creating table: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_table():
    """Verify the governance table was created correctly."""
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.load()
        
        print(f"\n✅ Table Verification:")
        print(f"   Table Name: {table.table_name}")
        print(f"   Table Status: {table.table_status}")
        print(f"   Key Schema: {table.key_schema}")
        print(f"   Global Secondary Indexes:")
        for gsi in table.global_secondary_indexes or []:
            print(f"      - {gsi['IndexName']}: {gsi['KeySchema']}")
        
        return True
    except ClientError as e:
        print(f"❌ Error verifying table: {e}")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("DynamoDB Governance Logs Table Creation - Ticket 15")
    print("=" * 80)
    print(f"Region: {REGION}")
    print(f"Table Name: {TABLE_NAME}")
    print("=" * 80)
    
    # Create table
    if create_governance_table():
        # Verify table
        verify_table()
        print("\n" + "=" * 80)
        print("✅ Governance table setup complete!")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. Add AWS_DYNAMODB_GOVERNANCE_TABLE to your .env file")
        print(f"   AWS_DYNAMODB_GOVERNANCE_TABLE={TABLE_NAME}")
        print("2. Restart your backend server")
        print("3. Submit a test request to verify governance logging")
        print("4. Query governance logs via API: POST /api/v1/governance/query")
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ Governance table setup failed!")
        print("=" * 80)
        sys.exit(1)

