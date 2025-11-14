"""
Utility functions for prompt template processing.

Includes token counting, validation, and context truncation.
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using rough heuristic.
    
    Rule of thumb: ~4 characters = 1 token for English text.
    This is a conservative estimate that works reasonably well
    for GPT-style tokenizers.
    
    Args:
        text: Input text string
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // 4


def validate_token_limit(text: str, max_tokens: int, context: str = "prompt") -> None:
    """
    Validate that text does not exceed token limit.
    
    Args:
        text: Text to validate
        max_tokens: Maximum allowed tokens
        context: Description of what is being validated (for error messages)
        
    Raises:
        ValueError: If text exceeds max_tokens
    """
    tokens = estimate_tokens(text)
    if tokens > max_tokens:
        raise ValueError(
            f"{context} exceeds token limit: {tokens} tokens > {max_tokens} max. "
            f"Text length: {len(text)} chars. Consider reducing context or chunk size."
        )
    
    logger.debug(f"{context} token count: {tokens}/{max_tokens}")


def truncate_context_documents(
    documents: List[Dict[str, Any]],
    max_tokens: int,
    preserve_first: int = 1
) -> List[Dict[str, Any]]:
    """
    Truncate document list to fit within token budget.
    
    Keeps adding documents until token budget would be exceeded.
    Always preserves at least the first N documents (if they fit).
    
    Args:
        documents: List of document dicts with 'text' and 'doc_id'
        max_tokens: Maximum token budget for all documents
        preserve_first: Number of documents to always include (default: 1)
        
    Returns:
        Truncated list of documents that fit within token budget
    """
    if not documents:
        return []
    
    truncated = []
    total_tokens = 0
    
    for i, doc in enumerate(documents):
        doc_text = doc.get('text', '')
        doc_tokens = estimate_tokens(doc_text)
        
        # Always include first N documents even if they exceed budget
        if i < preserve_first:
            truncated.append(doc)
            total_tokens += doc_tokens
            if total_tokens > max_tokens:
                logger.warning(
                    f"First {preserve_first} document(s) exceed token budget: "
                    f"{total_tokens} > {max_tokens}. Including anyway."
                )
            continue
        
        # Check if adding this document would exceed budget
        if total_tokens + doc_tokens > max_tokens:
            logger.info(
                f"Truncated context at document {i+1}/{len(documents)} "
                f"to stay within {max_tokens} token budget"
            )
            break
        
        truncated.append(doc)
        total_tokens += doc_tokens
    
    logger.info(
        f"Context: {len(truncated)}/{len(documents)} documents, "
        f"~{total_tokens} tokens"
    )
    
    return truncated


def format_citation(doc_id: str, text: str, max_length: int = 500) -> str:
    """
    Format a document as a citation with [Source DOC_ID] prefix.
    
    Args:
        doc_id: Document identifier
        text: Document text content
        max_length: Maximum text length (truncate if longer)
        
    Returns:
        Formatted citation string
    """
    # Truncate text if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return f"[Source {doc_id}] {text}"


def format_citations(documents: List[Dict[str, Any]], max_length: int = 500) -> str:
    """
    Format multiple documents as citations.
    
    Args:
        documents: List of document dicts with 'doc_id' and 'text'
        max_length: Maximum text length per document
        
    Returns:
        Formatted multi-line citation string
    """
    if not documents:
        return "No context documents available."
    
    citations = []
    for doc in documents:
        doc_id = doc.get('doc_id', 'UNKNOWN')
        text = doc.get('text', '')
        citations.append(format_citation(doc_id, text, max_length))
    
    return "\n\n".join(citations)


def build_json_schema(schema_dict: Dict[str, Any], indent: int = 2) -> str:
    """
    Build a readable JSON schema representation for prompts.
    
    Args:
        schema_dict: Schema as Python dict
        indent: Indentation spaces
        
    Returns:
        Formatted JSON schema string
    """
    import json
    return json.dumps(schema_dict, indent=indent)
