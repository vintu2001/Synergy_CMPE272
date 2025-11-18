import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
@patch('app.api.resident_api.get_requests_by_resident')
async def test_get_resident_requests(mock_get_requests):
    from datetime import datetime
    from app.models.schemas import ResidentRequest, Status
    
    mock_get_requests.return_value = [
        ResidentRequest(
            request_id="REQ1",
            resident_id="R001",
            resident_name="John Doe",
            message_text="Test request",
            category="Maintenance",
            urgency="High",
            intent="solve_problem",
            status=Status.SUBMITTED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/get-requests/R001")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["resident_id"] == "R001"


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_classify_message_success(mock_httpx_client):
    mock_client_instance = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "category": "Maintenance",
        "urgency": "High",
        "intent": "solve_problem",
        "confidence": 0.95
    }
    mock_response.raise_for_status = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "resident_id": "R001",
            "message_text": "My AC is broken"
        }
        response = await client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Maintenance"
        assert data["urgency"] == "High"


@pytest.mark.asyncio
async def test_classify_message_invalid_payload():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"invalid": "data"}
        response = await client.post("/api/v1/classify", json=payload)
        assert response.status_code == 422
