#!/usr/bin/env python3
"""
Knowledge Base Document Ingestion Script

Loads documents from kb/ directory, processes them, generates embeddings,
and stores them in ChromaDB vector store.

Supports:
- Markdown files (.md) with YAML frontmatter
- CSV files (.csv) with YAML header comments

Usage:
    python kb/ingest_documents.py                    # Ingest all documents
    python kb/ingest_documents.py --dir kb/policies  # Ingest specific directory
    python kb/ingest_documents.py --file kb/policies/policy_noise_1.0.md  # Ingest single file
    python kb/ingest_documents.py --force            # Force re-ingestion (overwrite existing)
    python kb/ingest_documents.py --dry-run          # Preview without changes
"""

import os
import sys
import argparse
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from sentence_transformers import SentenceTransformer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentIngester:
    """
    Handles document ingestion from KB into vector store.
    
    Features:
    - Parse YAML frontmatter from Markdown
    - Parse YAML comments from CSV
    - Chunk documents by paragraphs
    - Generate embeddings
    - Store in ChromaDB with metadata
    """
    
    def __init__(
        self,
        vector_store_path: str = "./vector_stores/chroma_db",
        collection_name: str = "apartment_kb",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """Initialize document ingester."""
        self.vector_store_path = vector_store_path
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info("Embedding model loaded successfully")
        
        # Initialize ChromaDB
        logger.info(f"Connecting to ChromaDB at: {vector_store_path}")
        self.chroma_client = chromadb.PersistentClient(path=vector_store_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Connected to collection '{collection_name}'")
    
    def parse_markdown_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from Markdown content.
        
        Args:
            content: Full markdown content
        
        Returns:
            Tuple of (metadata dict, content without frontmatter)
        """
        # Match YAML frontmatter between --- markers
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            logger.warning("No YAML frontmatter found in markdown")
            return {}, content
        
        frontmatter_text = match.group(1)
        document_text = match.group(2)
        
        try:
            metadata = yaml.safe_load(frontmatter_text)
            return metadata, document_text
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML frontmatter: {e}")
            return {}, content
    
    def parse_csv_header_metadata(self, file_path: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """
        Parse YAML metadata from CSV header comments.
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            Tuple of (metadata dict, DataFrame)
        """
        metadata = {}
        
        # Read file to extract YAML comments
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Extract YAML from comments (lines starting with ---)
        yaml_lines = []
        data_start_idx = 0
        in_yaml = False
        
        for idx, line in enumerate(lines):
            if line.strip() == '---':
                if not in_yaml:
                    in_yaml = True
                    continue
                else:
                    in_yaml = False
                    data_start_idx = idx + 1
                    break
            if in_yaml:
                yaml_lines.append(line)
        
        # Parse YAML metadata
        if yaml_lines:
            try:
                yaml_content = ''.join(yaml_lines)
                metadata = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                logger.error(f"Error parsing CSV YAML header: {e}")
        
        # Read CSV data (skip header comments)
        df = pd.read_csv(file_path, skiprows=data_start_idx)
        
        return metadata, df
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """
        Chunk text by paragraphs with overlap.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        # Split by paragraphs (double newline)
        paragraphs = re.split(r'\n\n+', text.strip())
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para)
            
            # If single paragraph exceeds chunk_size, split it
            if para_length > chunk_size:
                # Add current chunk if exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split long paragraph into sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                temp_chunk = []
                temp_length = 0
                
                for sentence in sentences:
                    if temp_length + len(sentence) > chunk_size and temp_chunk:
                        chunks.append(' '.join(temp_chunk))
                        # Keep overlap
                        if overlap > 0 and temp_chunk:
                            overlap_text = ' '.join(temp_chunk[-1:])
                            temp_chunk = [overlap_text, sentence]
                            temp_length = len(overlap_text) + len(sentence)
                        else:
                            temp_chunk = [sentence]
                            temp_length = len(sentence)
                    else:
                        temp_chunk.append(sentence)
                        temp_length += len(sentence)
                
                if temp_chunk:
                    chunks.append(' '.join(temp_chunk))
                
            # If adding paragraph fits in current chunk
            elif current_length + para_length <= chunk_size:
                current_chunk.append(para)
                current_length += para_length
            
            # Start new chunk
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                
                # Keep overlap from previous chunk
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    current_chunk = [overlap_text, para]
                    current_length = len(overlap_text) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def process_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a Markdown file into document chunks.
        
        Args:
            file_path: Path to markdown file
        
        Returns:
            List of document chunk dictionaries
        """
        logger.info(f"Processing Markdown: {file_path}")
        
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse frontmatter
        metadata, text = self.parse_markdown_frontmatter(content)
        
        if not metadata:
            logger.warning(f"No metadata found in {file_path}, skipping")
            return []
        
        # Chunk text
        chunks = self.chunk_text(text, self.chunk_size, self.chunk_overlap)
        
        # Build document chunks
        documents = []
        for idx, chunk_text in enumerate(chunks):
            doc_id = metadata.get('doc_id', Path(file_path).stem)
            chunk_id = f"{doc_id}_chunk_{idx}"
            
            # Convert keywords list to comma-separated string for ChromaDB
            keywords = metadata.get('keywords', [])
            if isinstance(keywords, list):
                keywords_str = ', '.join(str(k) for k in keywords)
            else:
                keywords_str = str(keywords)
            
            doc = {
                'id': chunk_id,
                'text': chunk_text,
                'metadata': {
                    'doc_id': doc_id,
                    'type': metadata.get('type', 'unknown'),
                    'category': metadata.get('category', 'unknown'),
                    'building_id': metadata.get('building_id', 'all_buildings'),
                    'effective_date': metadata.get('effective_date', ''),
                    'version': metadata.get('version', '1.0'),
                    'keywords': keywords_str,
                    'chunk_index': idx,
                    'total_chunks': len(chunks),
                    'source_file': str(file_path)
                }
            }
            documents.append(doc)
        
        logger.info(f"  Created {len(documents)} chunks")
        return documents
    
    def process_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a CSV file into document chunks.
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            List of document chunk dictionaries
        """
        logger.info(f"Processing CSV: {file_path}")
        
        # Parse metadata and data
        metadata, df = self.parse_csv_header_metadata(file_path)
        
        if not metadata:
            logger.warning(f"No metadata found in {file_path}, skipping")
            return []
        
        # Convert DataFrame to text representation
        text = f"# {metadata.get('category', 'Catalog').replace('_', ' ').title()}\n\n"
        text += df.to_string(index=False)
        
        # Chunk text
        chunks = self.chunk_text(text, self.chunk_size, self.chunk_overlap)
        
        # Build document chunks
        documents = []
        for idx, chunk_text in enumerate(chunks):
            doc_id = metadata.get('doc_id', Path(file_path).stem)
            chunk_id = f"{doc_id}_chunk_{idx}"
            
            # Convert keywords list to comma-separated string for ChromaDB
            keywords = metadata.get('keywords', [])
            if isinstance(keywords, list):
                keywords_str = ', '.join(str(k) for k in keywords)
            else:
                keywords_str = str(keywords)
            
            doc = {
                'id': chunk_id,
                'text': chunk_text,
                'metadata': {
                    'doc_id': doc_id,
                    'type': metadata.get('type', 'catalog'),
                    'category': metadata.get('category', 'unknown'),
                    'building_id': metadata.get('building_id', 'all_buildings'),
                    'effective_date': metadata.get('effective_date', ''),
                    'version': metadata.get('version', '1.0'),
                    'keywords': keywords_str,
                    'chunk_index': idx,
                    'total_chunks': len(chunks),
                    'source_file': str(file_path)
                }
            }
            documents.append(doc)
        
        logger.info(f"  Created {len(documents)} chunks")
        return documents
    
    def ingest_document(self, file_path: str) -> int:
        """
        Ingest a single document file.
        
        Args:
            file_path: Path to document file
        
        Returns:
            Number of chunks ingested
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Process based on file type
        if file_ext == '.md':
            documents = self.process_markdown_file(file_path)
        elif file_ext == '.csv':
            documents = self.process_csv_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return 0
        
        if not documents:
            return 0
        
        # Generate embeddings
        texts = [doc['text'] for doc in documents]
        logger.info(f"  Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        
        # Prepare for ChromaDB
        ids = [doc['id'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"  ✓ Ingested {len(documents)} chunks")
        return len(documents)
    
    def ingest_directory(self, directory: str, recursive: bool = True) -> Dict[str, int]:
        """
        Ingest all documents from a directory.
        
        Args:
            directory: Path to directory
            recursive: Whether to search subdirectories
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_files': 0,
            'total_chunks': 0,
            'successful': 0,
            'failed': 0
        }
        
        # Find all document files
        path = Path(directory)
        if recursive:
            md_files = list(path.rglob('*.md'))
            csv_files = list(path.rglob('*.csv'))
        else:
            md_files = list(path.glob('*.md'))
            csv_files = list(path.glob('*.csv'))
        
        all_files = md_files + csv_files
        stats['total_files'] = len(all_files)
        
        logger.info(f"Found {len(all_files)} document files in {directory}")
        
        # Process each file
        for file_path in all_files:
            try:
                chunks = self.ingest_document(str(file_path))
                stats['total_chunks'] += chunks
                stats['successful'] += 1
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")
                stats['failed'] += 1
        
        return stats
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        logger.warning("Clearing collection...")
        # Delete and recreate collection
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Collection cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        
        # Get sample documents to analyze
        if count > 0:
            sample = self.collection.get(limit=min(100, count), include=['metadatas'])
            
            # Count by type
            type_counts = {}
            building_counts = {}
            category_counts = {}
            
            for metadata in sample['metadatas']:
                doc_type = metadata.get('type', 'unknown')
                building = metadata.get('building_id', 'unknown')
                category = metadata.get('category', 'unknown')
                
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                building_counts[building] = building_counts.get(building, 0) + 1
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                'total_chunks': count,
                'type_distribution': type_counts,
                'building_distribution': building_counts,
                'category_distribution': category_counts
            }
        
        return {'total_chunks': 0}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Ingest knowledge base documents into ChromaDB vector store'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='kb',
        help='Directory to ingest (default: kb/)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Single file to ingest'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-ingestion (clear existing collection)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without making changes'
    )
    parser.add_argument(
        '--vector-store-path',
        type=str,
        default='./vector_stores/chroma_db',
        help='Path to ChromaDB storage'
    )
    parser.add_argument(
        '--collection-name',
        type=str,
        default='apartment_kb',
        help='ChromaDB collection name'
    )
    parser.add_argument(
        '--embedding-model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Sentence-transformers model name'
    )
    
    args = parser.parse_args()
    
    # Banner
    logger.info("=" * 60)
    logger.info("Knowledge Base Document Ingestion")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    # Initialize ingester
    try:
        ingester = DocumentIngester(
            vector_store_path=args.vector_store_path,
            collection_name=args.collection_name,
            embedding_model=args.embedding_model
        )
    except Exception as e:
        logger.error(f"Failed to initialize ingester: {e}")
        return 1
    
    # Show existing stats
    logger.info("\nCurrent collection stats:")
    stats = ingester.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # Force clear if requested
    if args.force and not args.dry_run:
        ingester.clear_collection()
    
    # Ingest documents
    if not args.dry_run:
        logger.info("\nStarting ingestion...")
        
        if args.file:
            # Ingest single file
            chunks = ingester.ingest_document(args.file)
            logger.info(f"\n✓ Ingested {chunks} chunks from {args.file}")
        else:
            # Ingest directory
            stats = ingester.ingest_directory(args.dir)
            logger.info("\nIngestion complete!")
            logger.info(f"  Total files: {stats['total_files']}")
            logger.info(f"  Successful: {stats['successful']}")
            logger.info(f"  Failed: {stats['failed']}")
            logger.info(f"  Total chunks: {stats['total_chunks']}")
        
        # Show final stats
        logger.info("\nFinal collection stats:")
        final_stats = ingester.get_stats()
        for key, value in final_stats.items():
            logger.info(f"  {key}: {value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Ingestion process finished")
    logger.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
