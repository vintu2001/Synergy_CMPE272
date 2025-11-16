"""
Decision & Simulation Service
Handles resolution option simulation, decision making, and RAG retrieval.
Deployed on EC2.
"""
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import HealthCheck

app = FastAPI(
    title="Decision & Simulation Service",
    description="Resolution simulation, decision making, and RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=HealthCheck)
async def root():
    return {"status": "healthy", "service": "Decision & Simulation Service"}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "service": "Decision & Simulation Service"}

# Import routers
from app.api import routes

app.include_router(routes.router, prefix="/api/v1", tags=["decision", "simulation"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

