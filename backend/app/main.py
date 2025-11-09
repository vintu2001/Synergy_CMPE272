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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthCheck)
async def root():
    return {"status": "healthy", "service": "Agentic Apartment Manager API"}


@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "service": "Agentic Apartment Manager API"}


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

