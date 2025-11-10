"""
Embeddings Service - Vector similarity search for repeat issue detection
Uses Pinecone (cloud vector DB) and sentence-transformers for semantic similarity.
"""
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Initialize the embedding model (downloads once, ~80MB)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Pinecone configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
INDEX_NAME = "apartment-issues"

# Initialize Pinecone client
pc = None
index = None

def initialize_pinecone():
    """Initialize Pinecone connection and create index if needed"""
    global pc, index
    
    print(f"🔍 DEBUG: PINECONE_API_KEY value: {PINECONE_API_KEY[:20] if PINECONE_API_KEY else 'None'}...")
    print(f"🔍 DEBUG: PINECONE_ENVIRONMENT: {PINECONE_ENVIRONMENT}")
    
    if not PINECONE_API_KEY or PINECONE_API_KEY == "your_pinecone_api_key_here":
        logger.warning("PINECONE_API_KEY not set - vector similarity disabled")
        print("❌ Pinecone API key is missing or not configured")
        return False
    
    try:
        # Initialize Pinecone
        print(f"🔄 Initializing Pinecone client...")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        print(f"✓ Pinecone client initialized")
        
        # Check if index exists, create if not
        print(f"🔄 Checking for existing indexes...")
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        print(f"✓ Found {len(existing_indexes)} existing indexes: {existing_indexes}")
        
        if INDEX_NAME not in existing_indexes:
            logger.info(f"Creating Pinecone index: {INDEX_NAME}")
            print(f"🔄 Creating new index: {INDEX_NAME}")
            pc.create_index(
                name=INDEX_NAME,
                dimension=384,  # all-MiniLM-L6-v2 produces 384-dim vectors
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=PINECONE_ENVIRONMENT
                )
            )
            logger.info(f"✓ Created index: {INDEX_NAME}")
            print(f"✓ Created index: {INDEX_NAME}")
        
        # Connect to index
        print(f"🔄 Connecting to index: {INDEX_NAME}")
        index = pc.Index(INDEX_NAME)
        logger.info(f"✓ Connected to Pinecone index: {INDEX_NAME}")
        print(f"✓ Connected to Pinecone index: {INDEX_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")
        print(f"❌ Failed to initialize Pinecone: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def add_issue_to_vector_db(
    request_id: str,
    message_text: str,
    resident_id: str,
    category: str,
    created_at: str
) -> bool:
    """
    Store a maintenance issue in the vector database.
    
    Args:
        request_id: Unique request ID
        message_text: The resident's message
        resident_id: Resident identifier
        category: Issue category
        created_at: ISO timestamp
        
    Returns:
        True if successful, False otherwise
    """
    if not index:
        logger.warning("Pinecone not initialized - skipping vector storage")
        return False
    
    try:
        # Generate embedding for the message
        embedding = model.encode(message_text).tolist()
        
        # Store in Pinecone with metadata
        index.upsert(vectors=[{
            'id': request_id,
            'values': embedding,
            'metadata': {
                'resident_id': resident_id,
                'category': category,
                'message_text': message_text,
                'created_at': created_at
            }
        }])
        
        logger.info(f"✓ Stored embedding for request {request_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store embedding: {e}")
        return False


def find_similar_issues(
    message_text: str,
    resident_id: str,
    category: str,
    similarity_threshold: float = 0.75,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Find similar past issues for a specific resident in the same category.
    
    Args:
        message_text: Current message to check
        resident_id: Resident to search for
        category: Issue category to filter by
        similarity_threshold: Minimum similarity score (0.0-1.0)
        top_k: Maximum number of results to return
        
    Returns:
        Dict with is_repeat, repeat_count, and similar_issues list
    """
    if not index:
        logger.warning("Pinecone not initialized - using fallback")
        return {
            'is_repeat_issue': False,
            'repeat_count': 0,
            'similar_issues': [],
            'method': 'fallback'
        }
    
    try:
        # Generate embedding for current message
        embedding = model.encode(message_text).tolist()
        
        # Query Pinecone for similar vectors
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter={
                'resident_id': {'$eq': resident_id},
                'category': {'$eq': category}
            }
        )
        
        # Filter by similarity threshold
        similar_issues = []
        for match in results.matches:
            similarity_score = match.score
            
            if similarity_score >= similarity_threshold:
                similar_issues.append({
                    'request_id': match.id,
                    'similarity_score': round(similarity_score, 3),
                    'message_text': match.metadata.get('message_text', ''),
                    'created_at': match.metadata.get('created_at', ''),
                })
        
        is_repeat = len(similar_issues) >= 1  # At least 1 similar past issue
        
        logger.info(
            f"Found {len(similar_issues)} similar issues for {resident_id} "
            f"(threshold: {similarity_threshold})"
        )
        
        return {
            'is_repeat_issue': is_repeat,
            'repeat_count': len(similar_issues),
            'similar_issues': similar_issues,
            'method': 'vector_similarity',
            'threshold': similarity_threshold
        }
        
    except Exception as e:
        logger.error(f"Error finding similar issues: {e}")
        return {
            'is_repeat_issue': False,
            'repeat_count': 0,
            'similar_issues': [],
            'method': 'error'
        }


def get_vector_db_stats() -> Dict[str, Any]:
    """Get statistics about the vector database"""
    if not index:
        return {'status': 'not_initialized'}
    
    try:
        stats = index.describe_index_stats()
        return {
            'status': 'connected',
            'total_vectors': stats.total_vector_count,
            'index_name': INDEX_NAME,
            'dimension': 384
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {'status': 'error', 'error': str(e)}


# Initialize on module import
initialize_pinecone()
