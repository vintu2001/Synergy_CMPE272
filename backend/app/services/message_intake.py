"""
Message Intake Service
Ingests resident messages, classifies them, predicts risk scores, generates resolution options, and stores in database.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MessageRequest, Status, ResidentRequest, ClassificationResponse, 
    SimulationResponse, PolicyWeights, PolicyConfiguration, DecisionResponse,
    DecisionRequest, SelectOptionRequest, ResolveRequestModel
)
from app.services.database import create_request, update_request_status
from app.agents.classification_agent import classify_message as classify_message_endpoint
from app.agents.risk_prediction_agent import predict_risk
from app.agents.simulation_agent import simulator
from app.agents.decision_agent import make_decision
from app.services.execution_layer import execute_decision
from app.services.governance import log_decision
from app.utils.helpers import generate_request_id
from app.utils.cloudwatch_logger import (
    log_request_submission,
    log_repeat_detection,
    log_classification,
    log_risk_assessment,
    log_simulation_result,
    log_error,
    ensure_log_stream
)
from datetime import datetime, timezone
import re
import os
import json
import boto3
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Environment
REGION = os.getenv("AWS_REGION")
SQS_URL = os.getenv("AWS_SQS_QUEUE_URL")
sqs = boto3.client("sqs", region_name=REGION) if SQS_URL else None

# Initialize CloudWatch logs on startup
try:
    ensure_log_stream()
    logger.info("CloudWatch log stream initialized")
except Exception as e:
    logger.warning(f"Could not initialize CloudWatch logs: {e}")


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
    start_time = time.time()
    request_id = generate_request_id()
    
    try:
        logger.info(f"Processing request for resident: {request.resident_id}")
        _normalized_text = normalize_text(request.message_text)
        
        # Classification
        classification = await classify_message_endpoint(request)
        
        final_category = request.category if request.category else classification.category
        final_urgency = request.urgency if request.urgency else classification.urgency
        
        # Log classification to CloudWatch
        log_classification(
            request_id=request_id,
            category=final_category.value,
            urgency=final_urgency.value,
            intent=classification.intent.value,
            confidence=classification.confidence
        )
        
        # Check for repeat issues (simple category-based for now)
        is_repeat = False
        repeat_count = 0
        similar_issues = []
        
        # Log repeat detection to CloudWatch
        log_repeat_detection(
            request_id=request_id,
            resident_id=request.resident_id,
            category=final_category.value,
            is_repeat=is_repeat,
            repeat_count=repeat_count,
            similarity_scores=[],
            method='disabled'
        )
        
        # Risk Prediction
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
            
            # Log risk assessment to CloudWatch
            risk_level = "High" if risk_score > 0.7 else "Medium" if risk_score > 0.3 else "Low"
            log_risk_assessment(
                request_id=request_id,
                risk_score=risk_score,
                risk_level=risk_level
            )
        except Exception as risk_error:
            logger.warning(f"Risk prediction failed (non-critical): {risk_error}")
        
        # Generate resolution options
        simulation_result = None
        simulated_options = None
        llm_generation_failed = False
        llm_error_message = None
        
        try:
            # Get resident history for context
            from app.services.database import get_requests_by_resident
            resident_history = get_requests_by_resident(request.resident_id)
            resident_history_dicts = [
                {
                    'category': req.category.value if hasattr(req.category, 'value') else str(req.category),
                    'urgency': req.urgency.value if hasattr(req.urgency, 'value') else str(req.urgency),
                    'message_text': req.message_text,
                    'status': req.status.value if hasattr(req.status, 'value') else str(req.status),
                    'created_at': req.created_at.isoformat() if isinstance(req.created_at, datetime) else str(req.created_at)
                }
                for req in resident_history[-5:]  # Last 5 requests
            ]
            
            # Generate options using AGENTIC approach (LLM + Tools)
            simulation_options = await simulator.generate_options(
                category=final_category,
                urgency=final_urgency,
                message_text=request.message_text,
                resident_id=request.resident_id,
                risk_score=risk_score if risk_score is not None else 0.5,
                resident_history=resident_history_dicts if resident_history_dicts else None
            )
            
            # Convert to dict for storage
            simulated_options = [
                {
                    "option_id": opt.option_id,
                    "action": opt.action,
                    "estimated_cost": opt.estimated_cost,
                    "estimated_time": opt.estimated_time,
                    "reasoning": opt.reasoning,
                    "source_doc_ids": opt.source_doc_ids,
                    "resident_satisfaction_impact": opt.resident_satisfaction_impact,
                    "steps": opt.steps
                }
                for opt in simulation_options
            ]
            
            simulation_result = SimulationResponse(
                options=simulation_options,
                issue_id=f"agentic_{final_category.value}_{final_urgency.value}_{request.resident_id}"
            )
            logger.info(f"Agentic simulation generated {len(simulated_options)} options")
        
        except HTTPException as http_error:
            # LLM generation failed - capture error for user display
            llm_generation_failed = True
            error_detail = http_error.detail if isinstance(http_error.detail, dict) else {'user_message': str(http_error.detail)}
            llm_error_message = error_detail.get('user_message', 'Unable to generate resolution options.')
            logger.error(f"LLM generation failed: {llm_error_message}")
        
        except Exception as sim_error:
            # Unexpected error
            llm_generation_failed = True
            llm_error_message = 'We encountered an unexpected error while analyzing your request. Please escalate this issue to a human administrator.'
            logger.error(f"Simulation failed with unexpected error: {sim_error}")
        
        # If LLM generation failed, still create request in database for escalation
        if llm_generation_failed:
            request_id = generate_request_id()
            now = datetime.now(timezone.utc)
            
            # Create request with status SUBMITTED (will be escalated when user selects escalation)
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
                simulated_options=None,  # No options generated
                created_at=now,
                updated_at=now
            )
            
            success = create_request(resident_request)
            if not success:
                logger.error(f"Failed to create request for LLM failure case: {request_id}")
            
            # Send to SQS if available
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
                        "simulated_options": None,
                        "submitted_at": now.isoformat(),
                        "llm_generation_failed": True
                    }
                    sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
                except Exception as sqs_error:
                    logger.warning(f"SQS enqueue failed for LLM error case (non-critical): {sqs_error}")
            
            return {
                "status": "error",
                "error_type": "LLM_GENERATION_FAILED",
                "message": llm_error_message,
                "escalation_required": True,
                "request_id": request_id,  # Include request_id so frontend can escalate
                "classification": {
                    "category": final_category.value,
                    "urgency": final_urgency.value,
                    "intent": classification.intent.value,
                    "confidence": classification.confidence
                },
                "risk_assessment": {
                    "risk_forecast": risk_score,
                    "risk_level": "High" if risk_score and risk_score > 0.7 else "Medium" if risk_score and risk_score > 0.3 else "Low" if risk_score else "Unknown"
                } if risk_score is not None else None,
                "action_required": "Please escalate this request to a human administrator using the 'Escalate to Human' option."
            }
        
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
            # Step 4: Get AI recommendation (but don't execute yet)
            recommended_option_id = None
            try:
                decision_request = DecisionRequest(
                    classification=classification,
                    simulation=simulation_result,
                    weights=PolicyWeights(),
                    config=PolicyConfiguration()
                )
                decision_result = await make_decision(request=decision_request)
                recommended_option_id = decision_result.chosen_option_id
                logger.info(f"AI recommended option: {recommended_option_id}")
            except Exception as decision_error:
                logger.warning(f"Decision recommendation failed (non-critical): {decision_error}")
            
            response_data["simulation"] = {
                "options_generated": len(simulation_result.options),
                "options": simulated_options,
                "recommended_option_id": recommended_option_id
            }
            
            # Log simulation to CloudWatch
            log_simulation_result(
                request_id=request_id,
                option_count=len(simulation_result.options),
                recommended_option_id=recommended_option_id,
                is_repeat=False
            )
            
            # Store recommended option in database
            if recommended_option_id:
                from app.services.database import get_table
                try:
                    table = get_table()
                    table.update_item(
                        Key={'request_id': request_id},
                        UpdateExpression='SET recommended_option_id = :rec_opt',
                        ExpressionAttributeValues={
                            ':rec_opt': recommended_option_id
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update recommended option: {e}")
        
        # Log final request submission to CloudWatch
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
        # Log error to CloudWatch
        log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            context={
                'request_id': request_id if 'request_id' in locals() else 'unknown',
                'resident_id': request.resident_id,
                'endpoint': '/submit-request'
            }
        )
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.post("/select-option")
async def select_option(selection: SelectOptionRequest):
    """
    Resident selects an option from the 3 simulated options, or escalates to human.
    This triggers execution.
    """
    try:
        from app.services.database import get_table, get_request_by_id
        
        # Get the request
        request = get_request_by_id(selection.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Special handling for human escalation
        if selection.selected_option_id == "escalate_to_human":
            # Update request with escalation
            table = get_table()
            table.update_item(
                Key={'request_id': selection.request_id},
                UpdateExpression='SET user_selected_option_id = :sel_opt, #status = :status, updated_at = :updated',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':sel_opt': "escalate_to_human",
                    ':status': Status.ESCALATED.value,
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return {
                "status": "escalated",
                "message": "Your request has been escalated to a human staff member. You'll receive a response within 24 hours.",
                "request_id": selection.request_id,
                "selected_option": {
                    "option_id": "escalate_to_human",
                    "action": "Escalate to Human Support",
                    "estimated_cost": 0,
                    "estimated_time": 24.0,
                    "reasoning": "Manual escalation requested by resident"
                }
            }
        
        # Normal option selection flow
        simulated_options = request.get('simulated_options', [])
        if not simulated_options:
            raise HTTPException(status_code=400, detail="No options available for this request")
        
        selected_option = next(
            (opt for opt in simulated_options if opt['option_id'] == selection.selected_option_id),
            None
        )
        
        if not selected_option:
            raise HTTPException(status_code=400, detail="Invalid option ID")
        
        # Update request with user's selection
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
        
        # Execute the selected option (simulate execution)
        execution_result = {
            "status": "executed",
            "action_taken": selected_option['action'],
            "estimated_cost": selected_option['estimated_cost'],
            "estimated_time": selected_option.get('estimated_time', selected_option.get('time_to_resolution', 1.0)),
            "message": f"Executing: {selected_option['action']}"
        }
        
        return {
            "status": "success",
            "message": "Option selected and execution initiated",
            "request_id": selection.request_id,
            "selected_option": selected_option,
            "execution": execution_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting option: {e}")
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")


@router.post("/resolve-request")
async def resolve_request(resolve_data: ResolveRequestModel):
    """
    Mark a request as resolved by admin or resident.
    """
    try:
        from app.services.database import get_table, get_request_by_id
        
        # Get the request
        request = get_request_by_id(resolve_data.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Update request status to Resolved
        table = get_table()
        now = datetime.now(timezone.utc)
        
        table.update_item(
            Key={'request_id': resolve_data.request_id},
            UpdateExpression='SET #status = :status, resolved_by = :resolved_by, resolved_at = :resolved_at, resolution_notes = :notes, updated_at = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': Status.RESOLVED.value,
                ':resolved_by': resolve_data.resolved_by,
                ':resolved_at': now.isoformat(),
                ':notes': resolve_data.resolution_notes or '',
                ':updated': now.isoformat()
            }
        )
        
        logger.info(f"Request {resolve_data.request_id} marked as resolved by {resolve_data.resolved_by}")
        
        return {
            "status": "success",
            "message": f"Request resolved by {resolve_data.resolved_by}",
            "request_id": resolve_data.request_id,
            "resolved_at": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving request: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving request: {str(e)}")
