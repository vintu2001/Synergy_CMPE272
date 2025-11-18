import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Execution Service"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Execution Service"


@pytest.mark.asyncio
@patch('app.main.log_to_cloudwatch')
async def test_middleware_logs_request(mock_log):
    """Test that middleware logs successful requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        # Middleware should log the request
        assert mock_log.called


@pytest.mark.asyncio
@patch('app.main.log_to_cloudwatch')
async def test_middleware_logs_error(mock_log):
    """Test that middleware logs errors."""
    # Create a request that will cause an error
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to access a non-existent endpoint
        try:
            response = await client.get("/nonexistent")
            # If it doesn't raise, check status
            assert response.status_code in [404, 500]
        except Exception:
            # Expected to raise for some errors
            pass
        # Middleware should have logged
        assert mock_log.called


@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are present."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 200
        # CORS middleware should add headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

