from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import logging
import boto3
import watchtower

sys.path.insert(0, '/app/libs')

from app.agents import classification_agent, decision_agent, risk_prediction_agent, simulation_agent
from shared_models import HealthCheck

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
        log_group='/synergy/decision-engine-service',
        stream_name='{machine_name}-{strftime:%Y-%m-%d}',
        boto3_client=boto3.client('logs', region_name=AWS_REGION)
    )
    cloudwatch_handler.setLevel(logging.INFO)
    logger.addHandler(cloudwatch_handler)
    logger.info("CloudWatch logging initialized successfully")
except Exception as e:
    logger.warning(f"CloudWatch logging not available: {e}. Using console logging only.")

app = FastAPI(title="decision-engine-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(classification_agent.router, prefix="/api", tags=["classification"])
app.include_router(decision_agent.router, prefix="/api", tags=["decision"])
app.include_router(risk_prediction_agent.router, prefix="/api", tags=["risk"])
app.include_router(simulation_agent.router, prefix="/api", tags=["simulation"])


@app.get("/health", response_model=HealthCheck)
async def health():
    return HealthCheck(status="healthy", service="decision-engine")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
