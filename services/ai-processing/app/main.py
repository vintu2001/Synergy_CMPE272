"""
AI Processing Service
Handles message classification and risk prediction.
Deployed on Railway.
"""
from dotenv import load_dotenv
load_dotenv()

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import HealthCheck
from app.utils.cloudwatch_logger import setup_cloudwatch_logging, log_to_cloudwatch
import time

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Processing Service",
    description="Message classification and risk prediction",
    version="1.0.0"
)

setup_cloudwatch_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        log_to_cloudwatch('http_request', {
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': round(process_time, 2)
        })
        
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        log_to_cloudwatch('http_error', {
            'method': request.method,
            'path': request.url.path,
            'error': str(e),
            'duration_ms': round(process_time, 2)
        })
        logger.error(f"Request error: {request.method} {request.url.path} - {str(e)}")
        raise

@app.get("/", response_model=HealthCheck)
async def root():
    return {"status": "healthy", "service": "AI Processing Service"}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "service": "AI Processing Service"}

# Import routers
from app.api import routes

app.include_router(routes.router, prefix="/api/v1", tags=["ai"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

