"""
RAG (Retrieval-Augmented Generation) Module
Provides knowledge base retrieval and context injection for agents.
"""

from .retriever import (
    RAGRetriever,
    get_retriever,
    retrieve_relevant_docs,
    retrieve_decision_rules
)

__all__ = [
    "RAGRetriever",
    "get_retriever",
    "retrieve_relevant_docs",
    "retrieve_decision_rules"
]
