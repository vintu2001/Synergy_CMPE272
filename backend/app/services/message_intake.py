"""
Message Intake Service
Ingests resident messages, classifies them, predicts risk scores, generates resolution options, and stores in database.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MessageRequest, Status, ResidentRequest, ClassificationResponse, 
    SimulationResponse, PolicyWeights, PolicyConfiguration, DecisionResponse,
    DecisionRequest
)
from app.services.database import create_request, update_request_status
from app.agents.classification_agent import classify_message as classify_message_endpoint
from app.agents.risk_prediction_agent import predict_risk
from app.agents.simulation_agent import simulator
from app.agents.decision_agent import make_decision
from app.services.execution_layer import execute_decision
from app.utils.helpers import generate_request_id
from datetime import datetime, timezone
import re
import os
import json
import boto3
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Environment
REGION = os.getenv("AWS_REGION")
SQS_URL = os.getenv("AWS_SQS_QUEUE_URL")
sqs = boto3.client("sqs", region_name=REGION) if SQS_URL else None


def normalize_text(text: str) -> str:
    """Normalize text before processing."""
    normalized = text.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^a-z0-9\s.,!?]', '', normalized)
    return normalized.strip()


@router.post("/submit-request")
async def submit_request(request: MessageRequest):
    """
    Submit a resident request with automatic classification, risk prediction, and resolution simulation.
    """
    try:
        _normalized_text = normalize_text(request.message_text)
        
        # Step 1: Classification
        classification = await classify_message_endpoint(request)
        
        final_category = request.category if request.category else classification.category
        final_urgency = request.urgency if request.urgency else classification.urgency
        
        # Step 2: Risk Prediction
        risk_result = None
        risk_score = None
        try:
            classification_for_risk = ClassificationResponse(
                category=final_category,
                urgency=final_urgency,
                intent=classification.intent,
                confidence=classification.confidence,
                message_text=request.message_text
            )
            risk_result = await predict_risk(classification_for_risk)
            risk_score = risk_result.risk_forecast
            logger.info(f"Risk prediction successful: {risk_score:.4f}")
        except Exception as risk_error:
            logger.warning(f"Risk prediction failed (non-critical): {risk_error}")
        
        # Step 3: Simulation - Generate resolution options
        simulation_result = None
        simulated_options = None
        try:
            simulation_options = simulator.generate_options(
                category=final_category,
                urgency=final_urgency,
                risk_score=risk_score if risk_score is not None else 0.5
            )
            
            # Convert to dict for storage
            simulated_options = [
                {
                    "option_id": opt.option_id,
                    "action": opt.action,
                    "estimated_cost": opt.estimated_cost,
                    "time_to_resolution": opt.time_to_resolution,
                    "resident_satisfaction_impact": opt.resident_satisfaction_impact
                }
                for opt in simulation_options
            ]
            
            simulation_result = SimulationResponse(
                options=simulation_options,
                issue_id=f"sim_{final_category.value}_{final_urgency.value}"
            )
            logger.info(f"Simulation generated {len(simulated_options)} options")
        except Exception as sim_error:
            logger.warning(f"Simulation failed (non-critical): {sim_error}")
        
        request_id = generate_request_id()
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
            simulated_options=simulated_options,  # NEW: Store simulation results
            created_at=now,
            updated_at=now
        )
        
        success = create_request(resident_request)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save request to database")
        
        if sqs and SQS_URL:
            try:
                payload = {
                    "request_id": request_id,
                    "resident_id": request.resident_id,
                    "message_text": request.message_text,
                    "category": final_category.value,
                    "urgency": final_urgency.value,
                    "intent": classification.intent.value,
                    "risk_forecast": risk_score,
                    "simulated_options": simulated_options,
                    "submitted_at": now.isoformat(),
                }
                sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
            except Exception as sqs_error:
                logger.warning(f"SQS enqueue failed (non-critical): {sqs_error}")
        
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
        
        # Add simulation results if available
        if simulation_result:
            response_data["simulation"] = {
                "options_generated": len(simulation_result.options),
                "options": simulated_options
            }
            
            # Step 4: Decision Making
            try:
                decision_request = DecisionRequest(
                    classification=classification,
                    simulation=simulation_result,
                    weights=PolicyWeights(),  # Use default weights
                    config=PolicyConfiguration()  # Use default configuration
                )
                decision_result = await make_decision(request=decision_request)
                
                # Step 5: Execute Decision
                execution_result = await execute_decision(
                    decision=decision_result,
                    category=final_category
                )
                
                # Update request status based on execution
                new_status = Status.ESCALATED if decision_result.escalation_reason else Status.IN_PROGRESS
                update_request_status(request_id, new_status)
                
                # Add decision and execution results to response
                response_data["decision"] = {
                    "chosen_action": decision_result.chosen_action,
                    "reasoning": decision_result.reasoning,
                    "policy_scores": decision_result.policy_scores
                }
                response_data["execution"] = execution_result
                
                logger.info(f"Decision executed successfully: {decision_result.chosen_action}")
                
            except Exception as decision_error:
                logger.error(f"Decision/execution failed: {decision_error}")
                # Don't fail the request if decision/execution fails
                response_data["decision_status"] = "failed"
                response_data["decision_error"] = str(decision_error)
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
