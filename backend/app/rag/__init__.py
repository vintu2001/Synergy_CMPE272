"""
RAG (Retrieval-Augmented Generation) Module
Provides knowledge base retrieval and context injection for agents.
"""

from .retriever import (
    RAGRetriever,
    get_retriever,
    retrieve_for_simulation,
    retrieve_for_decision
)

from .vector_store import (
    get_vector_store,
    create_embeddings,
    health_check,
    validate_vector_store_data,
    clear_cache,
    get_cache_stats
)

__all__ = [
    # Retriever
    "RAGRetriever",
    "get_retriever",
    "retrieve_for_simulation",
    "retrieve_for_decision",
    # Vector Store Factory
    "get_vector_store",
    "create_embeddings",
    "health_check",
    "validate_vector_store_data",
    "clear_cache",
    "get_cache_stats"
]
