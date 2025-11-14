from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file FIRST

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import HealthCheck, VectorStoreHealth
from app.rag.vector_store import health_check as vector_store_health_check
from app.config import get_settings

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


@app.get("/health/vector-store", response_model=VectorStoreHealth)
async def vector_store_health():
    """
    Check health of the vector store.
    
    Returns:
        VectorStoreHealth: Status, collection existence, document count
    """
    settings = get_settings()
    health = vector_store_health_check(
        persist_directory=settings.PERSIST_DIR,
        collection_name=settings.COLLECTION_NAME
    )
    return health


@app.on_event("startup")
async def startup_event():
    """Check vector store health on startup."""
    import logging
    logger = logging.getLogger(__name__)
    
    settings = get_settings()
    health = vector_store_health_check(
        persist_directory=settings.PERSIST_DIR,
        collection_name=settings.COLLECTION_NAME
    )
    
    if health["status"] == "healthy":
        logger.info(
            f"✅ Vector store healthy: {health['document_count']} documents in '{settings.COLLECTION_NAME}'"
        )
    else:
        logger.warning(
            f"⚠️  Vector store unhealthy: {health.get('error', 'unknown error')}"
        )


from app.agents import classification_agent, risk_prediction_agent, simulation_agent, decision_agent
from app.services import message_intake, execution_layer, admin_api, resident_api, governance_api

app.include_router(classification_agent.router, prefix="/api/v1", tags=["agents"])
app.include_router(risk_prediction_agent.router, prefix="/api/v1", tags=["agents"])
app.include_router(simulation_agent.router, prefix="/api/v1", tags=["agents"])
app.include_router(decision_agent.router, prefix="/api/v1", tags=["agents"])

app.include_router(message_intake.router, prefix="/api/v1", tags=["services"])
app.include_router(execution_layer.router, prefix="/api/v1", tags=["services"])
app.include_router(resident_api.router, prefix="/api/v1", tags=["services"])

app.include_router(admin_api.router, prefix="/api/v1", tags=["admin"])
app.include_router(governance_api.router, prefix="/api/v1", tags=["governance"])  # Ticket 15


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

