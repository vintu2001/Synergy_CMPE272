from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import logging
import boto3
import watchtower
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "message-intake": os.getenv("MESSAGE_INTAKE_URL", "http://message-intake:8003"),
    "decision-engine": os.getenv("DECISION_ENGINE_URL", "http://decision-engine:8002"),
    "governance": os.getenv("GOVERNANCE_URL", "http://governance:8001"),
}


@app.get("/health")
async def health():
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


@app.post("/api/requests/submit")
async def submit_request(request: Request):
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


@app.post("/api/governance/query")
async def query_governance(request: Request, x_api_key: str = Header(..., alias="X-API-Key")):
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


@app.post("/api/classify")
async def classify_message(request: Request):
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SERVICES['decision-engine']}/api/classify",
                json=body
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to decision-engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/requests/{resident_id}")
async def get_resident_requests(resident_id: str):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{SERVICES['message-intake']}/api/requests/{resident_id}"
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to message-intake: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/all-requests")
async def get_all_requests(x_api_key: str = Header(..., alias="X-API-Key")):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{SERVICES['message-intake']}/api/admin/all-requests",
                headers={"X-API-Key": x_api_key}
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding to message-intake: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
