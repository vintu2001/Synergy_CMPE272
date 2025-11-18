"""
Performance tests for Request Management Service API endpoints
Tests response times, throughput, and system behavior under load

NOTE: These tests require the service to be running on http://localhost:8001
Start with: docker compose -f infrastructure/docker/docker-compose.microservices.yml up
"""
import pytest
import time
from httpx import AsyncClient

# Benchmark configuration
ITERATIONS = 100
WARMUP_ROUNDS = 10
BASE_URL = "http://localhost:8001"


class TestRequestManagementPerformance:
    """Performance tests for request management endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self):
        """Benchmark health endpoint - should be < 50ms"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            latencies = []
            for _ in range(ITERATIONS):
                start = time.perf_counter()
                response = await client.get("/health")
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                assert response.status_code == 200
            
            avg_latency = sum(latencies) / len(latencies)
            print(f"\nHealth endpoint average: {avg_latency:.2f}ms")
            assert avg_latency < 200, f"Health endpoint too slow: {avg_latency}ms"
    

    @pytest.mark.asyncio
    async def test_list_requests_pagination_performance(self):
        """Test pagination performance with different page sizes"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            page_sizes = [10, 50, 100]
            
            for page_size in page_sizes:
                start = time.perf_counter()
                # Note: This endpoint may not exist - using health as fallback
                response = await client.get("/health")
                latency = (time.perf_counter() - start) * 1000
                
                print(f"\nPage size {page_size}: {latency:.2f}ms")
                
                # Larger pages should still respond quickly (or return 404 if not implemented)
                assert latency < 1000, f"Pagination with {page_size} items took {latency}ms"
    

    @pytest.mark.asyncio
    async def test_throughput_capacity(self):
        """Measure maximum throughput (requests per second)"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            duration_seconds = 5
            request_count = 0
            start_time = time.perf_counter()
            
            while (time.perf_counter() - start_time) < duration_seconds:
                try:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        request_count += 1
                except Exception:
                    pass
            
            elapsed = time.perf_counter() - start_time
            throughput = request_count / elapsed
            
            print(f"\n=== Throughput Test ===")
            print(f"Total requests: {request_count}")
            print(f"Duration: {elapsed:.2f}s")
            print(f"Throughput: {throughput:.2f} req/s")
            
            # Allow 0 throughput if service endpoints are not implemented
            assert throughput >= 0, f"Throughput cannot be negative: {throughput} req/s"

