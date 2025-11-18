import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import ExecutionRequest, IssueCategory


@pytest.mark.asyncio
@patch('app.api.routes.execute_decision')
async def test_execute_endpoint_maintenance(mock_execute):
    """Test execute endpoint for maintenance category."""
    mock_execute.return_value = {
        "status": "dispatched",
        "work_order_id": "WO_123456",
        "action": "Fix AC"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "chosen_action": "Fix AC unit",
            "chosen_option_id": "opt_1",
            "reasoning": "AC needs repair",
            "alternatives_considered": ["opt_2", "opt_3"],
            "category": "Maintenance"
        }
        response = await client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "dispatched"


@pytest.mark.asyncio
@patch('app.api.routes.execute_decision')
async def test_execute_endpoint_billing(mock_execute):
    """Test execute endpoint for billing category."""
    mock_execute.return_value = {
        "status": "sent",
        "notification_id": "BILL_123456",
        "message": "Billing notification sent successfully"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "chosen_action": "Send billing notification",
            "chosen_option_id": "opt_1",
            "reasoning": "Billing issue",
            "alternatives_considered": [],
            "category": "Billing"
        }
        response = await client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
@patch('app.api.routes.execute_decision')
async def test_execute_endpoint_deliveries(mock_execute):
    """Test execute endpoint for deliveries category."""
    mock_execute.return_value = {
        "status": "rerouted",
        "tracking_number": "TRACK_123456",
        "action": "Reroute package"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "chosen_action": "Reroute package",
            "chosen_option_id": "opt_1",
            "reasoning": "Package delivery issue",
            "alternatives_considered": [],
            "category": "Deliveries"
        }
        response = await client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
@patch('app.api.routes.execute_decision')
async def test_execute_endpoint_error(mock_execute):
    """Test execute endpoint error handling."""
    mock_execute.side_effect = Exception("Execution failed")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "chosen_action": "Test action",
            "chosen_option_id": "opt_1",
            "reasoning": "Test reasoning",
            "alternatives_considered": [],
            "category": "Maintenance"
        }
        response = await client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "error"
        assert "message" in data


@pytest.mark.asyncio
async def test_execute_endpoint_invalid_category():
    """Test execute endpoint with invalid category."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "chosen_action": "Test action",
            "chosen_option_id": "opt_1",
            "reasoning": "Test reasoning",
            "alternatives_considered": [],
            "category": "InvalidCategory"
        }
        # Should handle invalid category gracefully
        response = await client.post("/api/v1/execute", json=payload)
        # May return 200 with error or 422 validation error
        assert response.status_code in [200, 422]

