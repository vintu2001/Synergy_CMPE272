"""
Performance tests for Execution Service
Tests execution speed and workflow processing performance

NOTE: These tests require the service to be running on http://localhost:8004
Start with: docker compose -f infrastructure/docker/docker-compose.microservices.yml up
"""
import pytest
import time
from httpx import AsyncClient

BASE_URL = "http://localhost:8004"


class TestExecutionServicePerformance:
    """Performance tests for execution workflows"""
    
    @pytest.mark.asyncio
    async def test_execute_decision_response_time(self):
        """Test execution decision processing time"""
        async with AsyncClient(base_url=BASE_URL) as client:
            payload = {
                "request_id": "exec_perf_001",
                "decision": {
                    "action": "approve",
                    "assigned_to": "maintenance_team",
                    "estimated_cost": 150.00,
                    "priority": "medium"
                },
                "resident_id": "R001"
            }
            
            latencies = []
            for _ in range(20):
                start = time.perf_counter()
                response = await client.post("/api/execute", json=payload)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                
                if response.status_code == 200:
                    result = response.json()
                    assert "status" in result or "execution_id" in result
            
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
            
            print(f"\n=== Execution Performance ===")
            print(f"Average: {avg_latency:.2f}ms")
            print(f"P95: {p95_latency:.2f}ms")
            print(f"Min: {min(latencies):.2f}ms")
            print(f"Max: {max(latencies):.2f}ms")
            
            assert avg_latency < 2000, f"Execution too slow: {avg_latency}ms"
    
    @pytest.mark.asyncio
    async def test_workflow_processing_speed(self):
        """Test different workflow types processing speed"""
        async with AsyncClient(base_url=BASE_URL) as client:
            workflows = [
                {
                    "name": "Simple Approval",
                    "decision": {"action": "approve", "priority": "low"}
                },
                {
                    "name": "Emergency Escalation",
                    "decision": {"action": "escalate", "priority": "critical"}
                },
                {
                    "name": "Rejection",
                    "decision": {"action": "reject", "priority": "low"}
                },
                {
                    "name": "Complex Assignment",
                    "decision": {
                        "action": "approve",
                        "assigned_to": "specialist_team",
                        "requires_approval": True,
                        "priority": "high"
                    }
                }
            ]
            
            for workflow in workflows:
                payload = {
                    "request_id": f"workflow_{workflow['name'].replace(' ', '_')}",
                    "decision": workflow["decision"],
                    "resident_id": "R001"
                }
                
                start = time.perf_counter()
                response = await client.post("/api/execute", json=payload)
                processing_time = (time.perf_counter() - start) * 1000
                
                print(f"\n{workflow['name']}: {processing_time:.2f}ms")
                
                # All workflows should be fast
                assert processing_time < 1000, f"{workflow['name']} too slow"
    
    @pytest.mark.asyncio
    async def test_notification_delivery_performance(self):
        """Test notification delivery speed if applicable"""
        async with AsyncClient(base_url=BASE_URL) as client:
            payload = {
                "request_id": "notification_test",
                "decision": {
                    "action": "approve",
                    "notify_resident": True,
                    "priority": "high"
                },
                "resident_id": "R001"
            }
            
            notification_times = []
            for _ in range(10):
                start = time.perf_counter()
                response = await client.post("/api/execute", json=payload)
                notification_time = (time.perf_counter() - start) * 1000
                notification_times.append(notification_time)
            
            avg_time = sum(notification_times) / len(notification_times)
            
            print(f"\n=== Notification Performance ===")
            print(f"Average delivery time: {avg_time:.2f}ms")
            
            # Notifications should not significantly slow down execution
            assert avg_time < 1000, "Notifications causing slowdown"


class TestExecutionServiceScalability:
    """Test execution service under scaled load"""
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self):
        """Test performance under sustained load"""
        import asyncio
        
        async with AsyncClient(base_url=BASE_URL) as client:
            async def execute_batch():
                tasks = []
                for i in range(5):
                    payload = {
                        "request_id": f"sustained_{i}_{time.time()}",
                        "decision": {"action": "approve", "priority": "medium"},
                        "resident_id": f"R{i:03d}"
                    }
                    tasks.append(client.post("/api/execute", json=payload))
                
                return await asyncio.gather(*tasks, return_exceptions=True)
            
            # Run 3 batches
            batch_times = []
            for batch_num in range(3):
                start = time.perf_counter()
                results = await execute_batch()
                batch_time = (time.perf_counter() - start) * 1000
                batch_times.append(batch_time)
                
                success = sum(
                    1 for r in results 
                    if not isinstance(r, Exception) and r.status_code == 200
                )
                print(f"Batch {batch_num + 1}: {batch_time:.2f}ms, {success}/5 successful")
            
            # Performance should remain consistent across batches
            avg_batch_time = sum(batch_times) / len(batch_times)
            variation = max(batch_times) - min(batch_times)
            
            print(f"\nAverage batch time: {avg_batch_time:.2f}ms")
            print(f"Variation: {variation:.2f}ms")
            
            assert variation < avg_batch_time * 0.5, "Performance degrading under load"

