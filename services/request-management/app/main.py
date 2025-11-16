"""
Request Management Service
Handles request lifecycle, CRUD operations, and resident/admin APIs.
Deployed on Railway.
"""
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import HealthCheck

app = FastAPI(
    title="Request Management Service",
    description="Request lifecycle management and APIs",
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
    return {"status": "healthy", "service": "Request Management Service"}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "service": "Request Management Service"}

# Import routers
from app.api import resident_api, admin_api
from app.services import orchestrator

app.include_router(resident_api.router, prefix="/api/v1", tags=["resident"])
app.include_router(admin_api.router, prefix="/api/v1", tags=["admin"])
app.include_router(orchestrator.router, prefix="/api/v1", tags=["requests"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

