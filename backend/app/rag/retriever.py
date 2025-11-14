"""
RAG Retriever Module

Provides document retrieval functionality from ChromaDB vector store.
Supports building-specific filtering, document type filtering, and metadata enrichment.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.schemas import RetrievalContext
from app.config import get_settings
from app.rag.vector_store import get_vector_store


# Configure logging
settings = get_settings()
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


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
        # Load configuration from centralized settings
        settings = get_settings()
        self.enabled = settings.RAG_ENABLED
        self.top_k = settings.RETRIEVAL_K
        self.similarity_threshold = settings.SIMILARITY_CUTOFF
        self.vector_store_path = settings.PERSIST_DIR
        self.collection_name = settings.COLLECTION_NAME
        self.embedding_model_name = settings.EMBEDDING_MODEL
        self.log_retrievals = True  # Always log retrievals in production
        
        # Get vector store from factory (cached, includes embeddings)
        try:
            logger.info(f"Initializing vector store from factory")
            self.vectorstore = get_vector_store(
                persist_directory=self.vector_store_path,
                collection_name=self.collection_name
            )
            doc_count = self.vectorstore._collection.count()
            logger.info(
                f"Vector store initialized: {doc_count} documents in '{self.collection_name}'"
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.vectorstore = None
    
    def is_available(self) -> bool:
        """
        Check if RAG retriever is available and properly initialized.
        
        Returns:
            bool: True if enabled and all components initialized
        """
        return (
            self.enabled and
            self.vectorstore is not None
        )
    
    async def retrieve_for_simulation(
        self,
        issue_text: str,
        building_id: Optional[str] = None,
        category: Optional[str] = None,
        doc_types: Optional[List[str]] = None,
        k: Optional[int] = None,
        fetch_k: Optional[int] = None,
        lambda_mult: Optional[float] = None,
        similarity_threshold: Optional[float] = None
    ) -> Optional[RetrievalContext]:
        """
        Retrieve documents for simulation agent using MMR for diversity.
        
        Uses Maximal Marginal Relevance (MMR) to balance relevance and diversity
        in retrieved documents. This helps the simulation agent generate varied
        options by exposing it to diverse policy/SOP/cost information.
        
        Args:
            issue_text: Issue description or query text
            building_id: Building identifier for filtering
            category: Category filter (e.g., "maintenance", "community")
            doc_types: Document types to retrieve (default: ["policy", "sop", "cost"])
            k: Number of final documents to return (default: RETRIEVAL_K)
            fetch_k: Number of candidates to fetch before MMR (default: FETCH_K)
            lambda_mult: MMR diversity parameter 0-1 (default: LAMBDA_MULT)
                        0.0 = max diversity, 1.0 = max similarity, 0.5 = balanced
            similarity_threshold: Minimum similarity score (default: SIMILARITY_CUTOFF)
        
        Returns:
            RetrievalContext with retrieved documents, or None if unavailable
            Returns empty context (not None) if zero results
        
        Example:
            context = await retriever.retrieve_for_simulation(
                issue_text="AC unit not cooling properly",
                building_id="building_a",
                category="maintenance",
                k=5
            )
        """
        if not self.is_available():
            logger.warning("RAG retriever not available, skipping retrieval")
            return None
        
        # Use provided values or defaults
        k = k if k is not None else self.top_k
        settings = get_settings()
        fetch_k = fetch_k if fetch_k is not None else settings.FETCH_K
        lambda_mult = lambda_mult if lambda_mult is not None else settings.LAMBDA_MULT
        threshold = similarity_threshold if similarity_threshold is not None else self.similarity_threshold
        
        # Default document types for simulation
        if doc_types is None:
            doc_types = ["policy", "sop", "cost"]
        
        try:
            # Build metadata filters
            filters = self._build_filters(
                building_id=building_id,
                doc_types=doc_types,
                category=category
            )
            
            # Create MMR retriever
            search_kwargs = {
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult
            }
            if filters:
                search_kwargs["filter"] = filters
            
            retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs=search_kwargs
            )
            
            # Invoke retriever (returns List[Document])
            documents = retriever.invoke(issue_text)
            
            # Process MMR results
            retrieved_docs = self._process_mmr_results(
                documents=documents,
                similarity_threshold=threshold
            )
            
            # Verify MMR diversity
            diversity_info = self._verify_mmr_diversity(retrieved_docs)
            
            # Handle zero results
            if len(retrieved_docs) == 0:
                return self._handle_zero_results(
                    query=issue_text,
                    filters=filters,
                    context_type="simulation"
                )
            
            # Create retrieval context
            context = RetrievalContext(
                query=issue_text,
                retrieved_docs=retrieved_docs,
                total_retrieved=len(retrieved_docs),
                retrieval_timestamp=datetime.now(),
                retrieval_method="mmr"
            )
            
            # Log retrieval with MMR info
            if self.log_retrievals:
                logger.info(
                    f"[MMR Simulation] Retrieved {len(retrieved_docs)} documents for: '{issue_text}' "
                    f"(building_id={building_id}, category={category}, types={doc_types}, "
                    f"k={k}, fetch_k={fetch_k}, lambda={lambda_mult:.2f}, "
                    f"diversity={diversity_info['unique_docs']}/{len(retrieved_docs)}, "
                    f"avg_score={self._avg_score(retrieved_docs):.3f})"
                )
            
            return context
            
        except Exception as e:
            logger.error(f"Error during simulation retrieval: {e}", exc_info=True)
            return None
    
    async def retrieve_for_decision(
        self,
        query: str,
        building_id: Optional[str] = None,
        category: Optional[str] = None,
        doc_types: Optional[List[str]] = None,
        k: Optional[int] = None,
        fetch_k: Optional[int] = None,
        lambda_mult: Optional[float] = None,
        similarity_threshold: Optional[float] = None
    ) -> Optional[RetrievalContext]:
        """
        Retrieve documents for decision agent using MMR for diversity.
        
        Uses Maximal Marginal Relevance (MMR) to retrieve policy rules, SLAs,
        and scoring criteria for decision-making. Uses higher precision threshold
        and fewer documents than simulation retrieval.
        
        Args:
            query: Decision context or query text
            building_id: Building identifier for filtering
            category: Category filter (e.g., "maintenance", "community")
            doc_types: Document types to retrieve (default: ["policy", "sla", "scoring"])
            k: Number of final documents to return (default: 3, fewer for decision)
            fetch_k: Number of candidates to fetch before MMR (default: FETCH_K)
            lambda_mult: MMR diversity parameter 0-1 (default: LAMBDA_MULT)
                        0.0 = max diversity, 1.0 = max similarity, 0.5 = balanced
            similarity_threshold: Minimum similarity score (default: 0.75, higher precision)
        
        Returns:
            RetrievalContext with retrieved documents, or None if unavailable
            Returns empty context (not None) if zero results
        
        Example:
            context = await retriever.retrieve_for_decision(
                query="maintenance decision rules high urgency",
                building_id="building_a",
                category="maintenance"
            )
        """
        if not self.is_available():
            logger.warning("RAG retriever not available, skipping retrieval")
            return None
        
        # Use provided values or decision-specific defaults
        k = k if k is not None else 3  # Fewer documents for decision (vs 5 for simulation)
        settings = get_settings()
        fetch_k = fetch_k if fetch_k is not None else settings.FETCH_K
        lambda_mult = lambda_mult if lambda_mult is not None else settings.LAMBDA_MULT
        threshold = similarity_threshold if similarity_threshold is not None else 0.75  # Higher precision
        
        # Default document types for decision
        if doc_types is None:
            doc_types = ["policy", "sla", "scoring"]
        
        try:
            # Build metadata filters
            filters = self._build_filters(
                building_id=building_id,
                doc_types=doc_types,
                category=category
            )
            
            # Create MMR retriever
            search_kwargs = {
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult
            }
            if filters:
                search_kwargs["filter"] = filters
            
            retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs=search_kwargs
            )
            
            # Invoke retriever (returns List[Document])
            documents = retriever.invoke(query)
            
            # Process MMR results
            retrieved_docs = self._process_mmr_results(
                documents=documents,
                similarity_threshold=threshold
            )
            
            # Verify MMR diversity
            diversity_info = self._verify_mmr_diversity(retrieved_docs)
            
            # Handle zero results
            if len(retrieved_docs) == 0:
                return self._handle_zero_results(
                    query=query,
                    filters=filters,
                    context_type="decision"
                )
            
            # Create retrieval context
            context = RetrievalContext(
                query=query,
                retrieved_docs=retrieved_docs,
                total_retrieved=len(retrieved_docs),
                retrieval_timestamp=datetime.now(),
                retrieval_method="mmr"
            )
            
            # Log retrieval with MMR info
            if self.log_retrievals:
                logger.info(
                    f"[MMR Decision] Retrieved {len(retrieved_docs)} documents for: '{query}' "
                    f"(building_id={building_id}, category={category}, types={doc_types}, "
                    f"k={k}, fetch_k={fetch_k}, lambda={lambda_mult:.2f}, "
                    f"diversity={diversity_info['unique_docs']}/{len(retrieved_docs)}, "
                    f"avg_score={self._avg_score(retrieved_docs):.3f})"
                )
            
            return context
            
        except Exception as e:
            logger.error(f"Error during decision retrieval: {e}", exc_info=True)
            return None
    
    def _map_category_to_kb(self, category: str) -> List[str]:
        """
        Map classification category to KB document categories.
        
        Classification uses simplified categories (Maintenance, Billing, etc.)
        while KB documents use more specific categories (maintenance_request, etc.)
        
        Args:
            category: Classification category
            
        Returns:
            List of KB document categories that match
        """
        category_lower = category.lower()
        
        # Map classification categories to KB document categories
        category_mapping = {
            'maintenance': ['maintenance_request'],
            'billing': ['rent_payment'],
            'security': ['security_access'],
            'deliveries': ['package_delivery'],
            'amenities': ['pool_amenity', 'common_area'],
            'community': ['community_rules', 'noise_complaint'],
            'parking': ['parking_complaint'],
            'pets': ['pet_complaint'],
            'guests': ['guest_policy'],
            'lease': ['lease_violation', 'subletting'],
            'moving': ['move_in_out'],
            'smoking': ['smoking']
        }
        
        # Return mapped categories or original if no mapping found
        return category_mapping.get(category_lower, [category_lower])
    
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
        if building_id:
            filter_conditions.append({
                "building_id": {"$in": [building_id, "all_buildings"]}
            })
        
        # Document type filter
        if doc_types:
            filter_conditions.append({
                "type": {"$in": doc_types}
            })
        
        # Category filter with mapping
        if category:
            # Map classification category to KB document categories
            kb_categories = self._map_category_to_kb(category)
            if len(kb_categories) == 1:
                filter_conditions.append({
                    "category": {"$eq": kb_categories[0]}
                })
            else:
                # Multiple possible categories, use $in
                filter_conditions.append({
                    "category": {"$in": kb_categories}
                })
        
        # Combine filters with AND logic
        if len(filter_conditions) == 0:
            return None
        elif len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            return {"$and": filter_conditions}
    
    def _process_langchain_results(
        self,
        results: List[Tuple[Any, float]],
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Process LangChain query results into structured format.
        
        LangChain returns list of (Document, distance_score) tuples where:
        - Document has .page_content (text) and .metadata (dict)
        - distance_score is cosine distance (lower = more similar)
        
        Args:
            results: List of (Document, distance) tuples from LangChain
            similarity_threshold: Minimum similarity score to include
        
        Returns:
            List of processed document dictionaries
        """
        processed_docs = []
        
        for doc, distance in results:
            # Convert distance to similarity score (cosine distance → similarity)
            # LangChain uses cosine distance where 0 = identical, 2 = opposite
            similarity_score = 1.0 - (distance / 2.0)  # Normalize to 0-1 range
            
            # Filter by threshold
            if similarity_score < similarity_threshold:
                continue
            
            # Build document dictionary
            metadata = doc.metadata
            doc_dict = {
                "doc_id": metadata.get("doc_id", "unknown"),
                "text": doc.page_content,
                "score": round(similarity_score, 4),
                "metadata": {
                    "type": metadata.get("type", "unknown"),
                    "category": metadata.get("category", "unknown"),
                    "building_id": metadata.get("building_id", "unknown"),
                    "version": metadata.get("version", "1.0"),
                    "effective_date": metadata.get("effective_date", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "chunk_id": metadata.get("chunk_id", ""),
                    "total_chunks": metadata.get("total_chunks", 1)
                }
            }
            
            processed_docs.append(doc_dict)
        
        return processed_docs
    
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
            
            # Filter by threshold
            if similarity_score < similarity_threshold:
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
    
    def _process_mmr_results(
        self,
        documents: List[Any],
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Process MMR retriever results into structured format.
        
        MMR retriever returns List[Document] without scores.
        We convert to our standard format with estimated relevance.
        
        Args:
            documents: List of Document objects from MMR retriever
            similarity_threshold: Minimum threshold (note: MMR docs don't have scores)
        
        Returns:
            List of processed document dictionaries
        """
        processed_docs = []
        
        for i, doc in enumerate(documents):
            # MMR doesn't return scores, estimate based on rank
            # Higher rank = higher estimated relevance
            estimated_score = 1.0 - (i * 0.1)  # Decay by rank
            estimated_score = max(estimated_score, similarity_threshold)
            
            # Build document dictionary
            metadata = doc.metadata
            doc_dict = {
                "doc_id": metadata.get("doc_id", "unknown"),
                "text": doc.page_content,
                "score": round(estimated_score, 4),
                "metadata": {
                    "type": metadata.get("type", "unknown"),
                    "category": metadata.get("category", "unknown"),
                    "building_id": metadata.get("building_id", "unknown"),
                    "version": metadata.get("version", "1.0"),
                    "effective_date": metadata.get("effective_date", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "chunk_id": metadata.get("chunk_id", ""),
                    "total_chunks": metadata.get("total_chunks", 1)
                }
            }
            
            processed_docs.append(doc_dict)
        
        return processed_docs
    
    def _verify_mmr_diversity(
        self,
        retrieved_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify MMR diversity by checking unique document IDs.
        
        MMR should provide diverse results. This verifies that top-k
        contains at least 2 different document IDs when possible.
        
        Args:
            retrieved_docs: List of retrieved document dictionaries
        
        Returns:
            dict with diversity metrics:
                - unique_docs: number of unique doc_ids
                - total_docs: total number of documents
                - diversity_ratio: unique/total
                - has_diversity: True if >=2 unique docs
        """
        if not retrieved_docs:
            return {
                "unique_docs": 0,
                "total_docs": 0,
                "diversity_ratio": 0.0,
                "has_diversity": False
            }
        
        # Extract unique doc_ids (ignoring chunk suffixes)
        doc_ids = [doc["doc_id"].split("_chunk_")[0] for doc in retrieved_docs]
        unique_doc_ids = set(doc_ids)
        
        total = len(retrieved_docs)
        unique = len(unique_doc_ids)
        ratio = unique / total if total > 0 else 0.0
        has_diversity = unique >= 2
        
        return {
            "unique_docs": unique,
            "total_docs": total,
            "diversity_ratio": round(ratio, 2),
            "has_diversity": has_diversity
        }
    
    def _handle_zero_results(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        context_type: str
    ) -> RetrievalContext:
        """
        Handle zero-result scenarios with proper fallback behavior.
        
        When no documents match the query+filters, return an empty
        RetrievalContext (not None) with escalation indicator.
        
        Args:
            query: Original query text
            filters: Filters that were applied
            context_type: "simulation" or "decision"
        
        Returns:
            Empty RetrievalContext with escalation metadata
        """
        logger.warning(
            f"Zero results for {context_type} retrieval: query='{query}', filters={filters}"
        )
        
        # Return empty context with escalation flag
        return RetrievalContext(
            query=query,
            retrieved_docs=[],
            total_retrieved=0,
            retrieval_timestamp=datetime.now(),
            retrieval_method="mmr_no_results"
        )
    
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


# Convenience functions for direct use with new MMR-based retrieval
async def retrieve_for_simulation(*args, **kwargs) -> Optional[RetrievalContext]:
    """Convenience wrapper for RAGRetriever.retrieve_for_simulation()"""
    retriever = get_retriever()
    return await retriever.retrieve_for_simulation(*args, **kwargs)


async def retrieve_for_decision(*args, **kwargs) -> Optional[RetrievalContext]:
    """Convenience wrapper for RAGRetriever.retrieve_for_decision()"""
    retriever = get_retriever()
    return await retriever.retrieve_for_decision(*args, **kwargs)

