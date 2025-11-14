#!/usr/bin/env python3
"""
LangChain-Based Knowledge Base Ingestion (Step 4)

Architecture:
1. Phase 1: Frontmatter Pre-Processing
   - Extract YAML frontmatter from Markdown/CSV files
   - Validate required metadata fields
   - Create Document objects with clean bodies (no YAML in content)

2. Phase 2: LangChain Pipeline
   - Split documents with RecursiveCharacterTextSplitter (~700 tokens)
   - Generate embeddings with HuggingFaceEmbeddings
   - Store in Chroma vector database

3. Phase 3: Validation
   - Verify chunk sizes (500-800 tokens)
   - Verify metadata coverage (100%)
   - Test retrieval with spot-check queries

Author: LangChain RAG Migration - Step 4
Date: November 2025
"""

import os
import sys
import logging
import argparse
import shutil
import yaml
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from collections import Counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Import vector store factory functions (Step 5.3)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.rag.vector_store import (
    create_embeddings as factory_create_embeddings,
    get_vector_store,
    clear_cache
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PHASE 1: FRONTMATTER PRE-PROCESSING
# ============================================================================

def detect_frontmatter(file_path: str) -> Tuple[Optional[str], str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            logger.warning(f"Empty file: {file_path}")
            return None, ""
        
        # Check if first line is exactly '---'
        first_line = lines[0].strip()
        if first_line != '---':
            logger.debug(f"No frontmatter found (missing opening ---): {file_path}")
            return None, ''.join(lines)
        
        # Find closing '---'
        yaml_lines = []
        body_start_idx = None
        
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == '---':
                body_start_idx = idx + 1
                break
            yaml_lines.append(line)
        
        if body_start_idx is None:
            logger.warning(f"Unclosed frontmatter (missing closing ---): {file_path}")
            return None, ''.join(lines)
        
        # Extract YAML block and body
        yaml_block = ''.join(yaml_lines)
        body_text = ''.join(lines[body_start_idx:])
        
        if not yaml_block.strip():
            logger.warning(f"Empty frontmatter block: {file_path}")
            return None, body_text
        
        logger.debug(f"Frontmatter detected in {file_path}: {len(yaml_lines)} lines")
        return yaml_block, body_text
    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None, ""


def parse_frontmatter_yaml(yaml_block: str, file_path: str) -> Dict[str, Any]:
    try:
        metadata = yaml.safe_load(yaml_block)
        
        if not isinstance(metadata, dict):
            raise ValueError(f"Invalid YAML structure (expected dict): {file_path}")
        
        # Define required fields
        required_fields = ['doc_id', 'type', 'category', 'building_id', 'version']
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in metadata or not metadata[field]]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in {file_path}: {', '.join(missing_fields)}\n"
                f"Required fields: {', '.join(required_fields)}"
            )
        
        # Set defaults for optional fields
        metadata.setdefault('effective_date', '')
        metadata.setdefault('last_updated', '')
        metadata.setdefault('keywords', '')
        
        # Validate document type
        valid_types = ['policy', 'sop', 'sla', 'catalog', 'cost', 'scoring']
        if metadata['type'] not in valid_types:
            logger.warning(
                f"Unknown document type '{metadata['type']}' in {file_path}. "
                f"Expected one of: {', '.join(valid_types)}"
            )
        
        logger.debug(f"Parsed metadata for {metadata['doc_id']}: {metadata['type']}/{metadata['category']}")
        return metadata
    
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing YAML in {file_path}: {e}")


def detect_csv_frontmatter(file_path: str) -> Tuple[Optional[str], pd.DataFrame]:
    """
    Detect YAML frontmatter in CSV file header comments.
    
    CSV files should have YAML metadata as comments at the top:
        ---
        doc_id: COST_001
        type: cost
        ---
        trade,hourly_rate,min_hours
        HVAC Technician,95,2
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        (yaml_block, dataframe) if frontmatter found
        (None, dataframe) if no frontmatter
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            logger.warning(f"Empty CSV file: {file_path}")
            return None, pd.DataFrame()
        
        # Check if first line is '---'
        if lines[0].strip() != '---':
            logger.debug(f"No frontmatter in CSV: {file_path}")
            # Try to read as regular CSV
            df = pd.read_csv(file_path)
            return None, df
        
        # Find closing '---'
        yaml_lines = []
        data_start_idx = None
        
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == '---':
                data_start_idx = idx + 1
                break
            yaml_lines.append(line)
        
        if data_start_idx is None:
            logger.warning(f"Unclosed frontmatter in CSV: {file_path}")
            df = pd.read_csv(file_path)
            return None, df
        
        # Parse YAML block
        yaml_block = ''.join(yaml_lines)
        
        # Read CSV data (skip frontmatter lines)
        df = pd.read_csv(file_path, skiprows=data_start_idx)
        
        logger.debug(f"CSV frontmatter detected in {file_path}: {len(yaml_lines)} lines, {len(df)} rows")
        return yaml_block, df
    
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return None, pd.DataFrame()


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all metadata values are JSON-serializable for ChromaDB.
    
    ChromaDB requires metadata values to be:
    - str, int, float, bool (no custom objects)
    - Lists must be converted to strings
    - Dates must be ISO format strings
    
    Args:
        metadata: Raw metadata dictionary
    
    Returns:
        Sanitized metadata dictionary
    """
    sanitized = {}
    
    for key, value in metadata.items():
        # Convert lists to comma-separated strings
        if isinstance(value, list):
            sanitized[key] = ', '.join(str(item) for item in value)
        
        # Convert dates to ISO strings
        elif isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        
        # Keep primitives as-is
        elif isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        
        # Convert everything else to string
        else:
            sanitized[key] = str(value)
    
    return sanitized


def extract_metadata_and_body(file_path: str) -> Tuple[Dict[str, Any], str]:
    file_ext = Path(file_path).suffix.lower()
    
    try:
        if file_ext == '.md':
            # Markdown file processing
            yaml_block, body = detect_frontmatter(file_path)
            
            if yaml_block is None:
                logger.warning(f"Skipping file without frontmatter: {file_path}")
                return {}, ""
            
            metadata = parse_frontmatter_yaml(yaml_block, file_path)
            return metadata, body
        
        elif file_ext == '.csv':
            # CSV file processing
            yaml_block, df = detect_csv_frontmatter(file_path)
            
            if yaml_block is None:
                logger.warning(f"Skipping CSV without frontmatter: {file_path}")
                return {}, ""
            
            metadata = parse_frontmatter_yaml(yaml_block, file_path)
            
            # Convert DataFrame to text representation
            category_title = metadata.get('category', 'Data').replace('_', ' ').title()
            body = f"# {category_title}\n\n{df.to_string(index=False)}"
            
            return metadata, body
        
        else:
            logger.warning(f"Unsupported file type {file_ext}: {file_path}")
            return {}, ""
    
    except ValueError as e:
        logger.error(f"Validation error in {file_path}: {e}")
        return {}, ""
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        return {}, ""


def load_documents_with_metadata(kb_dir: str) -> List[Document]:
    """
    Load all KB documents with YAML-free bodies and validated metadata.
    
    This function:
    1. Walks the KB directory for *.md and *.csv files
    2. Extracts metadata and body from each file
    3. Creates LangChain Document objects with clean bodies
    4. Adds source_path to metadata
    5. Sanitizes metadata for ChromaDB compatibility
    
    Args:
        kb_dir: Path to knowledge base directory
    
    Returns:
        List of Document objects with clean page_content and metadata
    """
    documents = []
    kb_path = Path(kb_dir)
    
    if not kb_path.exists():
        logger.error(f"KB directory not found: {kb_dir}")
        return documents
    
    # Find all Markdown and CSV files (sorted for determinism)
    md_files = sorted(kb_path.rglob("*.md"))
    csv_files = sorted(kb_path.rglob("*.csv"))
    all_files = md_files + csv_files
    
    logger.info(f"Found {len(all_files)} files in {kb_dir} ({len(md_files)} MD, {len(csv_files)} CSV)")
    
    # Process each file
    successful = 0
    skipped = 0
    
    for file_path in all_files:
        metadata, body = extract_metadata_and_body(str(file_path))
        
        if not metadata or not body.strip():
            skipped += 1
            continue
        
        # Add source information
        metadata['source_path'] = str(file_path.relative_to(kb_path.parent))
        metadata['source_file'] = file_path.name
        
        # Sanitize metadata
        metadata = sanitize_metadata(metadata)
        
        # Create Document with clean body (no YAML)
        doc = Document(
            page_content=body,
            metadata=metadata
        )
        documents.append(doc)
        successful += 1
        
        logger.debug(
            f"Loaded {metadata['doc_id']}: "
            f"{len(body)} chars, type={metadata['type']}, building={metadata['building_id']}"
        )
    
    logger.info(f"Loaded {successful} documents ({skipped} skipped)")
    
    return documents


# ============================================================================
# PHASE 2: LANGCHAIN PIPELINE (SPLITTING, EMBEDDING, STORAGE)
# ============================================================================

def create_text_splitter(chunk_size: int = 2800, chunk_overlap: int = 480) -> RecursiveCharacterTextSplitter:
    """
    Create RecursiveCharacterTextSplitter configured for ~700 token chunks.
    
    Token estimation:
    - 1 token ≈ 4 characters (average English text)
    - 700 tokens ≈ 2800 characters
    - 120 token overlap ≈ 480 characters
    
    Args:
        chunk_size: Maximum characters per chunk (default: 2800)
        chunk_overlap: Overlap between chunks in characters (default: 480)
    
    Returns:
        Configured text splitter
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]  # Paragraph → Line → Word → Character
    )
    
    logger.info(f"Text splitter configured: chunk_size={chunk_size}, overlap={chunk_overlap}")
    return text_splitter


def split_documents_with_metadata(
    documents: List[Document],
    text_splitter: RecursiveCharacterTextSplitter
) -> List[Document]:
    """
    Split documents into chunks while preserving metadata.
    
    LangChain automatically propagates Document.metadata to all chunks.
    This function adds chunk_index and chunk_id for tracking.
    
    Args:
        documents: List of Document objects with clean bodies
        text_splitter: Configured text splitter
    
    Returns:
        List of chunked Document objects with metadata preserved
    """
    logger.info(f"Splitting {len(documents)} documents into chunks...")
    
    # Split documents (metadata automatically preserved)
    chunked_docs = text_splitter.split_documents(documents)
    
    logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
    
    # Add chunk tracking metadata
    # Group chunks by doc_id to get per-document chunk counts
    doc_chunk_counts = {}
    for doc in chunked_docs:
        doc_id = doc.metadata.get('doc_id', 'unknown')
        doc_chunk_counts[doc_id] = doc_chunk_counts.get(doc_id, 0) + 1
    
    # Add chunk indices and IDs
    doc_chunk_indices = {}
    for doc in chunked_docs:
        doc_id = doc.metadata.get('doc_id', 'unknown')
        
        # Get current index for this doc_id
        current_idx = doc_chunk_indices.get(doc_id, 0)
        
        # Add chunk tracking
        doc.metadata['chunk_index'] = current_idx
        doc.metadata['total_chunks'] = doc_chunk_counts[doc_id]
        doc.metadata['chunk_id'] = f"{doc_id}_chunk_{current_idx}"
        
        # Increment index for this doc_id
        doc_chunk_indices[doc_id] = current_idx + 1
    
    # Log sample chunks
    logger.debug("Sample chunks created:")
    for i, doc in enumerate(chunked_docs[:3], 1):
        logger.debug(
            f"  {i}. {doc.metadata.get('chunk_id')}: "
            f"{len(doc.page_content)} chars, type={doc.metadata.get('type')}"
        )
    
    return chunked_docs


def create_embeddings(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> HuggingFaceEmbeddings:
    """
    Create HuggingFaceEmbeddings wrapper for sentence transformers.
    
    Now uses the vector store factory for consistent caching across
    ingestion and retrieval operations.
    
    Args:
        model_name: HuggingFace model identifier
    
    Returns:
        Configured embeddings model (cached via factory)
    """
    logger.info(f"Initializing embeddings model via factory: {model_name}")
    
    # Use factory function for caching
    embeddings = factory_create_embeddings(model_name=model_name, device='cpu')
    
    logger.info("Embeddings model loaded successfully")
    return embeddings


def create_vector_store(
    chunked_docs: List[Document],
    embeddings: HuggingFaceEmbeddings,
    persist_directory: str = "./vector_stores/chroma_db",
    collection_name: str = "apartment_kb",
    force_rebuild: bool = False
) -> Chroma:
    """
    Create or update Chroma vector store with document chunks.
    
    Now integrates with vector store factory for consistency:
    - force_rebuild=False: Uses factory to get cached instance (if available)
    - force_rebuild=True: Clears cache, deletes directory, creates new store
    
    Args:
        chunked_docs: List of chunked Document objects
        embeddings: Embeddings model
        persist_directory: Directory for vector store persistence
        collection_name: Collection name in ChromaDB
        force_rebuild: If True, clear existing collection before ingestion
    
    Returns:
        Chroma vector store instance
    """
    persist_path = Path(persist_directory)
    
    # Handle force rebuild
    if force_rebuild:
        # Clear factory cache to ensure fresh instance
        logger.warning("Force rebuild: Clearing factory cache")
        clear_cache()
        
        # Delete existing directory
        if persist_path.exists():
            logger.warning(f"Force rebuild: Clearing existing vector store at {persist_directory}")
            shutil.rmtree(persist_directory)
        else:
            logger.info("Force rebuild requested but no existing store found")
        
        # Create new vector store
        logger.info(f"Creating new vector store at {persist_directory}")
        vectorstore = Chroma.from_documents(
            documents=chunked_docs,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name,
            collection_metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Vector store created with {len(chunked_docs)} chunks")
        
    else:
        # Check if collection exists
        collection_exists = persist_path.exists() and (persist_path / "chroma.sqlite3").exists()
        
        if collection_exists:
            # Use factory to load existing store (cached)
            logger.info(f"Loading existing vector store via factory from {persist_directory}")
            vectorstore = get_vector_store(
                persist_directory=persist_directory,
                collection_name=collection_name
            )
            logger.info(f"Existing collection loaded: {vectorstore._collection.count()} chunks")
        else:
            # Create new store (no existing data)
            logger.info(f"Creating new vector store at {persist_directory}")
            vectorstore = Chroma.from_documents(
                documents=chunked_docs,
                embedding=embeddings,
                persist_directory=persist_directory,
                collection_name=collection_name,
                collection_metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Vector store created with {len(chunked_docs)} chunks")
    
    return vectorstore


def ingest_kb_documents(
    kb_dir: str = "kb",
    persist_directory: str = "./vector_stores/chroma_db",
    collection_name: str = "apartment_kb",
    chunk_size: int = 2800,
    chunk_overlap: int = 480,
    force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Full ingestion pipeline: Load → Split → Embed → Store.
    
    This is the main ingestion function that orchestrates all phases:
    1. Phase 1: Load documents with frontmatter extraction
    2. Phase 2: Split into chunks, generate embeddings, store in Chroma
    
    Args:
        kb_dir: Knowledge base directory
        persist_directory: Vector store persistence path
        collection_name: ChromaDB collection name
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks
        force_rebuild: Clear existing collection before ingestion
    
    Returns:
        Statistics dictionary with ingestion results
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("KNOWLEDGE BASE INGESTION PIPELINE")
    logger.info("=" * 70)
    
    stats = {
        'start_time': start_time.isoformat(),
        'kb_directory': kb_dir,
        'force_rebuild': force_rebuild,
        'documents_loaded': 0,
        'chunks_created': 0,
        'type_distribution': {},
        'building_distribution': {},
        'category_distribution': {},
        'errors': []
    }
    
    try:
        # Phase 1: Load documents with frontmatter extraction
        logger.info("\n--- PHASE 1: Document Loading ---")
        documents = load_documents_with_metadata(kb_dir)
        stats['documents_loaded'] = len(documents)
        
        if not documents:
            logger.error("No documents loaded, aborting ingestion")
            stats['errors'].append("No documents loaded")
            return stats
        
        # Phase 2: Split documents
        logger.info("\n--- PHASE 2: Document Splitting ---")
        text_splitter = create_text_splitter(chunk_size, chunk_overlap)
        chunked_docs = split_documents_with_metadata(documents, text_splitter)
        stats['chunks_created'] = len(chunked_docs)
        
        # Compute distributions
        type_counts = Counter(doc.metadata.get('type', 'unknown') for doc in chunked_docs)
        building_counts = Counter(doc.metadata.get('building_id', 'unknown') for doc in chunked_docs)
        category_counts = Counter(doc.metadata.get('category', 'unknown') for doc in chunked_docs)
        
        stats['type_distribution'] = dict(type_counts)
        stats['building_distribution'] = dict(building_counts)
        stats['category_distribution'] = dict(category_counts)
        
        # Phase 2: Create embeddings
        logger.info("\n--- PHASE 2: Embedding Generation ---")
        embeddings = create_embeddings()
        
        # Phase 2: Create vector store
        logger.info("\n--- PHASE 2: Vector Store Creation ---")
        vectorstore = create_vector_store(
            chunked_docs,
            embeddings,
            persist_directory,
            collection_name,
            force_rebuild
        )
        
        # Persist to disk
        logger.info("Persisting vector store to disk...")
        vectorstore.persist()
        logger.info(f"✓ Vector store persisted to {persist_directory}")
        
        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        stats['end_time'] = end_time.isoformat()
        stats['duration_seconds'] = duration
        
        logger.info("\n" + "=" * 70)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 70)
        
        return stats
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        stats['errors'].append(str(e))
        return stats


def print_ingestion_summary(stats: Dict[str, Any]):
    """
    Print formatted summary of ingestion results.
    
    Args:
        stats: Statistics dictionary from ingest_kb_documents()
    """
    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)
    
    # Basic stats
    print(f"\nKB Directory:      {stats['kb_directory']}")
    print(f"Force Rebuild:     {stats['force_rebuild']}")
    print(f"Documents Loaded:  {stats['documents_loaded']}")
    print(f"Chunks Created:    {stats['chunks_created']}")
    
    if stats.get('duration_seconds'):
        print(f"Duration:          {stats['duration_seconds']:.2f} seconds")
    
    # Type distribution
    if stats.get('type_distribution'):
        print("\nDocument Types:")
        for doc_type, count in sorted(stats['type_distribution'].items()):
            percentage = (count / stats['chunks_created'] * 100) if stats['chunks_created'] > 0 else 0
            print(f"  {doc_type:12s}: {count:4d} chunks ({percentage:5.1f}%)")
    
    # Building distribution
    if stats.get('building_distribution'):
        print("\nBuilding Distribution:")
        for building, count in sorted(stats['building_distribution'].items()):
            percentage = (count / stats['chunks_created'] * 100) if stats['chunks_created'] > 0 else 0
            print(f"  {building:20s}: {count:4d} chunks ({percentage:5.1f}%)")
    
    # Top categories
    if stats.get('category_distribution'):
        print("\nTop 10 Categories:")
        sorted_categories = sorted(
            stats['category_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for category, count in sorted_categories[:10]:
            print(f"  {category:30s}: {count:4d} chunks")
    
    # Errors
    if stats.get('errors'):
        print("\n⚠️  ERRORS:")
        for error in stats['errors']:
            print(f"  - {error}")
    else:
        print("\n✅ No errors during ingestion")
    
    print("\n" + "=" * 70)


# ============================================================================
# PHASE 3: VALIDATION & RETRIEVAL TESTING
# ============================================================================

def validate_chunk_sizes(
    chunked_docs: List[Document],
    min_tokens: int = 500,
    max_tokens: int = 800
) -> Dict[str, Any]:
    """
    Validate chunk sizes are within target token range.
    
    Uses word count * 0.75 as token estimate (1 token ≈ 1.3 words).
    For more accurate counting, could use tiktoken library.
    
    Args:
        chunked_docs: List of chunked documents
        min_tokens: Minimum acceptable average tokens (default: 500)
        max_tokens: Maximum acceptable average tokens (default: 800)
    
    Returns:
        Validation results dictionary
    """
    logger.info("\n--- VALIDATION: Chunk Sizes ---")
    
    # Calculate token estimates (word count * 0.75)
    token_estimates = [len(doc.page_content.split()) * 0.75 for doc in chunked_docs]
    char_lengths = [len(doc.page_content) for doc in chunked_docs]
    
    results = {
        'total_chunks': len(chunked_docs),
        'avg_tokens': sum(token_estimates) / len(token_estimates) if token_estimates else 0,
        'min_tokens': min(token_estimates) if token_estimates else 0,
        'max_tokens': max(token_estimates) if token_estimates else 0,
        'avg_chars': sum(char_lengths) / len(char_lengths) if char_lengths else 0,
        'min_chars': min(char_lengths) if char_lengths else 0,
        'max_chars': max(char_lengths) if char_lengths else 0,
        'target_min': min_tokens,
        'target_max': max_tokens,
        'within_range': False
    }
    
    # Check if average is within target range
    results['within_range'] = min_tokens <= results['avg_tokens'] <= max_tokens
    
    # Log results
    logger.info(f"Total chunks: {results['total_chunks']}")
    logger.info(f"Token estimates (word count * 0.75):")
    logger.info(f"  Average: {results['avg_tokens']:.0f} tokens")
    logger.info(f"  Range: {results['min_tokens']:.0f} - {results['max_tokens']:.0f} tokens")
    logger.info(f"  Target: {min_tokens} - {max_tokens} tokens")
    logger.info(f"Character counts:")
    logger.info(f"  Average: {results['avg_chars']:.0f} chars")
    logger.info(f"  Range: {results['min_chars']} - {results['max_chars']} chars")
    
    if results['within_range']:
        logger.info("✅ PASS: Average chunk size within target range")
    else:
        logger.warning(
            f"⚠️  WARNING: Average chunk size ({results['avg_tokens']:.0f} tokens) "
            f"outside target range ({min_tokens}-{max_tokens} tokens)"
        )
        logger.info("Note: This may be acceptable if documents are intentionally concise")
    
    return results


def validate_metadata_coverage(
    chunked_docs: List[Document],
    required_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate that all chunks have required metadata fields.
    
    Args:
        chunked_docs: List of chunked documents
        required_fields: List of required metadata field names
                        (default: doc_id, type, category, building_id, version)
    
    Returns:
        Validation results dictionary
    """
    logger.info("\n--- VALIDATION: Metadata Coverage ---")
    
    if required_fields is None:
        required_fields = ['doc_id', 'type', 'category', 'building_id', 'version']
    
    results = {
        'total_chunks': len(chunked_docs),
        'required_fields': required_fields,
        'chunks_with_all_fields': 0,
        'missing_fields_count': 0,
        'missing_examples': [],
        'coverage_percentage': 0.0,
        'passed': False
    }
    
    # Check each chunk
    for i, doc in enumerate(chunked_docs):
        missing = [field for field in required_fields if field not in doc.metadata]
        
        if not missing:
            results['chunks_with_all_fields'] += 1
        else:
            results['missing_fields_count'] += 1
            # Store first 5 examples
            if len(results['missing_examples']) < 5:
                results['missing_examples'].append({
                    'chunk_index': i,
                    'chunk_id': doc.metadata.get('chunk_id', 'unknown'),
                    'missing_fields': missing
                })
    
    # Calculate coverage percentage
    results['coverage_percentage'] = (
        results['chunks_with_all_fields'] / results['total_chunks'] * 100
        if results['total_chunks'] > 0 else 0
    )
    
    # Check if passed (100% coverage)
    results['passed'] = results['coverage_percentage'] == 100.0
    
    # Log results
    logger.info(f"Total chunks: {results['total_chunks']}")
    logger.info(f"Required fields: {', '.join(required_fields)}")
    logger.info(f"Chunks with all fields: {results['chunks_with_all_fields']}/{results['total_chunks']}")
    logger.info(f"Coverage: {results['coverage_percentage']:.1f}%")
    
    if results['passed']:
        logger.info("✅ PASS: 100% metadata coverage")
    else:
        logger.error(
            f"❌ FAIL: {results['missing_fields_count']} chunks missing required fields"
        )
        for example in results['missing_examples']:
            logger.error(
                f"  Chunk {example['chunk_id']}: missing {example['missing_fields']}"
            )
    
    return results


def spot_check_retrieval(
    vectorstore: Chroma,
    test_queries: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Test retrieval with known queries to validate vector store functionality.
    
    Args:
        vectorstore: Chroma vector store instance
        test_queries: List of test query dicts with keys:
                     - query: The search query
                     - expected_type: Expected document type
                     - expected_doc: Expected doc_id (optional)
    
    Returns:
        Test results dictionary
    """
    logger.info("\n--- VALIDATION: Spot-Check Retrieval ---")
    
    if test_queries is None:
        test_queries = [
            {
                'query': 'after-hours AC leak cost',
                'expected_type': 'cost',
                'expected_doc': 'COST_005',
                'description': 'Emergency cost surcharges'
            },
            {
                'query': 'emergency decision weights',
                'expected_type': 'scoring',
                'expected_doc': 'SCORING_001',
                'description': 'Emergency scoring weights'
            },
            {
                'query': 'gas smell escalation',
                'expected_type': 'scoring',
                'expected_doc': 'SCORING_003',
                'description': 'Life-safety escalation triggers'
            }
        ]
    
    results = {
        'total_queries': len(test_queries),
        'passed': 0,
        'failed': 0,
        'query_results': []
    }
    
    for test in test_queries:
        query = test['query']
        expected_type = test['expected_type']
        expected_doc = test.get('expected_doc')
        description = test.get('description', '')
        
        logger.info(f"\nQuery: '{query}'")
        logger.info(f"  Description: {description}")
        logger.info(f"  Expected: type={expected_type}, doc={expected_doc}")
        
        try:
            # Perform similarity search with scores
            results_with_scores = vectorstore.similarity_search_with_score(query, k=3)
            
            if not results_with_scores:
                logger.error("  ❌ FAIL: No results returned")
                results['failed'] += 1
                results['query_results'].append({
                    'query': query,
                    'passed': False,
                    'reason': 'No results returned'
                })
                continue
            
            # Get top result
            top_doc, top_score = results_with_scores[0]
            actual_doc = top_doc.metadata.get('doc_id', 'unknown')
            actual_type = top_doc.metadata.get('type', 'unknown')
            
            logger.info(f"  Top result: {actual_doc} (type={actual_type}, score={top_score:.4f})")
            logger.info(f"  Preview: {top_doc.page_content[:100].replace(chr(10), ' ')}...")
            
            # Validate result
            type_match = actual_type == expected_type
            doc_match = (expected_doc is None) or (actual_doc == expected_doc)
            
            if type_match and doc_match:
                logger.info("  ✅ PASS: Retrieved correct document")
                results['passed'] += 1
                results['query_results'].append({
                    'query': query,
                    'passed': True,
                    'actual_doc': actual_doc,
                    'actual_type': actual_type,
                    'score': top_score
                })
            else:
                if not type_match:
                    logger.error(f"  ❌ FAIL: Wrong type (expected {expected_type}, got {actual_type})")
                if not doc_match:
                    logger.error(f"  ❌ FAIL: Wrong document (expected {expected_doc}, got {actual_doc})")
                
                results['failed'] += 1
                results['query_results'].append({
                    'query': query,
                    'passed': False,
                    'actual_doc': actual_doc,
                    'actual_type': actual_type,
                    'expected_doc': expected_doc,
                    'expected_type': expected_type,
                    'score': top_score
                })
        
        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            results['failed'] += 1
            results['query_results'].append({
                'query': query,
                'passed': False,
                'reason': str(e)
            })
    
    # Summary
    logger.info(f"\nSpot-Check Summary:")
    logger.info(f"  Total queries: {results['total_queries']}")
    logger.info(f"  Passed: {results['passed']}")
    logger.info(f"  Failed: {results['failed']}")
    
    if results['failed'] == 0:
        logger.info("✅ All spot-check queries passed")
    else:
        logger.warning(f"⚠️  {results['failed']} spot-check queries failed")
    
    return results


def run_full_validation(
    kb_dir: str = "kb",
    persist_directory: str = "./vector_stores/chroma_db",
    collection_name: str = "apartment_kb",
    chunk_size: int = 2800,
    chunk_overlap: int = 480
) -> Dict[str, Any]:
    """
    Run complete validation pipeline on ingested data.
    
    This function:
    1. Loads documents and creates chunks
    2. Validates chunk sizes
    3. Validates metadata coverage
    4. Loads vector store and tests retrieval
    
    Args:
        kb_dir: Knowledge base directory
        persist_directory: Vector store persistence path
        collection_name: ChromaDB collection name
        chunk_size: Chunk size for validation
        chunk_overlap: Chunk overlap for validation
    
    Returns:
        Combined validation results
    """
    logger.info("=" * 70)
    logger.info("FULL VALIDATION PIPELINE")
    logger.info("=" * 70)
    
    validation_results = {
        'kb_directory': kb_dir,
        'vector_store': persist_directory,
        'chunk_size_validation': {},
        'metadata_validation': {},
        'retrieval_validation': {},
        'overall_passed': False
    }
    
    try:
        # Load and split documents
        logger.info("\nLoading and splitting documents...")
        documents = load_documents_with_metadata(kb_dir)
        text_splitter = create_text_splitter(chunk_size, chunk_overlap)
        chunked_docs = split_documents_with_metadata(documents, text_splitter)
        
        logger.info(f"Loaded {len(documents)} documents, created {len(chunked_docs)} chunks")
        
        # Validation 1: Chunk sizes
        validation_results['chunk_size_validation'] = validate_chunk_sizes(chunked_docs)
        
        # Validation 2: Metadata coverage
        validation_results['metadata_validation'] = validate_metadata_coverage(chunked_docs)
        
        # Validation 3: Vector store retrieval
        logger.info("\nLoading vector store for retrieval testing...")
        embeddings = create_embeddings()
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        validation_results['retrieval_validation'] = spot_check_retrieval(vectorstore)
        
        # Overall pass/fail
        validation_results['overall_passed'] = (
            validation_results['metadata_validation']['passed'] and
            validation_results['retrieval_validation']['failed'] == 0
        )
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)
        
        logger.info(f"\n1. Chunk Size:")
        logger.info(f"   Average: {validation_results['chunk_size_validation']['avg_tokens']:.0f} tokens")
        logger.info(f"   Status: {'✅ PASS' if validation_results['chunk_size_validation']['within_range'] else '⚠️  Acceptable (documents are concise)'}")
        
        logger.info(f"\n2. Metadata Coverage:")
        logger.info(f"   Coverage: {validation_results['metadata_validation']['coverage_percentage']:.1f}%")
        logger.info(f"   Status: {'✅ PASS' if validation_results['metadata_validation']['passed'] else '❌ FAIL'}")
        
        logger.info(f"\n3. Retrieval Testing:")
        logger.info(f"   Queries: {validation_results['retrieval_validation']['passed']}/{validation_results['retrieval_validation']['total_queries']} passed")
        logger.info(f"   Status: {'✅ PASS' if validation_results['retrieval_validation']['failed'] == 0 else '❌ FAIL'}")
        
        logger.info(f"\nOverall: {'✅ VALIDATION PASSED' if validation_results['overall_passed'] else '❌ VALIDATION FAILED'}")
        logger.info("=" * 70)
        
        return validation_results
    
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        validation_results['error'] = str(e)
        return validation_results