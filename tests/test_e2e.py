import pytest
import httpx
import asyncio
import time


BASE_URLS = {
    "request_management": "http://localhost:8001",
    "ai_processing": "http://localhost:8002",
    "decision_simulation": "http://localhost:8003",
    "execution": "http://localhost:8004"
}


@pytest.mark.asyncio
async def test_all_services_health():
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service, base_url in BASE_URLS.items():
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_end_to_end_request_flow():
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "resident_id": "R001",
            "message_text": "The air conditioning in my apartment is not working"
        }
        
        response = await client.post(
            f"{BASE_URLS['request_management']}/api/v1/submit-request",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "request_id" in data
        assert "classification" in data or "category" in data
        
        request_id = data["request_id"]
        print(f"\n✓ Request created: {request_id}")
        
        if "classification" in data:
            print(f"✓ Category: {data['classification']['category']}")
            print(f"✓ Urgency: {data['classification']['urgency']}")
        
        if "options" in data:
            print(f"✓ Options generated: {len(data['options'])}")
        elif "error_type" in data:
            print(f"✓ Response received (escalation required: {data.get('escalation_required', False)})")


@pytest.mark.asyncio
async def test_classification_endpoint():
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "resident_id": "R002",
            "message_text": "Emergency water leak in bathroom"
        }
        
        response = await client.post(
            f"{BASE_URLS['ai_processing']}/api/v1/classify",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "category" in data
        assert "urgency" in data
        assert "intent" in data
        assert "confidence" in data
        assert data["confidence"] > 0


@pytest.mark.asyncio
async def test_simulation_endpoint():
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "resident_id": "R003",
            "message_text": "Elevator is broken",
            "category": "Maintenance",
            "urgency": "High",
            "risk_score": 0.7
        }
        
        response = await client.post(
            f"{BASE_URLS['decision_simulation']}/api/v1/simulate",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "options" in data
        assert len(data["options"]) > 0


@pytest.mark.asyncio
async def test_execution_endpoint():
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "chosen_action": "Dispatch technician",
            "chosen_option_id": "OPT1",
            "reasoning": "Critical issue requiring immediate attention",
            "alternatives_considered": ["Schedule maintenance", "Defer to next week"],
            "category": "Maintenance"
        }
        
        response = await client.post(
            f"{BASE_URLS['execution']}/api/v1/execute",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data or "execution_id" in data


@pytest.mark.asyncio
async def test_multiple_concurrent_requests():
    async with httpx.AsyncClient(timeout=60.0) as client:
        messages = [
            "Air conditioning not working",
            "Water leak in kitchen",
            "Broken window in bedroom",
            "Elevator making noise",
            "Package delivery needed"
        ]
        
        tasks = []
        for i, message in enumerate(messages):
            payload = {
                "resident_id": f"R{i:03d}",
                "message_text": message
            }
            task = client.post(
                f"{BASE_URLS['request_management']}/api/v1/submit-request",
                json=payload
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        print(f"\n✓ {successful}/{len(messages)} concurrent requests succeeded")
        
        assert successful >= len(messages) * 0.8


@pytest.mark.asyncio
async def test_service_response_times():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response_times = {}
        
        for service, base_url in BASE_URLS.items():
            start = time.perf_counter()
            response = await client.get(f"{base_url}/health")
            elapsed = (time.perf_counter() - start) * 1000
            
            response_times[service] = elapsed
            assert elapsed < 5000, f"{service} health check too slow: {elapsed}ms"
        
        print("\n=== Service Response Times ===")
        for service, elapsed in response_times.items():
            print(f"{service}: {elapsed:.2f}ms")
