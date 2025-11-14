"""
API Gateway
Routes requests to appropriate microservices
"""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import logging
import boto3
import watchtower
from typing import Dict

# Configure logging with CloudWatch
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler for local development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Add CloudWatch handler for AWS
try:
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    cloudwatch_handler = watchtower.CloudWatchLogHandler(
        log_group='/synergy/gateway-service',
        stream_name='{machine_name}-{strftime:%Y-%m-%d}',
        boto3_client=boto3.client('logs', region_name=AWS_REGION)
    )
    cloudwatch_handler.setLevel(logging.INFO)
    logger.addHandler(cloudwatch_handler)
    logger.info("CloudWatch logging initialized successfully")
except Exception as e:
    logger.warning(f"CloudWatch logging not available: {e}. Using console logging only.")

app = FastAPI(title="api-gateway", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "message-intake": os.getenv("MESSAGE_INTAKE_URL", "http://message-intake:8003"),
    "decision-engine": os.getenv("DECISION_ENGINE_URL", "http://decision-engine:8002"),
    "governance": os.getenv("GOVERNANCE_URL", "http://governance:8001"),
}


@app.get("/health")
async def health():
    """Gateway health check and downstream service health"""
    health_checks = {"gateway": "healthy"}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in SERVICES.items():
            try:
                resp = await client.get(f"{url}/health")
                if resp.status_code == 200:
                    health_checks[name] = resp.json()
                else:
                    health_checks[name] = {"status": "unhealthy", "code": resp.status_code}
            except Exception as e:
                health_checks[name] = {"status": "unreachable", "error": str(e)}
    
    return {"status": "healthy", "services": health_checks}


# Message Intake endpoints
@app.post("/api/requests/submit")
async def submit_request(request: Request):
    """Forward to message-intake service"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{SERVICES['message-intake']}/api/requests/submit",
                json=body
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to message-intake: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/requests/select")
async def select_option(request: Request):
    """Forward to message-intake service"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICES['message-intake']}/api/requests/select",
                json=body
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to message-intake: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/requests/resolve")
async def resolve_request(request: Request):
    """Forward to message-intake service"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICES['message-intake']}/api/requests/resolve",
                json=body
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to message-intake: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Governance endpoints
@app.post("/api/governance/query")
async def query_governance(request: Request, x_api_key: str = Header(..., alias="X-API-Key")):
    """Forward to governance service"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICES['governance']}/api/governance/query",
                json=body,
                headers={"X-API-Key": x_api_key}
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to governance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/governance/stats")
async def get_governance_stats(x_api_key: str = Header(..., alias="X-API-Key")):
    """Forward to governance service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{SERVICES['governance']}/api/governance/stats",
                headers={"X-API-Key": x_api_key}
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to governance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/governance/export")
async def export_governance(format: str = "json", x_api_key: str = Header(..., alias="X-API-Key")):
    """Forward to governance service"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{SERVICES['governance']}/api/governance/export?format={format}",
                headers={"X-API-Key": x_api_key}
            )
            resp.raise_for_status()
            return JSONResponse(
                content=resp.json() if format == "json" else resp.text,
                media_type="application/json" if format == "json" else "text/csv"
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to governance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin and resident endpoints (proxy to backend database service if needed)
# For now, these can also be routed through message-intake or a separate admin service

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
