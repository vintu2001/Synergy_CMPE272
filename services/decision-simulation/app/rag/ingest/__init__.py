"""
Knowledge Base Ingestion Module
Handles loading, chunking, and embedding documents into vector stores.
"""

from .loader import DocumentLoader
from .chunker import DocumentChunker
from .embedder import EmbeddingGenerator

__all__ = ["DocumentLoader", "DocumentChunker", "EmbeddingGenerator"]
