import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
@patch('app.api.admin_api.get_all_requests')
async def test_get_all_requests_admin(mock_get_all):
    from datetime import datetime
    from app.models.schemas import ResidentRequest, Status
    
    mock_get_all.return_value = [
        ResidentRequest(
            request_id="REQ1",
            resident_id="R001",
            resident_name="John Doe",
            message_text="Test request 1",
            category="Maintenance",
            urgency="High",
            intent="solve_problem",
            status=Status.SUBMITTED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ResidentRequest(
            request_id="REQ2",
            resident_id="R002",
            resident_name="Jane Smith",
            message_text="Test request 2",
            category="Billing",
            urgency="Medium",
            intent="answer_a_question",
            status=Status.PROCESSING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/all-requests",
            headers={"X-API-Key": "default-admin-key-change-in-production"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["requests"]) == 2
        assert data["requests"][0]["request_id"] == "REQ1"
        assert data["requests"][1]["request_id"] == "REQ2"


@pytest.mark.asyncio
@patch('app.api.admin_api.get_all_requests')
async def test_get_all_requests_admin_empty(mock_get_all):
    mock_get_all.return_value = []
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/all-requests",
            headers={"X-API-Key": "default-admin-key-change-in-production"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["requests"]) == 0
