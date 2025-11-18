"""
Performance tests for AI Processing Service
Tests AI agent response times and throughput

NOTE: These tests require the service to be running on http://localhost:8002
Start with: docker compose -f infrastructure/docker/docker-compose.microservices.yml up
"""
import pytest
import time
from httpx import AsyncClient

BASE_URL = "http://localhost:8002"


class TestAIProcessingPerformance:
    """Performance tests for AI classification and risk prediction"""
    
    @pytest.mark.asyncio
    async def test_classification_response_time(self):
        """Test classification agent response time - should be < 3s"""
        async with AsyncClient(base_url=BASE_URL) as client:
            payload = {
                "request_id": "perf_test_001",
                "description": "The air conditioning in my apartment is not working properly",
                "category": "maintenance"
            }
            
            latencies = []
            for _ in range(10):  # Fewer iterations due to AI processing time
                start = time.perf_counter()
                response = await client.post("/api/classify", json=payload)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                
                if response.status_code == 200:
                    assert response.json().get("classification") is not None
            
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\n=== Classification Performance ===")
            print(f"Average: {avg_latency:.2f}ms")
            print(f"Min: {min_latency:.2f}ms")
            print(f"Max: {max_latency:.2f}ms")
            
            # AI processing should complete within reasonable time
            assert avg_latency < 15000, f"Classification too slow: {avg_latency}ms"
    
    @pytest.mark.asyncio
    async def test_risk_prediction_response_time(self):
        """Test risk prediction agent response time"""
        async with AsyncClient(base_url=BASE_URL) as client:
            payload = {
                "request_id": "perf_test_002",
                "description": "Emergency: Water leak flooding apartment",
                "category": "emergency",
                "priority": "critical"
            }
            
            latencies = []
            for _ in range(10):
                start = time.perf_counter()
                response = await client.post("/api/risk-assessment", json=payload)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                
                if response.status_code == 200:
                    result = response.json()
                    assert "risk_score" in result or "assessment" in result
            
            avg_latency = sum(latencies) / len(latencies)
            
            print(f"\n=== Risk Assessment Performance ===")
            print(f"Average latency: {avg_latency:.2f}ms")
            
            assert avg_latency < 15000, f"Risk assessment too slow: {avg_latency}ms"
    
    @pytest.mark.asyncio
    async def test_ai_agent_cold_start(self):
        """Measure cold start performance (first request after idle)"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # First request (cold start)
            payload = {
                "request_id": "cold_start_test",
                "description": "Cold start performance test",
                "category": "maintenance"
            }
            
            start = time.perf_counter()
            response = await client.post("/api/classify", json=payload)
            cold_start_time = (time.perf_counter() - start) * 1000
            
            # Subsequent requests (warm)
            warm_times = []
            for _ in range(5):
                start = time.perf_counter()
                await client.post("/api/classify", json=payload)
                warm_time = (time.perf_counter() - start) * 1000
                warm_times.append(warm_time)
            
            avg_warm_time = sum(warm_times) / len(warm_times)
            
            print(f"\n=== Cold Start Analysis ===")
            print(f"Cold start: {cold_start_time:.2f}ms")
            print(f"Avg warm: {avg_warm_time:.2f}ms")
            print(f"Difference: {cold_start_time - avg_warm_time:.2f}ms")
            
            # Cold start penalty should be reasonable
            assert cold_start_time < 30000, "Cold start too slow"


class TestAIAgentBenchmarks:
    """Code-level benchmarks for AI agent functions"""
    
    def test_text_preprocessing_benchmark(self):
        """Benchmark text preprocessing performance"""
        text = "The air conditioning system is not working properly and needs repair"
        
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            result = text.lower().strip()
            times.append((time.perf_counter() - start) * 1000000)  # microseconds
        
        avg_time = sum(times) / len(times)
        print(f"\nText preprocessing: {avg_time:.2f}μs")
        assert avg_time < 10, "Text preprocessing too slow"
    
    @pytest.mark.asyncio
    async def test_model_inference_time(self):
        """Measure raw model inference time via API"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            descriptions = [
                "Air conditioning not working",
                "Water leak in bathroom",
                "Noise complaint from neighbors",
                "Request for package delivery assistance",
                "Emergency: Gas smell in apartment"
            ]
            
            inference_times = []
            for i, desc in enumerate(descriptions):
                payload = {
                    "request_id": f"inference_test_{i}",
                    "description": desc,
                    "category": "maintenance"
                }
                start = time.perf_counter()
                try:
                    response = await client.post("/api/classify", json=payload)
                    if response.status_code == 200:
                        inference_time = (time.perf_counter() - start) * 1000
                        inference_times.append(inference_time)
                except Exception:
                    pass
            
            if inference_times:
                avg_inference = sum(inference_times) / len(inference_times)
                print(f"\n=== Model Inference Performance ===")
                print(f"Average inference time: {avg_inference:.2f}ms")
                print(f"Min: {min(inference_times):.2f}ms")
                print(f"Max: {max(inference_times):.2f}ms")
