"""
Pytest configuration and shared fixtures for RAG tests.
"""
import pytest
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    original_env = {}
    test_vars = {
        "RAG_ENABLED": "true",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
        "VECTOR_STORE_TYPE": "chromadb",
        "VECTOR_STORE_PATH": "./tests/fixtures/test_vector_store",
        "RAG_TOP_K": "5",
        "RAG_SIMILARITY_THRESHOLD": "0.7",
        "RAG_MAX_CONTEXT_LENGTH": "2000",
        "KB_PATH": "./tests/fixtures/kb",
    }
    
    # Save original values and set test values
    for key, value in test_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(scope="session")
def sample_documents():
    """Load sample KB documents for testing."""
    from tests.fixtures.sample_documents import get_all_sample_documents
    return get_all_sample_documents()


@pytest.fixture(scope="session")
def sample_policies():
    """Load sample policy documents."""
    from tests.fixtures.sample_documents import get_documents_by_type
    return get_documents_by_type("policy")


@pytest.fixture(scope="session")
def sample_sops():
    """Load sample SOP documents."""
    from tests.fixtures.sample_documents import get_documents_by_type
    return get_documents_by_type("sop")


@pytest.fixture(scope="session")
def test_queries():
    """Load test queries with expected results."""
    from tests.fixtures.sample_documents import get_all_test_queries
    return get_all_test_queries()


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model that returns deterministic vectors."""
    class MockEmbeddingModel:
        def encode(self, texts, show_progress_bar=False):
            """Return mock embeddings (384D like all-MiniLM-L6-v2)."""
            import numpy as np
            if isinstance(texts, str):
                texts = [texts]
            # Generate deterministic embeddings based on text hash
            embeddings = []
            for text in texts:
                # Use hash for determinism
                seed = hash(text) % (2**32)
                np.random.seed(seed)
                embedding = np.random.randn(384).astype('float32')
                # Normalize to unit length (like real embeddings)
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
            return np.array(embeddings)
    
    return MockEmbeddingModel()


@pytest.fixture
def test_vector_store(tmp_path):
    """Create a temporary vector store for testing."""
    import shutil
    vector_store_path = tmp_path / "test_chroma_db"
    vector_store_path.mkdir(exist_ok=True)
    
    yield str(vector_store_path)
    
    # Cleanup
    if vector_store_path.exists():
        shutil.rmtree(vector_store_path)


@pytest.fixture
def populated_vector_store(test_vector_store, sample_documents, mock_embedding_model):
    """Create a vector store pre-populated with sample documents."""
    import chromadb
    from chromadb.config import Settings
    
    # Create ChromaDB client
    client = chromadb.PersistentClient(
        path=test_vector_store,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Create collection
    collection = client.get_or_create_collection(
        name="test_apartment_kb",
        metadata={"description": "Test knowledge base"}
    )
    
    # Add documents
    for doc in sample_documents:
        doc_id = doc["doc_id"]
        text = doc["text"]
        metadata = {
            "type": doc["type"],
            "category": doc["category"],
            "building_id": doc["building_id"],
            "title": doc["title"]
        }
        
        # Generate embedding
        embedding = mock_embedding_model.encode(text)[0].tolist()
        
        # Add to collection
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    return {
        "client": client,
        "collection": collection,
        "path": test_vector_store,
        "doc_count": len(sample_documents)
    }
