"""
Sample KB documents for RAG testing.
Provides mock documents that simulate actual knowledge base content.
"""

from typing import List, Dict, Any


# Sample policy documents
SAMPLE_POLICIES = [
    {
        "doc_id": "test_policy_noise_1.0",
        "type": "policy",
        "category": "community",
        "building_id": "TestBuilding1",
        "title": "Noise Complaint Policy",
        "text": """# Noise Complaint Policy

## Quiet Hours
Quiet hours are enforced from 10:00 PM to 8:00 AM on all days.

## Violation Response
- First violation: Written warning
- Second violation: $50 fine
- Third violation: Lease review meeting

## Emergency Noise
For emergency noise situations (construction, alarm malfunction), contact on-call manager immediately.
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["noise", "quiet_hours", "violations", "complaints"]
        }
    },
    {
        "doc_id": "test_policy_maint_1.0",
        "type": "policy",
        "category": "maintenance",
        "building_id": "all_buildings",
        "title": "Emergency Maintenance Policy",
        "text": """# Emergency Maintenance Policy

## Response Times
- High urgency: Within 2 hours
- Medium urgency: Within 24 hours
- Low urgency: Within 7 days

## HVAC Emergencies
HVAC failures during extreme weather (>90°F or <32°F) require:
- 1-hour priority response
- Pre-approved emergency service up to $300
- Use approved 24/7 HVAC vendors only

## Cost Approvals
- Emergency repairs up to $500: Auto-approved
- Repairs $500-$1000: Manager approval required
- Repairs >$1000: Owner approval required
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["maintenance", "emergency", "hvac", "response_time"]
        }
    },
    {
        "doc_id": "test_policy_parking_1.0",
        "type": "policy",
        "category": "parking",
        "building_id": "TestBuilding1",
        "title": "Parking Policy",
        "text": """# Parking Policy

## Assigned Spaces
Each unit receives 1 assigned parking space. Additional spaces available for $50/month.

## Guest Parking
Guest parking available in designated areas. 48-hour maximum stay.

## Violations
- Unauthorized parking in assigned space: Warning + towing
- Blocking fire lane: Immediate towing + $200 fine
- Expired registration: 30-day notice to update
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["parking", "violations", "guest", "towing"]
        }
    }
]

# Sample SOP documents
SAMPLE_SOPS = [
    {
        "doc_id": "test_sop_emergency_1.0",
        "type": "sop",
        "category": "operations",
        "building_id": "all_buildings",
        "title": "Emergency Response SOP",
        "text": """# Emergency Response Standard Operating Procedure

## HVAC Emergency Procedure
1. Assess severity (high if temp >90°F or medical need)
2. Contact approved 24/7 HVAC vendor from catalog
3. If vendor unavailable, provide portable AC unit as temp solution
4. Log incident in maintenance system
5. Follow up within 4 hours to confirm resolution

## Plumbing Emergency Procedure
1. Shut off water if active leak
2. Contact emergency plumber from approved vendor list
3. Document damage for insurance if applicable
4. Notify affected residents
5. Schedule follow-up inspection

## After-Hours Protocol
- On-call manager must respond within 30 minutes
- Emergency vendors have 2-hour maximum response time
- All emergency calls logged in system within 1 hour
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["emergency", "response", "procedure", "hvac", "plumbing"]
        }
    },
    {
        "doc_id": "test_sop_noise_complaint_1.0",
        "type": "sop",
        "category": "operations",
        "building_id": "all_buildings",
        "title": "Noise Complaint Handling SOP",
        "text": """# Noise Complaint Handling Procedure

## Initial Response
1. Log complaint with timestamp and details
2. Verify if during quiet hours (10 PM - 8 AM)
3. Check resident history for previous complaints

## Investigation Steps
1. Attempt to contact noise-making resident
2. Document response or lack thereof
3. If no response, leave door notice
4. Escalate to on-call manager if continues

## Follow-up
- Contact complainant within 24 hours with update
- If resolved, mark complete
- If recurring, schedule mediation meeting
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["noise", "complaint", "procedure", "quiet_hours"]
        }
    }
]

# Sample catalog documents
SAMPLE_CATALOGS = [
    {
        "doc_id": "test_catalog_hvac_vendors_1.0",
        "type": "catalog",
        "category": "vendors",
        "building_id": "TestBuilding1",
        "title": "HVAC Vendors",
        "text": """# Approved HVAC Vendors

## 24/7 Emergency Service
- **ABC Cooling Services**: (555) 123-4567
  - Average response: 45 minutes
  - Service area: All buildings
  - Specialties: Emergency repairs, system replacements

- **QuickFix HVAC**: (555) 234-5678
  - Average response: 60 minutes
  - Service area: Downtown only
  - Specialties: Routine maintenance, filter replacements

- **Arctic Air Pros**: (555) 345-6789
  - Average response: 90 minutes
  - Service area: All buildings
  - Specialties: Commercial systems, large repairs
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["hvac", "vendors", "emergency", "contact"]
        }
    }
]

# Sample SLA documents
SAMPLE_SLAS = [
    {
        "doc_id": "test_sla_response_times_1.0",
        "type": "sla",
        "category": "service_level",
        "building_id": "all_buildings",
        "title": "Response Time SLAs",
        "text": """# Service Level Agreement - Response Times

## Emergency Response
- Critical (life safety): 15 minutes
- High urgency: 2 hours
- Medium urgency: 24 hours
- Low urgency: 7 days

## Resolution Times
- Critical: 4 hours
- High: 24 hours
- Medium: 72 hours
- Low: 14 days

## Penalties
Failure to meet SLA may result in:
- Rent credit: $25/day for critical issues
- Service credit: $10/day for high urgency issues
""",
        "metadata": {
            "effective_date": "2024-01-01",
            "version": "1.0",
            "keywords": ["sla", "response", "resolution", "timeline"]
        }
    }
]


def get_all_sample_documents() -> List[Dict[str, Any]]:
    """Get all sample documents combined."""
    return SAMPLE_POLICIES + SAMPLE_SOPS + SAMPLE_CATALOGS + SAMPLE_SLAS


def get_documents_by_type(doc_type: str) -> List[Dict[str, Any]]:
    """Get sample documents filtered by type."""
    mapping = {
        "policy": SAMPLE_POLICIES,
        "sop": SAMPLE_SOPS,
        "catalog": SAMPLE_CATALOGS,
        "sla": SAMPLE_SLAS
    }
    return mapping.get(doc_type, [])


def get_documents_by_building(building_id: str) -> List[Dict[str, Any]]:
    """Get sample documents filtered by building ID."""
    all_docs = get_all_sample_documents()
    return [
        doc for doc in all_docs
        if doc.get("building_id") in [building_id, "all_buildings"]
    ]


def get_document_by_id(doc_id: str) -> Dict[str, Any]:
    """Get a specific sample document by ID."""
    all_docs = get_all_sample_documents()
    for doc in all_docs:
        if doc.get("doc_id") == doc_id:
            return doc
    return None


# Test queries mapped to expected relevant documents
TEST_QUERIES = {
    "noise_complaint": {
        "query": "neighbor making loud noise at night",
        "expected_docs": ["test_policy_noise_1.0", "test_sop_noise_complaint_1.0"],
        "category": "community",
        "urgency": "Medium"
    },
    "hvac_emergency": {
        "query": "air conditioner broken and it's 95 degrees",
        "expected_docs": ["test_policy_maint_1.0", "test_sop_emergency_1.0", "test_catalog_hvac_vendors_1.0"],
        "category": "maintenance",
        "urgency": "High"
    },
    "parking_violation": {
        "query": "car parked in my assigned spot",
        "expected_docs": ["test_policy_parking_1.0"],
        "category": "parking",
        "urgency": "Low"
    },
    "plumbing_emergency": {
        "query": "pipe burst water everywhere",
        "expected_docs": ["test_sop_emergency_1.0", "test_policy_maint_1.0"],
        "category": "maintenance",
        "urgency": "High"
    }
}


def get_test_query(query_name: str) -> Dict[str, Any]:
    """Get a test query configuration by name."""
    return TEST_QUERIES.get(query_name)


def get_all_test_queries() -> Dict[str, Dict[str, Any]]:
    """Get all test queries."""
    return TEST_QUERIES
