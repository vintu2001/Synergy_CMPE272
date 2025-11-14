from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import httpx
import logging
import time
import re
import boto3
from datetime import datetime, timezone

sys.path.insert(0, '/app/libs')

from shared_models import (
    MessageRequest, Status, ResidentRequest, ClassificationResponse,
    SimulationResponse, PolicyWeights, PolicyConfiguration,
    SelectOptionRequest, ResolveRequestModel, HealthCheck
)
from app.services.database import create_request, get_request_by_id
from app.utils.helpers import generate_request_id
from app.utils.cloudwatch_logger import (
    log_request_submission, log_classification, log_risk_assessment,
    log_simulation_result, log_error, ensure_log_stream
)
import watchtower

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
        log_group='/synergy/message-intake-service',
        stream_name='{machine_name}-{strftime:%Y-%m-%d}',
        boto3_client=boto3.client('logs', region_name=AWS_REGION)
    )
    cloudwatch_handler.setLevel(logging.INFO)
    logger.addHandler(cloudwatch_handler)
    logger.info("CloudWatch logging initialized successfully")
except Exception as e:
    logger.warning(f"CloudWatch logging not available: {e}. Using console logging only.")

app = FastAPI(title="message-intake-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DECISION_ENGINE_URL = os.getenv("DECISION_ENGINE_URL", "http://decision-engine:8002")
GOVERNANCE_URL = os.getenv("GOVERNANCE_URL", "http://governance:8001")

try:
    ensure_log_stream()
    logger.info("CloudWatch log stream initialized")
except Exception as e:
    logger.warning(f"Could not initialize CloudWatch logs: {e}")


def normalize_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^a-z0-9\s.,!?]', '', normalized)
    return normalized.strip()


@app.get("/health", response_model=HealthCheck)
async def health():
    return HealthCheck(status="healthy", service="message-intake")


@app.post("/api/requests/submit")
async def submit_request(request: MessageRequest):
    start_time = time.time()
    request_id = generate_request_id()
    
    try:
        logger.info(f"Processing request for resident: {request.resident_id}")
        _normalized_text = normalize_text(request.message_text)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            classification_response = await client.post(
                f"{DECISION_ENGINE_URL}/api/classify",
                json={"message_text": request.message_text, "resident_id": request.resident_id}
            )
            classification_response.raise_for_status()
            classification_data = classification_response.json()
            classification = ClassificationResponse(**classification_data)
        
        final_category = request.category if request.category else classification.category
        final_urgency = request.urgency if request.urgency else classification.urgency
        
        log_classification(
            request_id=request_id,
            category=final_category.value,
            urgency=final_urgency.value,
            intent=classification.intent.value,
            confidence=classification.confidence
        )
        
        risk_score = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                risk_response = await client.post(
                    f"{DECISION_ENGINE_URL}/api/predict-risk",
                    json={
                        "category": final_category.value,
                        "urgency": final_urgency.value,
                        "intent": classification.intent.value,
                        "confidence": classification.confidence,
                        "message_text": request.message_text
                    }
                )
                risk_response.raise_for_status()
                risk_data = risk_response.json()
                risk_score = risk_data.get("risk_forecast")
                logger.info(f"Risk prediction successful: {risk_score:.4f}")
                
                risk_level = "High" if risk_score > 0.7 else "Medium" if risk_score > 0.3 else "Low"
                log_risk_assessment(
                    request_id=request_id,
                    risk_score=risk_score,
                    risk_level=risk_level
                )
        except Exception as risk_error:
            logger.warning(f"Risk prediction failed (non-critical): {risk_error}")
        
        simulation_result = None
        simulated_options = None
        recommended_option_id = None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                sim_response = await client.post(
                    f"{DECISION_ENGINE_URL}/api/simulate",
                    json={
                        "classification": {
                            "category": final_category.value,
                            "urgency": final_urgency.value,
                            "intent": classification.intent.value,
                            "confidence": classification.confidence,
                            "message_text": request.message_text,
                            "resident_id": request.resident_id
                        },
                        "risk_score": risk_score if risk_score is not None else 0.5
                    }
                )
                sim_response.raise_for_status()
                simulation_data = sim_response.json()
                simulation_result = SimulationResponse(**simulation_data)
                
                simulated_options = [
                    {
                        "option_id": opt.option_id,
                        "action": opt.action,
                        "estimated_cost": opt.estimated_cost,
                        "time_to_resolution": opt.time_to_resolution,
                        "resident_satisfaction_impact": opt.resident_satisfaction_impact
                    }
                    for opt in simulation_result.options
                ]
                logger.info(f"Simulation generated {len(simulated_options)} options")
        except Exception as sim_error:
            logger.warning(f"Simulation failed (non-critical): {sim_error}")
        
        if simulation_result:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    decision_response = await client.post(
                        f"{DECISION_ENGINE_URL}/api/decide",
                        json={
                            "classification": classification_data,
                            "simulation": simulation_data,
                            "weights": PolicyWeights().dict(),
                            "config": PolicyConfiguration().dict()
                        }
                    )
                    decision_response.raise_for_status()
                    decision_data = decision_response.json()
                    recommended_option_id = decision_data.get("chosen_option_id")
                    logger.info(f"AI recommended option: {recommended_option_id}")
            except Exception as decision_error:
                logger.warning(f"Decision recommendation failed (non-critical): {decision_error}")
        
        now = datetime.now(timezone.utc)
        resident_request = ResidentRequest(
            request_id=request_id,
            resident_id=request.resident_id,
            message_text=request.message_text,
            category=final_category,
            urgency=final_urgency,
            intent=classification.intent,
            status=Status.SUBMITTED,
            risk_forecast=risk_score,
            classification_confidence=classification.confidence,
            simulated_options=simulated_options,
            recommended_option_id=recommended_option_id,
            created_at=now,
            updated_at=now
        )
        
        success = create_request(resident_request)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save request to database")
        
        response_data = {
            "status": "submitted",
            "message": "Request submitted successfully!",
            "request_id": request_id,
            "classification": {
                "category": final_category.value,
                "urgency": final_urgency.value,
                "intent": classification.intent.value,
                "confidence": classification.confidence
            },
            "risk_assessment": {
                "risk_forecast": risk_score,
                "risk_level": "High" if risk_score and risk_score > 0.7 else "Medium" if risk_score and risk_score > 0.3 else "Low" if risk_score else "Unknown"
            } if risk_score is not None else None
        }
        
        if simulation_result:
            response_data["simulation"] = {
                "options_generated": len(simulation_result.options),
                "options": simulated_options,
                "recommended_option_id": recommended_option_id
            }
            
            log_simulation_result(
                request_id=request_id,
                option_count=len(simulation_result.options),
                recommended_option_id=recommended_option_id,
                is_repeat=False
            )
        
        processing_time = (time.time() - start_time) * 1000
        log_request_submission(
            request_id=request_id,
            resident_id=request.resident_id,
            category=final_category.value,
            urgency=final_urgency.value,
            confidence=classification.confidence,
            message_preview=request.message_text[:100]
        )
        
        logger.info(f"Request {request_id} processed in {processing_time:.2f}ms")
        
        return response_data
        
    except Exception as e:
        log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={
                'request_id': request_id if 'request_id' in locals() else 'unknown',
                'resident_id': request.resident_id,
                'endpoint': '/api/requests/submit'
            }
        )
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/api/requests/select")
async def select_option(selection: SelectOptionRequest):
    try:
        request = get_request_by_id(selection.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        from app.services.database import get_table
        table = get_table()
        table.update_item(
            Key={'request_id': selection.request_id},
            UpdateExpression='SET user_selected_option_id = :sel_opt, #status = :status, updated_at = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':sel_opt': selection.selected_option_id,
                ':status': Status.IN_PROGRESS.value,
                ':updated': datetime.now(timezone.utc).isoformat()
            }
        )
        
        selected_option_data = None
        if request.get("simulated_options"):
            for opt in request["simulated_options"]:
                if opt.get("option_id") == selection.selected_option_id:
                    selected_option_data = opt
                    break
        
        if selected_option_data:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        f"{GOVERNANCE_URL}/api/governance/log",
                        json={
                            "request_id": selection.request_id,
                            "resident_id": request.get("resident_id", "unknown"),
                            "decision": {
                                "chosen_action": selected_option_data.get("action"),
                                "chosen_option_id": selection.selected_option_id,
                                "reasoning": "User selected option",
                                "alternatives_considered": [],
                                "policy_scores": {}
                            },
                            "classification": {
                                "category": request.get("category"),
                                "urgency": request.get("urgency"),
                                "intent": request.get("intent")
                            },
                            "risk_score": request.get("risk_forecast"),
                            "total_options_simulated": len(request.get("simulated_options", [])),
                            "estimated_cost": selected_option_data.get("estimated_cost", 0),
                            "estimated_time": selected_option_data.get("time_to_resolution", 0),
                            "exceeds_budget_threshold": False,
                            "exceeds_time_threshold": False,
                            "policy_weights": {}
                        }
                    )
            except Exception as gov_error:
                logger.warning(f"Governance logging failed (non-critical): {gov_error}")
        
        return {
            "status": "success",
            "message": "Option selected successfully",
            "request_id": selection.request_id,
            "selected_option_id": selection.selected_option_id,
            "selected_action": selected_option_data.get("action") if selected_option_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting option: {e}")
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")


@app.post("/api/requests/resolve")
async def resolve_request(resolve: ResolveRequestModel):
    try:
        request = get_request_by_id(resolve.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        from app.services.database import get_table
        table = get_table()
        table.update_item(
            Key={'request_id': resolve.request_id},
            UpdateExpression='SET #status = :status, resolution_notes = :notes, resolved_by = :by, resolved_at = :at, updated_at = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': Status.RESOLVED.value,
                ':notes': resolve.resolution_notes or "",
                ':by': resolve.resolved_by,
                ':at': datetime.now(timezone.utc).isoformat(),
                ':updated': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "status": "success",
            "message": "Request marked as resolved",
            "request_id": resolve.request_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving request: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving request: {str(e)}")


@app.get("/api/requests/{resident_id}")
async def get_resident_requests_endpoint(resident_id: str):
    try:
        from app.services.database import get_requests_by_resident
        requests = get_requests_by_resident(resident_id)
        return {"requests": requests}
    except Exception as e:
        logger.error(f"Error getting resident requests: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting resident requests: {str(e)}")


@app.get("/api/admin/all-requests")
async def get_all_requests_endpoint(x_api_key: str = Header(..., alias="X-API-Key")):
    try:
        admin_key = os.getenv("ADMIN_API_KEY", "yes")
        if x_api_key != admin_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        from app.services.database import get_all_requests
        requests = get_all_requests()
        return {"requests": requests}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all requests: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting all requests: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
