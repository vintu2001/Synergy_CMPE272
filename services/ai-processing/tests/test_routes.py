import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Processing Service"


@pytest.mark.asyncio
async def test_classify_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "resident_id": "R001",
            "message_text": "My air conditioning is broken"
        }
        response = await client.post("/api/v1/classify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert "urgency" in data
        assert "intent" in data
        assert "confidence" in data


@pytest.mark.asyncio
async def test_classify_endpoint_invalid_payload():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"invalid": "data"}
        response = await client.post("/api/v1/classify", json=payload)
        assert response.status_code == 422


@pytest.mark.asyncio
@patch('app.agents.classification_agent.classify_message')
async def test_classify_endpoint_service_error(mock_classify):
    # Simulate classification error
    mock_classify.side_effect = Exception("Classification failed")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "resident_id": "R001",
            "message_text": "Test message"
        }
        response = await client.post("/api/v1/classify", json=payload)
        # Should handle error gracefully
        assert response.status_code in [500, 200]


@pytest.mark.asyncio
async def test_classify_endpoint_empty_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "resident_id": "R001",
            "message_text": ""
        }
        response = await client.post("/api/v1/classify", json=payload)
        # Should either reject or handle empty message
        assert response.status_code in [200, 422]
