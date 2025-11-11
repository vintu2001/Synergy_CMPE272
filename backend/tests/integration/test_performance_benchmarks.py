"""
Performance benchmarks for RAG operations.
Tests embedding generation, vector search, and end-to-end retrieval performance.
"""
import pytest
import time
import statistics
from typing import List


class TestEmbeddingPerformance:
    """Benchmark embedding generation performance."""
    
    def test_single_embedding_latency(self, mock_embedding_model):
        """Measure latency for single embedding generation."""
        text = "Test embedding generation latency"
        
        latencies = []
        for _ in range(10):
            start = time.time()
            _ = mock_embedding_model.encode(text)
            latency = (time.time() - start) * 1000  # Convert to ms
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        print(f"\nSingle Embedding:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        
        # Mock should be very fast
        assert avg_latency < 50  # Less than 50ms average
    
    def test_batch_embedding_throughput(self, mock_embedding_model):
        """Measure throughput for batch embedding generation."""
        texts = ["Test sentence"] * 100
        
        start = time.time()
        embeddings = mock_embedding_model.encode(texts)
        elapsed = time.time() - start
        
        throughput = len(texts) / elapsed
        
        print(f"\nBatch Embedding (100 texts):")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.1f} texts/second")
        
        assert len(embeddings) == 100
        # Mock should process quickly
        assert throughput > 100  # At least 100 texts/second


class TestVectorSearchPerformance:
    """Benchmark vector search performance."""
    
    def test_single_query_latency(self, populated_vector_store, mock_embedding_model):
        """Measure latency for single similarity search."""
        collection = populated_vector_store["collection"]
        query = "test search performance"
        query_embedding = mock_embedding_model.encode(query)[0].tolist()
        
        latencies = []
        for _ in range(20):
            start = time.time()
            _ = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            latency = (time.time() - start) * 1000  # Convert to ms
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]
        
        print(f"\nVector Search (single query):")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  Document count: {populated_vector_store['doc_count']}")
        
        # Should be fast for small dataset
        assert avg_latency < 100  # Less than 100ms average
    
    def test_batch_query_performance(self, populated_vector_store, mock_embedding_model):
        """Measure performance for batch queries."""
        collection = populated_vector_store["collection"]
        
        queries = [
            "noise complaint",
            "maintenance request",
            "parking issue",
            "emergency situation",
            "billing question"
        ]
        
        query_embeddings = [
            mock_embedding_model.encode(q)[0].tolist()
            for q in queries
        ]
        
        start = time.time()
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=3
        )
        elapsed = time.time() - start
        
        queries_per_second = len(queries) / elapsed
        
        print(f"\nBatch Vector Search ({len(queries)} queries):")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Queries/second: {queries_per_second:.1f}")
        print(f"  Avg per query: {(elapsed/len(queries))*1000:.2f}ms")
        
        assert len(results["ids"]) == len(queries)
        assert queries_per_second > 5  # At least 5 queries/second
    
    def test_search_with_filters_performance(self, populated_vector_store, mock_embedding_model):
        """Measure performance impact of metadata filtering."""
        collection = populated_vector_store["collection"]
        query = "policy search"
        query_embedding = mock_embedding_model.encode(query)[0].tolist()
        
        # Without filter
        start = time.time()
        results_no_filter = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        time_no_filter = (time.time() - start) * 1000
        
        # With filter
        start = time.time()
        results_with_filter = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where={"type": "policy"}
        )
        time_with_filter = (time.time() - start) * 1000
        
        print(f"\nSearch Performance Comparison:")
        print(f"  No filter: {time_no_filter:.2f}ms")
        print(f"  With filter: {time_with_filter:.2f}ms")
        print(f"  Overhead: {time_with_filter - time_no_filter:.2f}ms")
        
        # Both should be fast
        assert time_no_filter < 100
        assert time_with_filter < 150


class TestEndToEndRAGPerformance:
    """Benchmark complete RAG retrieval pipeline."""
    
    def test_full_retrieval_pipeline(self, populated_vector_store, mock_embedding_model):
        """Measure end-to-end retrieval latency."""
        collection = populated_vector_store["collection"]
        
        test_cases = [
            {
                "query": "noise complaint at night",
                "building_id": "TestBuilding1",
                "doc_types": ["policy", "sop"]
            },
            {
                "query": "HVAC emergency high temperature",
                "building_id": "all_buildings",
                "doc_types": ["policy", "sop", "catalog"]
            },
            {
                "query": "parking violation towing",
                "building_id": "TestBuilding1",
                "doc_types": ["policy"]
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            start = time.time()
            
            # Step 1: Generate embedding
            query_embedding = mock_embedding_model.encode(test_case["query"])[0].tolist()
            
            # Step 2: Search with filters
            search_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={
                    "$and": [
                        {"building_id": {"$in": [test_case["building_id"], "all_buildings"]}},
                        {"type": {"$in": test_case["doc_types"]}}
                    ]
                }
            )
            
            # Step 3: Build retrieval context (simulate)
            retrieved_docs = [
                {
                    "doc_id": doc_id,
                    "text": doc_text,
                    "score": 0.9  # Would be actual distance in real implementation
                }
                for doc_id, doc_text in zip(
                    search_results["ids"][0],
                    search_results["documents"][0]
                )
            ]
            
            elapsed = (time.time() - start) * 1000
            
            results.append({
                "query": test_case["query"][:30] + "...",
                "latency_ms": elapsed,
                "docs_retrieved": len(retrieved_docs)
            })
        
        # Print results
        print("\nEnd-to-End RAG Pipeline:")
        for r in results:
            print(f"  Query: {r['query']}")
            print(f"    Latency: {r['latency_ms']:.2f}ms")
            print(f"    Docs: {r['docs_retrieved']}")
        
        avg_latency = statistics.mean([r["latency_ms"] for r in results])
        print(f"  Average latency: {avg_latency:.2f}ms")
        
        # Full pipeline should complete in < 200ms
        assert avg_latency < 200
        assert all(r["docs_retrieved"] > 0 for r in results)


class TestScalabilityProjections:
    """Project performance at scale."""
    
    def test_project_large_dataset_performance(self, test_vector_store, mock_embedding_model):
        """Project performance with larger document count."""
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=test_vector_store,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_or_create_collection(name="scale_test")
        
        # Add progressively more documents and measure search time
        doc_counts = [10, 50, 100]
        search_times = []
        
        for target_count in doc_counts:
            # Add documents to reach target count
            current_count = collection.count()
            docs_to_add = target_count - current_count
            
            if docs_to_add > 0:
                for i in range(docs_to_add):
                    doc_id = f"doc_{current_count + i}"
                    text = f"Document {current_count + i} content for testing scalability"
                    embedding = mock_embedding_model.encode(text)[0].tolist()
                    
                    collection.add(
                        ids=[doc_id],
                        embeddings=[embedding],
                        documents=[text],
                        metadatas=[{"index": current_count + i}]
                    )
            
            # Measure search time
            query = "test search scalability"
            query_embedding = mock_embedding_model.encode(query)[0].tolist()
            
            start = time.time()
            _ = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            search_time = (time.time() - start) * 1000
            
            search_times.append(search_time)
        
        print("\nScalability Projection:")
        for count, time_ms in zip(doc_counts, search_times):
            print(f"  {count} docs: {time_ms:.2f}ms")
        
        # Project to 1000 docs (linear extrapolation - conservative)
        if len(search_times) >= 2:
            rate = (search_times[-1] - search_times[0]) / (doc_counts[-1] - doc_counts[0])
            projected_1000 = search_times[-1] + rate * (1000 - doc_counts[-1])
            print(f"  1000 docs (projected): {projected_1000:.2f}ms")
            
            # Should still be reasonable at scale
            assert projected_1000 < 500  # Less than 500ms projected
        
        del client


class TestMemoryUsage:
    """Test memory efficiency of RAG operations."""
    
    def test_embedding_memory_footprint(self, mock_embedding_model):
        """Estimate memory usage for embeddings."""
        import sys
        
        # Single embedding
        text = "Test memory usage"
        embedding = mock_embedding_model.encode(text)[0]
        
        # Size in bytes
        embedding_size = embedding.nbytes
        
        print(f"\nMemory Usage:")
        print(f"  Single embedding (384D float32): {embedding_size} bytes")
        print(f"  1000 embeddings: {embedding_size * 1000 / 1024:.2f} KB")
        print(f"  10000 embeddings: {embedding_size * 10000 / 1024 / 1024:.2f} MB")
        
        # 384D float32 should be 384 * 4 = 1536 bytes
        assert embedding_size == 384 * 4
    
    def test_vector_store_disk_usage(self, populated_vector_store):
        """Measure disk usage of vector store."""
        import os
        from pathlib import Path
        
        store_path = Path(populated_vector_store["path"])
        
        # Calculate total size
        total_size = sum(
            f.stat().st_size
            for f in store_path.rglob("*")
            if f.is_file()
        )
        
        doc_count = populated_vector_store["doc_count"]
        size_per_doc = total_size / doc_count if doc_count > 0 else 0
        
        print(f"\nVector Store Disk Usage:")
        print(f"  Total size: {total_size / 1024:.2f} KB")
        print(f"  Document count: {doc_count}")
        print(f"  Size per document: {size_per_doc / 1024:.2f} KB")
        print(f"  Projected 1000 docs: {size_per_doc * 1000 / 1024 / 1024:.2f} MB")
        
        # Should be reasonable
        assert size_per_doc < 50 * 1024  # Less than 50KB per doc
