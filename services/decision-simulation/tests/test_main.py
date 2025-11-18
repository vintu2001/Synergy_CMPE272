import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

import asyncio

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
