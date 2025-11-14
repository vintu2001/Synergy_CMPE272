"""
Vector Store Factory Module

Provides a single entry point for creating and caching ChromaDB vector store instances.
Ensures process-level singleton pattern to avoid duplicate initialization.

Features:
- Cached vector store instances per (persist_directory, collection_name)
- Cached embeddings model instances per model name
- Health check for collection existence and document count
- Data validation before loading
- Thread-safe cache access
"""

import os
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Tuple, Any

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb

from app.config import get_settings


# Configure logging
settings = get_settings()
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


# Module-level caches for singleton pattern
_vectorstore_cache: Dict[Tuple[str, str], Chroma] = {}
_embeddings_cache: Dict[str, HuggingFaceEmbeddings] = {}
_cache_lock = threading.Lock()


def create_embeddings(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    force_reload: bool = False
) -> HuggingFaceEmbeddings:
    """
    Create or retrieve cached HuggingFaceEmbeddings instance.
    
    Uses singleton pattern to avoid reloading the same model multiple times.
    Thread-safe caching ensures single instance per model name.
    
    Args:
        model_name: HuggingFace model identifier (default: from settings)
        device: Device for inference - 'cpu', 'cuda', or 'mps' (default: from settings)
        force_reload: If True, bypasses cache and creates new instance
        
    Returns:
        HuggingFaceEmbeddings instance (cached if previously loaded)
        
    Example:
        embeddings = create_embeddings()
        embeddings = create_embeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    """
    # Use settings defaults if not provided
    if model_name is None:
        model_name = settings.EMBEDDING_MODEL
    if device is None:
        device = settings.EMBEDDING_DEVICE
    
    # Check cache (thread-safe)
    cache_key = model_name
    if not force_reload:
        with _cache_lock:
            if cache_key in _embeddings_cache:
                logger.debug(f"Using cached embeddings model: {model_name}")
                return _embeddings_cache[cache_key]
    
    # Create new embeddings instance
    logger.info(f"Loading embeddings model: {model_name} (device: {device})")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}  # L2 normalization for cosine similarity
        )
        
        # Cache the instance (thread-safe)
        with _cache_lock:
            _embeddings_cache[cache_key] = embeddings
        
        logger.info(f"Embeddings model loaded successfully: {model_name}")
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to load embeddings model '{model_name}': {e}", exc_info=True)
        raise RuntimeError(f"Cannot initialize embeddings model: {e}") from e


def get_vector_store(
    persist_directory: Optional[str] = None,
    collection_name: Optional[str] = None,
    force_reload: bool = False
) -> Chroma:
    """
    Get or create cached ChromaDB vector store instance.
    
    Main factory function for vector store access. Uses singleton pattern to ensure
    single instance per (persist_directory, collection_name) combination.
    
    If the directory exists with data, loads existing vector store without re-ingestion.
    If the directory doesn't exist, creates it and returns empty vector store.
    
    Args:
        persist_directory: Path to ChromaDB persistence directory (default: from settings)
        collection_name: ChromaDB collection name (default: from settings)
        force_reload: If True, bypasses cache and creates new instance
        
    Returns:
        LangChain Chroma vector store instance (cached if previously loaded)
        
    Raises:
        RuntimeError: If vector store initialization fails
        
    Example:
        # Use default settings
        store = get_vector_store()
        
        # Custom directory/collection
        store = get_vector_store(
            persist_directory="./custom_store",
            collection_name="custom_collection"
        )
        
        # Force reload (bypass cache)
        store = get_vector_store(force_reload=True)
    """
    # Use settings defaults if not provided
    if persist_directory is None:
        persist_directory = settings.PERSIST_DIR
    if collection_name is None:
        collection_name = settings.COLLECTION_NAME
    
    # Resolve to absolute path for consistent caching
    persist_path = Path(persist_directory).resolve()
    persist_directory = str(persist_path)
    
    # Check cache (thread-safe)
    cache_key = (persist_directory, collection_name)
    if not force_reload:
        with _cache_lock:
            if cache_key in _vectorstore_cache:
                logger.debug(
                    f"Using cached vector store: {persist_directory} / {collection_name}"
                )
                return _vectorstore_cache[cache_key]
    
    # Validate directory exists or create it
    if not persist_path.exists():
        logger.warning(
            f"Vector store directory does not exist: {persist_directory}. "
            "Creating empty directory."
        )
        persist_path.mkdir(parents=True, exist_ok=True)
    
    # Check if data exists
    data_exists = validate_vector_store_data(persist_directory)
    if data_exists:
        logger.info(
            f"Loading existing vector store from: {persist_directory} / {collection_name}"
        )
    else:
        logger.warning(
            f"No data found in: {persist_directory}. "
            "Vector store will be empty until ingestion runs."
        )
    
    # Create embeddings function
    embeddings = create_embeddings()
    
    # Create Chroma vector store instance
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
            collection_metadata={"hnsw:space": "cosine"}
        )
        
        # Log document count
        try:
            doc_count = vectorstore._collection.count()
            logger.info(
                f"Vector store initialized: {doc_count} documents in '{collection_name}'"
            )
        except Exception as e:
            logger.warning(f"Could not retrieve document count: {e}")
        
        # Cache the instance (thread-safe)
        with _cache_lock:
            _vectorstore_cache[cache_key] = vectorstore
        
        return vectorstore
        
    except Exception as e:
        logger.error(
            f"Failed to initialize vector store at '{persist_directory}': {e}",
            exc_info=True
        )
        raise RuntimeError(f"Cannot initialize vector store: {e}") from e


def health_check(
    persist_directory: Optional[str] = None,
    collection_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform health check on vector store.
    
    Validates that the collection exists and reports document count.
    Useful for monitoring, startup checks, and troubleshooting.
    
    Args:
        persist_directory: Path to ChromaDB directory (default: from settings)
        collection_name: Collection name (default: from settings)
        
    Returns:
        dict: Health status with the following fields:
            - status: "healthy" or "unhealthy"
            - collection_exists: bool
            - document_count: int (0 if collection doesn't exist)
            - persist_directory: str
            - collection_name: str
            - error: str or None (error message if unhealthy)
            
    Example:
        health = health_check()
        if health["status"] == "healthy":
            print(f"Vector store has {health['document_count']} documents")
        else:
            print(f"Error: {health['error']}")
    """
    # Use settings defaults
    if persist_directory is None:
        persist_directory = settings.PERSIST_DIR
    if collection_name is None:
        collection_name = settings.COLLECTION_NAME
    
    result = {
        "status": "unhealthy",
        "collection_exists": False,
        "document_count": 0,
        "persist_directory": persist_directory,
        "collection_name": collection_name,
        "error": None
    }
    
    try:
        # Check if directory exists
        persist_path = Path(persist_directory)
        if not persist_path.exists():
            result["error"] = f"Directory does not exist: {persist_directory}"
            logger.warning(result["error"])
            return result
        
        # Check if data exists
        if not validate_vector_store_data(persist_directory):
            result["error"] = f"No ChromaDB data found in: {persist_directory}"
            logger.warning(result["error"])
            return result
        
        # Try to connect and get collection
        client = chromadb.PersistentClient(path=persist_directory)
        
        # Check if collection exists
        try:
            collection = client.get_collection(name=collection_name)
            result["collection_exists"] = True
            
            # Get document count
            doc_count = collection.count()
            result["document_count"] = doc_count
            
            # Status is healthy if we got this far
            result["status"] = "healthy"
            
            logger.info(
                f"Health check PASSED: {collection_name} has {doc_count} documents"
            )
            
        except Exception as e:
            result["error"] = f"Collection '{collection_name}' not found: {str(e)}"
            logger.warning(result["error"])
            return result
        
    except Exception as e:
        result["error"] = f"Health check failed: {str(e)}"
        logger.error(result["error"], exc_info=True)
        return result
    
    return result


def validate_vector_store_data(persist_directory: Optional[str] = None) -> bool:
    """
    Validate that vector store data exists in the directory.
    
    Checks for ChromaDB files (chroma.sqlite3) and metadata folders.
    Does not validate data integrity, only presence.
    
    Args:
        persist_directory: Path to ChromaDB directory (default: from settings)
        
    Returns:
        bool: True if data exists, False otherwise
        
    Example:
        if validate_vector_store_data("./vector_stores/chroma_db"):
            print("Data exists, can load vector store")
        else:
            print("No data found, need to run ingestion")
    """
    if persist_directory is None:
        persist_directory = settings.PERSIST_DIR
    
    persist_path = Path(persist_directory)
    
    # Check if directory exists
    if not persist_path.exists():
        logger.debug(f"Directory does not exist: {persist_directory}")
        return False
    
    # Check for chroma.sqlite3 file
    db_file = persist_path / "chroma.sqlite3"
    if not db_file.exists():
        logger.debug(f"ChromaDB database file not found: {db_file}")
        return False
    
    # Check file is non-empty
    if db_file.stat().st_size == 0:
        logger.debug(f"ChromaDB database file is empty: {db_file}")
        return False
    
    logger.debug(f"Vector store data exists at: {persist_directory}")
    return True


def clear_cache() -> None:
    """
    Clear all cached vector store and embeddings instances.
    
    Forces next call to get_vector_store() or create_embeddings() to create
    new instances. Useful for testing or when you need to force reload.
    
    Thread-safe operation.
    
    Example:
        # Clear cache to force reload
        clear_cache()
        store = get_vector_store()  # Creates new instance
    """
    with _cache_lock:
        cleared_stores = len(_vectorstore_cache)
        cleared_embeddings = len(_embeddings_cache)
        
        _vectorstore_cache.clear()
        _embeddings_cache.clear()
        
        logger.info(
            f"Cache cleared: {cleared_stores} vector stores, "
            f"{cleared_embeddings} embeddings models"
        )


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about cached instances.
    
    Returns:
        dict: Cache statistics with keys:
            - vectorstore_count: Number of cached vector stores
            - embeddings_count: Number of cached embeddings models
            - vectorstore_keys: List of (persist_dir, collection_name) tuples
            - embeddings_keys: List of model names
            
    Example:
        stats = get_cache_stats()
        print(f"Cached vector stores: {stats['vectorstore_count']}")
    """
    with _cache_lock:
        return {
            "vectorstore_count": len(_vectorstore_cache),
            "embeddings_count": len(_embeddings_cache),
            "vectorstore_keys": list(_vectorstore_cache.keys()),
            "embeddings_keys": list(_embeddings_cache.keys())
        }
