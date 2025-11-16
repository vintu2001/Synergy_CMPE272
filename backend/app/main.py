from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file FIRST

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import HealthCheck

app = FastAPI(
    title="Agentic Apartment Manager API",
    description="Autonomous AI-driven apartment management system",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed to False for compatibility with allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthCheck)
async def root():
    return {"status": "healthy", "service": "Agentic Apartment Manager API"}


@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "service": "Agentic Apartment Manager API"}


@app.get("/config/rag")
async def get_rag_config():
    """Debug endpoint to check RAG configuration values"""
    return {
        "RAG_ENABLED": os.getenv("RAG_ENABLED", "not set"),
        "RAG_TOP_K": os.getenv("RAG_TOP_K", "not set"),
        "RAG_SIMILARITY_THRESHOLD": os.getenv("RAG_SIMILARITY_THRESHOLD", "not set"),
        "VECTOR_STORE_PATH": os.getenv("VECTOR_STORE_PATH", "not set"),
        "VECTOR_STORE_COLLECTION": os.getenv("VECTOR_STORE_COLLECTION", "not set"),
        "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "not set"),
    }


@app.get("/debug/rag-test")
async def test_rag_retrieval():
    """Debug endpoint to directly test RAG retrieval"""
    from app.rag.retriever import get_retriever, reset_retriever, RETRIEVER_VERSION
    
    # Force reinitialize to pick up any code changes
    reset_retriever()
    retriever = get_retriever()
    
    # Test query expansion
    test_query = "AC not working"
    expanded = retriever.expand_query(test_query)
    
    # Get raw ChromaDB results BEFORE threshold filtering
    query_embedding = retriever.embedding_model.encode(expanded).tolist()
    raw_results = retriever.collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        include=["documents", "metadatas", "distances"]
    )
    
    # Convert distances to similarity scores
    raw_docs = []
    if raw_results and raw_results.get('distances'):
        for i, distance in enumerate(raw_results['distances'][0]):
            similarity = 1.0 - distance
            metadata = raw_results['metadatas'][0][i] if i < len(raw_results['metadatas'][0]) else {}
            raw_docs.append({
                "doc_id": metadata.get("doc_id", "unknown"),
                "score": round(similarity, 4),
                "distance": round(distance, 4),
                "category": metadata.get("category", "unknown"),
                "type": metadata.get("type", "unknown")
            })
    
    # Test query with normal flow (don't specify doc_types to use default which now includes sla)
    result = await retriever.retrieve_relevant_docs(
        query=test_query,
        category="Maintenance",
        building_id=None,
        doc_types=None  # Use default which includes sla
    )
    
    if result:
        return {
            "success": True,
            "version": RETRIEVER_VERSION,
            "query": test_query,
            "expanded_query": expanded,
            "raw_top_10_scores": raw_docs,
            "total_retrieved_after_filter": result.total_retrieved,
            "documents": [
                {
                    "doc_id": doc.get("doc_id"),
                    "score": doc.get("score"),
                    "category": doc.get("metadata", {}).get("category"),
                    "type": doc.get("metadata", {}).get("type"),
                    "text_preview": doc.get("text", "")[:100]
                }
                for doc in (result.retrieved_docs or [])
            ],
            "retriever_config": {
                "enabled": retriever.enabled,
                "threshold": retriever.similarity_threshold,
                "top_k": retriever.top_k,
                "collection_name": retriever.collection_name
            }
        }
    else:
        return {
            "success": False,
            "message": "RAG retrieval returned None",
            "version": RETRIEVER_VERSION,
            "raw_top_10_scores": raw_docs,
            "retriever_config": {
                "enabled": retriever.enabled,
                "threshold": retriever.similarity_threshold,
                "top_k": retriever.top_k
            }
        }


from app.agents import classification_agent, risk_prediction_agent, simulation_agent, decision_agent
from app.services import message_intake, execution_layer, admin_api, resident_api

app.include_router(classification_agent.router, prefix="/api/v1", tags=["agents"])
app.include_router(risk_prediction_agent.router, prefix="/api/v1", tags=["agents"])
app.include_router(simulation_agent.router, prefix="/api/v1", tags=["agents"])
app.include_router(decision_agent.router, prefix="/api/v1", tags=["agents"])

app.include_router(message_intake.router, prefix="/api/v1", tags=["services"])
app.include_router(execution_layer.router, prefix="/api/v1", tags=["services"])
app.include_router(resident_api.router, prefix="/api/v1", tags=["services"])

app.include_router(admin_api.router, prefix="/api/v1", tags=["admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

