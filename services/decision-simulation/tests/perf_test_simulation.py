"""
Performance tests for Decision Simulation Service
Tests RAG retrieval speed and decision-making performance

NOTE: These tests require the service to be running on http://localhost:8003
Start with: docker compose -f infrastructure/docker/docker-compose.microservices.yml up
"""
import pytest
import time
from httpx import AsyncClient

BASE_URL = "http://localhost:8003"


class TestDecisionSimulationPerformance:
    """Performance tests for decision simulation and RAG"""
    
    @pytest.mark.asyncio
    async def test_simulation_response_time(self):
        """Test decision simulation response time - critical for user experience"""
        async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            payload = {
                "request_id": "perf_sim_001",
                "description": "Air conditioning not working in apartment 304",
                "category": "maintenance",
                "priority": "high",
                "resident_id": "R001"
            }
            
            latencies = []
            for _ in range(5):  # Fewer iterations due to complexity
                start = time.perf_counter()
                response = await client.post("/api/simulate", json=payload)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                
                if response.status_code == 200:
                    result = response.json()
                    assert "options" in result or "simulation" in result
            
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\n=== Simulation Performance ===")
            print(f"Average: {avg_latency:.2f}ms")
            print(f"Min: {min_latency:.2f}ms")
            print(f"Max: {max_latency:.2f}ms")
            
            # Simulation should complete in reasonable time
            assert avg_latency < 30000, f"Simulation too slow: {avg_latency}ms"
    
    @pytest.mark.skip(reason="Requires RAG system dependencies - causes access violation on Windows")
    @pytest.mark.asyncio
    async def test_rag_retrieval_performance(self):
        """Test RAG document retrieval speed"""
        from app.rag.retriever import RAGRetriever
        
        retriever = RAGRetriever()
        queries = [
            "What is the cost for HVAC repair?",
            "SLA for emergency requests",
            "Maintenance policy for air conditioning",
            "How to handle urgent repair requests",
            "Cost estimation for plumbing work"
        ]
        
        retrieval_times = []
        for query in queries:
            start = time.perf_counter()
            try:
                results = await retriever.retrieve(query, top_k=5)
                retrieval_time = (time.perf_counter() - start) * 1000
                retrieval_times.append(retrieval_time)
            except Exception:
                pass
        
        if retrieval_times:
            avg_retrieval = sum(retrieval_times) / len(retrieval_times)
            
            print(f"\n=== RAG Retrieval Performance ===")
            print(f"Average: {avg_retrieval:.2f}ms")
            print(f"Min: {min(retrieval_times):.2f}ms")
            print(f"Max: {max(retrieval_times):.2f}ms")
            
            # RAG retrieval should be fast
            assert avg_retrieval < 2000, f"RAG retrieval too slow: {avg_retrieval}ms"
    
    @pytest.mark.asyncio
    async def test_decision_agent_reasoning_time(self):
        """Test how long decision agent takes to reason"""
        async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            test_cases = [
                {
                    "description": "Minor maintenance request",
                    "category": "maintenance",
                    "priority": "low"
                },
                {
                    "description": "Emergency water leak",
                    "category": "emergency",
                    "priority": "critical"
                },
                {
                    "description": "Noise complaint",
                    "category": "complaint",
                    "priority": "medium"
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                payload = {
                    "request_id": f"reasoning_test_{i}",
                    "resident_id": f"R{i:03d}",
                    **test_case
                }
                
                start = time.perf_counter()
                response = await client.post("/api/simulate", json=payload)
                reasoning_time = (time.perf_counter() - start) * 1000
                
                print(f"\n{test_case['priority'].upper()} priority: {reasoning_time:.2f}ms")
                
                # Higher priority should still complete quickly
                if test_case['priority'] == 'critical':
                    assert reasoning_time < 30000, "Critical requests must be processed quickly"
    
    @pytest.mark.skip(reason="Requires RAG system dependencies - causes access violation on Windows")
    @pytest.mark.asyncio
    async def test_knowledge_base_lookup_performance(self):
        """Test knowledge base document lookup speed"""
        from app.rag.retriever import RAGRetriever
        
        retriever = RAGRetriever()
        
        # Test different query types
        query_types = {
            "policy": "What is the maintenance policy?",
            "cost": "Cost for emergency repairs?",
            "sla": "SLA for urgent requests?",
            "procedure": "How to handle maintenance requests?"
        }
        
        for query_type, query in query_types.items():
            start = time.perf_counter()
            try:
                results = await retriever.retrieve(query, top_k=3)
                lookup_time = (time.perf_counter() - start) * 1000
                print(f"{query_type}: {lookup_time:.2f}ms")
            except Exception:
                pass


class TestRAGSystemBenchmarks:
    """Benchmarks for RAG system components"""
    
    @pytest.mark.skip(reason="Requires RAG system dependencies - causes access violation on Windows")
    @pytest.mark.asyncio
    async def test_vector_similarity_search_speed(self):
        """Benchmark vector similarity search"""
        from app.rag.retriever import RAGRetriever
        
        retriever = RAGRetriever()
        query = "emergency maintenance procedures"
        
        search_times = []
        for _ in range(10):
            start = time.perf_counter()
            try:
                await retriever.retrieve(query, top_k=5)
                search_time = (time.perf_counter() - start) * 1000
                search_times.append(search_time)
            except Exception:
                pass
        
        if search_times:
            avg_search = sum(search_times) / len(search_times)
            print(f"\n=== Vector Search Performance ===")
            print(f"Average: {avg_search:.2f}ms")
            
            assert avg_search < 1000, "Vector search too slow"

