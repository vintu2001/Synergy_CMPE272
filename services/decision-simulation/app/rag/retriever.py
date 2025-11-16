"""
RAG Retriever Module

Provides document retrieval functionality from ChromaDB vector store.
Supports building-specific filtering, document type filtering, and metadata enrichment.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer

from app.models.schemas import RetrievalContext


# Configure logging
logger = logging.getLogger(__name__)
log_level = os.getenv("RAG_LOG_LEVEL", "INFO")
logger.setLevel(getattr(logging, log_level))

# Version marker to track code reloads
RETRIEVER_VERSION = "v2.0-with-query-expansion"
logger.info(f"RAG Retriever module loaded - {RETRIEVER_VERSION}")


# Query expansion dictionary for common abbreviations and synonyms
QUERY_EXPANSIONS = {
    "ac": ["air conditioning", "HVAC", "cooling system", "climate control"],
    "hvac": ["heating ventilation air conditioning", "climate control", "AC"],
    "fridge": ["refrigerator", "cooling appliance"],
    "dishwasher": ["dish washer", "dishwashing machine"],
    "washer": ["washing machine", "laundry machine"],
    "dryer": ["drying machine", "laundry dryer"],
    "hot water": ["water heater", "hot water heater"],
    "leak": ["leaking", "water leak", "drip", "dripping"],
    "broken": ["not working", "malfunction", "failure", "damaged"],
    "noisy": ["loud", "noise", "making noise"],
}


class RAGRetriever:
    """
    Retrieves relevant documents from ChromaDB vector store.
    
    Features:
    - Building-specific filtering with global fallback
    - Document type filtering (policy, sop, catalog, sla)
    - Category-based filtering
    - Top-K retrieval with similarity threshold
    - Metadata enrichment
    
    Usage:
        retriever = RAGRetriever()
        context = await retriever.retrieve_relevant_docs(
            query="AC is broken",
            building_id="Building123",
            top_k=5
        )
    """
    
    def __init__(self):
        """Initialize the RAG retriever with embedding model and vector store."""
        logger.info(f"🔄 Initializing RAGRetriever {RETRIEVER_VERSION}")
        
        # Load configuration from environment
        self.enabled = os.getenv("RAG_ENABLED", "false").lower() == "true"
        self.top_k = int(os.getenv("RAG_TOP_K", "5"))
        self.similarity_threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
        self.vector_store_path = os.getenv("VECTOR_STORE_PATH", "./vector_stores/chroma_db")
        self.collection_name = os.getenv("VECTOR_STORE_COLLECTION", "apartment_kb")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.log_retrievals = os.getenv("RAG_LOG_RETRIEVALS", "true").lower() == "true"
        
        # Initialize embedding model
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
        
        # Initialize ChromaDB client
        try:
            logger.info(f"Connecting to ChromaDB at: {self.vector_store_path}")
            self.chroma_client = chromadb.PersistentClient(path=self.vector_store_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            doc_count = self.collection.count()
            logger.info(f"Connected to collection '{self.collection_name}' with {doc_count} documents")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None
    
    def is_available(self) -> bool:
        """
        Check if RAG retriever is available and properly initialized.
        
        Returns:
            bool: True if enabled and all components initialized
        """
        return (
            self.enabled and
            self.embedding_model is not None and
            self.collection is not None
        )
    
    def expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms to improve retrieval.
        
        Args:
            query: Original query string
        
        Returns:
            Expanded query with synonyms
        """
        query_lower = query.lower()
        expanded_terms = [query]  # Always include original query
        
        # Check for expansions
        for abbrev, expansions in QUERY_EXPANSIONS.items():
            if abbrev in query_lower:
                expanded_terms.extend(expansions)
                logger.info(f"✨ Expanded '{abbrev}' with {expansions}")
        
        expanded_query = " ".join(expanded_terms)
        if expanded_query != query:
            logger.info(f"📝 Query expanded: '{query}' → '{expanded_query}'")
        else:
            logger.info(f"📝 Query unchanged: '{query}'")
        
        return expanded_query
    
    async def retrieve_relevant_docs(
        self,
        query: str,
        building_id: Optional[str] = None,
        doc_types: Optional[List[str]] = None,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> Optional[RetrievalContext]:
        """
        Retrieve relevant documents for simulation agent.
        
        Suitable for retrieving policies, SOPs, and catalogs to inform option generation.
        Includes building-specific filtering with global fallback.
        
        Args:
            query: Search query string
            building_id: Building identifier for filtering (e.g., "Building123")
            doc_types: List of document types to retrieve (e.g., ["policy", "sop", "catalog"])
            category: Category filter (e.g., "maintenance", "community")
            top_k: Number of documents to retrieve (overrides default)
            similarity_threshold: Minimum similarity score (overrides default)
        
        Returns:
            RetrievalContext object with retrieved documents, or None if retrieval fails
        """
        if not self.is_available():
            logger.warning("RAG retriever not available, skipping retrieval")
            logger.warning(f"RAG enabled: {self.enabled}, embedding_model: {self.embedding_model is not None}, collection: {self.collection is not None}")
            return None
        
        logger.info(f"RAG retrieval starting: query='{query[:50]}...', category={category}, building_id={building_id}")
        
        # Use provided values or defaults
        k = top_k if top_k is not None else self.top_k
        threshold = similarity_threshold if similarity_threshold is not None else self.similarity_threshold
        
        # Default to retrieving policies, SOPs, and catalogs for simulation
        if doc_types is None:
            doc_types = ["policy", "sop", "catalog", "sla"]  # Include SLAs for maintenance queries
        
        logger.info(f"RAG retrieval params: top_k={k}, threshold={threshold}, doc_types={doc_types}")
        
        try:
            # Expand query with synonyms for better matching
            expanded_query = self.expand_query(query)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(expanded_query).tolist()
            logger.info(f"Generated query embedding with {len(query_embedding)} dimensions")
            
            # Build metadata filters
            filters = self._build_filters(
                building_id=building_id,
                doc_types=doc_types,
                category=category
            )
            
            logger.info(f"RAG filters: {filters}")
            
            # Query vector store
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filters if filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            logger.info(f"RAG query returned {len(results['ids'][0]) if results['ids'] else 0} results")
            
            # Process results
            retrieved_docs = self._process_results(
                results=results,
                similarity_threshold=threshold
            )
            
            logger.info(f"After filtering by threshold {threshold}, {len(retrieved_docs)} documents remain")
            
            # Create retrieval context
            context = RetrievalContext(
                query=query,
                retrieved_docs=retrieved_docs,
                total_retrieved=len(retrieved_docs),
                retrieval_timestamp=datetime.now(),
                retrieval_method="similarity_search"
            )
            
            # Log retrieval
            if self.log_retrievals:
                logger.info(
                    f"Retrieved {len(retrieved_docs)} documents for query: '{query}' "
                    f"(building_id={building_id}, doc_types={doc_types}, "
                    f"avg_score={self._avg_score(retrieved_docs):.3f})"
                )
            
            return context
            
        except Exception as e:
            logger.error(f"Error during document retrieval: {e}", exc_info=True)
            return None
    
    async def retrieve_decision_rules(
        self,
        query: str,
        building_id: Optional[str] = None,
        category: Optional[str] = None,
        urgency: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> Optional[RetrievalContext]:
        """
        Retrieve policy rules and thresholds for decision agent.
        
        Focuses on retrieving policies with decision criteria, thresholds,
        and cost limits to inform decision-making.
        
        Args:
            query: Search query string (e.g., "maintenance policy decision rules")
            building_id: Building identifier for filtering
            category: Category filter (e.g., "maintenance")
            urgency: Urgency level to include in query context
            top_k: Number of documents to retrieve (default: 3 for decision agent)
            similarity_threshold: Minimum similarity score (default: 0.75 for precision)
        
        Returns:
            RetrievalContext object with policy documents, or None if retrieval fails
        """
        if not self.is_available():
            logger.warning("RAG retriever not available, skipping retrieval")
            return None
        
        # Use decision-specific defaults
        k = top_k if top_k is not None else 3  # Fewer docs for decision agent
        threshold = similarity_threshold if similarity_threshold is not None else 0.75  # Higher precision
        
        # Enhance query with context
        enhanced_query = query
        if urgency:
            enhanced_query = f"{query} {urgency} urgency"
        if category:
            enhanced_query = f"{enhanced_query} {category}"
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(enhanced_query).tolist()
            
            # Build metadata filters - policies only for decision rules
            filters = self._build_filters(
                building_id=building_id,
                doc_types=["policy"],  # Only policies for decision rules
                category=category
            )
            
            # Query vector store
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filters if filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            retrieved_docs = self._process_results(
                results=results,
                similarity_threshold=threshold
            )
            
            # Create retrieval context
            context = RetrievalContext(
                query=enhanced_query,
                retrieved_docs=retrieved_docs,
                total_retrieved=len(retrieved_docs),
                retrieval_timestamp=datetime.now(),
                retrieval_method="similarity_search"
            )
            
            # Log retrieval
            if self.log_retrievals:
                logger.info(
                    f"Retrieved {len(retrieved_docs)} policy documents for decision rules "
                    f"(building_id={building_id}, category={category}, "
                    f"avg_score={self._avg_score(retrieved_docs):.3f})"
                )
            
            return context
            
        except Exception as e:
            logger.error(f"Error during decision rule retrieval: {e}", exc_info=True)
            return None
    
    def _build_filters(
        self,
        building_id: Optional[str] = None,
        doc_types: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB metadata filters.
        
        Args:
            building_id: Building identifier (includes global fallback)
            doc_types: List of document types
            category: Category filter
        
        Returns:
            Filter dictionary for ChromaDB query, or None if no filters
        """
        filter_conditions = []
        
        # Building filter with global fallback
        # If no building_id provided, include global documents only
        if building_id:
            filter_conditions.append({
                "building_id": {"$in": [building_id, "all_buildings"]}
            })
        else:
            # No building_id: retrieve global/general documents
            logger.info("No building_id provided, retrieving global documents")
            # Don't add building filter - will retrieve all buildings
        
        # Document type filter
        if doc_types:
            filter_conditions.append({
                "type": {"$in": doc_types}
            })
        
        # Category filter - be flexible with matching
        # Don't filter by category since documents use specific subcategories
        # like "maintenance_request", "maintenance_vendors" vs just "maintenance"
        # The semantic search will handle relevance
        if category:
            logger.info(f"Category '{category}' provided - relying on semantic search for relevance")
            # Note: Could map categories to subcategories if needed in future
            # Semantic search handles this better than strict filtering
        
        # Combine filters with AND logic
        if len(filter_conditions) == 0:
            return None
        elif len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            return {"$and": filter_conditions}
    
    def _process_results(
        self,
        results: Dict[str, Any],
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Process ChromaDB query results into structured format.
        
        Args:
            results: Raw ChromaDB query results
            similarity_threshold: Minimum similarity score to include
        
        Returns:
            List of processed document dictionaries
        """
        processed_docs = []
        
        # ChromaDB returns results as parallel lists
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        for doc_text, metadata, distance in zip(documents, metadatas, distances):
            # Convert distance to similarity score (cosine distance → similarity)
            similarity_score = 1.0 - distance
            
            # Log similarity scores for debugging
            logger.info(f"Document {metadata.get('doc_id', 'unknown')}: similarity={similarity_score:.4f}, category={metadata.get('category', 'unknown')}, type={metadata.get('type', 'unknown')}")
            
            # Filter by threshold
            if similarity_score < similarity_threshold:
                logger.debug(f"Filtered out document {metadata.get('doc_id', 'unknown')} with score {similarity_score:.4f} < threshold {similarity_threshold}")
                continue
            
            # Build document dictionary
            doc_dict = {
                "doc_id": metadata.get("doc_id", "unknown"),
                "text": doc_text,
                "score": round(similarity_score, 4),
                "metadata": {
                    "type": metadata.get("type", "unknown"),
                    "category": metadata.get("category", "unknown"),
                    "building_id": metadata.get("building_id", "unknown"),
                    "version": metadata.get("version", "1.0"),
                    "effective_date": metadata.get("effective_date", ""),
                    "chunk_index": metadata.get("chunk_index", 0)
                }
            }
            
            processed_docs.append(doc_dict)
        
        return processed_docs
    
    def _avg_score(self, docs: List[Dict[str, Any]]) -> float:
        """Calculate average similarity score from retrieved documents."""
        if not docs:
            return 0.0
        scores = [doc.get("score", 0.0) for doc in docs]
        return sum(scores) / len(scores)
    
    def format_context_for_llm(
        self,
        retrieval_context: Optional[RetrievalContext],
        template: str = "default"
    ) -> str:
        """
        Format retrieved documents for LLM prompt injection.
        
        Args:
            retrieval_context: RetrievalContext with retrieved documents
            template: Format template ("default", "detailed", "minimal")
        
        Returns:
            Formatted string ready for LLM prompt
        """
        if not retrieval_context or not retrieval_context.retrieved_docs:
            return ""
        
        if template == "minimal":
            # Just document IDs
            doc_ids = [doc["doc_id"] for doc in retrieval_context.retrieved_docs]
            return f"Relevant documents: {', '.join(doc_ids)}"
        
        elif template == "detailed":
            # Full details with metadata
            formatted = ["KNOWLEDGE BASE CONTEXT:\n"]
            for i, doc in enumerate(retrieval_context.retrieved_docs, 1):
                formatted.append(f"{i}. [{doc['doc_id']}] (score: {doc['score']:.2f})")
                formatted.append(f"   Type: {doc['metadata']['type']}, Category: {doc['metadata']['category']}")
                formatted.append(f"   Content: {doc['text'][:500]}...\n")
            return "\n".join(formatted)
        
        else:  # default
            # Document ID and text
            formatted = ["KNOWLEDGE BASE CONTEXT:\n"]
            for i, doc in enumerate(retrieval_context.retrieved_docs, 1):
                formatted.append(f"{i}. [{doc['doc_id']}]:")
                formatted.append(f"{doc['text']}\n")
            return "\n".join(formatted)


# Global retriever instance
_retriever_instance: Optional[RAGRetriever] = None


def reset_retriever():
    """Reset the global RAGRetriever instance (for testing/reinitialization)."""
    global _retriever_instance
    _retriever_instance = None


def get_retriever() -> RAGRetriever:
    """
    Get or create global RAGRetriever instance (singleton pattern).
    
    Returns:
        RAGRetriever instance
    """
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever()
    return _retriever_instance


# Convenience functions for direct use
async def retrieve_relevant_docs(*args, **kwargs) -> Optional[RetrievalContext]:
    """Convenience wrapper for RAGRetriever.retrieve_relevant_docs()"""
    retriever = get_retriever()
    return await retriever.retrieve_relevant_docs(*args, **kwargs)


async def retrieve_decision_rules(*args, **kwargs) -> Optional[RetrievalContext]:
    """Convenience wrapper for RAGRetriever.retrieve_decision_rules()"""
    retriever = get_retriever()
    return await retriever.retrieve_decision_rules(*args, **kwargs)


async def answer_question(
    question: str,
    building_id: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Answer a resident's question using RAG retrieval and LLM generation.
    
    Args:
        question: The question to answer
        building_id: Optional building ID for context-specific answers
        category: Optional category for filtering relevant documents
        top_k: Number of documents to retrieve
    
    Returns:
        Dict with answer, sources, and confidence
    """
    logger.info(f"Answering question: '{question[:100]}...'")
    
    try:
        # Retrieve relevant documents
        retrieval_context = await retrieve_relevant_docs(
            query=question,
            building_id=building_id,
            category=category,
            top_k=top_k,
            similarity_threshold=0.5  # Lower threshold for questions
        )
        
        # Format context from retrieved documents
        if retrieval_context and retrieval_context.retrieved_docs:
            context_text = "\n\n".join([
                f"[Source {i+1}]: {doc['text']}"
                for i, doc in enumerate(retrieval_context.retrieved_docs)
            ])
        else:
            context_text = None
        
        # Use llm_client to generate answer based on context
        from app.utils.llm_client import llm_client
        
        if not llm_client.enabled:
            logger.error("LLM client not enabled")
            return {
                "answer": "I'm unable to process your question right now. Please try again later or contact the property management office.",
                "source_docs": [],
                "confidence": 0.0
            }
        
        # Generate answer using llm_client
        answer_result = await llm_client.answer_question(
            question=question,
            rag_context=context_text
        )
        
        # If no relevant docs found, return the LLM answer anyway (it will say it doesn't have info)
        source_docs = []
        if retrieval_context and retrieval_context.retrieved_docs:
            source_docs = [
                {
                    "doc_id": doc["doc_id"],
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "score": doc["score"]
                }
                for doc in retrieval_context.retrieved_docs
            ]
        
        return {
            "answer": answer_result.get("answer", "I couldn't generate a proper answer."),
            "source_docs": source_docs,
            "confidence": float(answer_result.get("confidence", 0.5))
        }
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "answer": "I encountered an error while trying to answer your question. Please try rephrasing or contact support.",
            "source_docs": [],
            "confidence": 0.0
        }
