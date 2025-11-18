"""
Request Orchestrator
Coordinates request submission flow across microservices using HTTP calls.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MessageRequest, Status, ResidentRequest, SelectOptionRequest, ResolveRequestModel
)
from app.services.database import create_request, get_request_by_id, get_table
from app.utils.helpers import generate_request_id
from datetime import datetime, timezone
import httpx
import os
import json
import boto3
import logging
import time
import re

logger = logging.getLogger(__name__)
router = APIRouter()

# Service URLs
AI_PROCESSING_URL = os.getenv("AI_PROCESSING_SERVICE_URL", "http://localhost:8002")
DECISION_SIMULATION_URL = os.getenv("DECISION_SIMULATION_SERVICE_URL", "http://localhost:8003")
EXECUTION_URL = os.getenv("EXECUTION_SERVICE_URL", "http://localhost:8004")

# AWS Configuration
REGION = os.getenv("AWS_REGION", "us-west-2")
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
    Orchestrates calls to AI Processing and Decision & Simulation services.
    """
    start_time = time.time()
    request_id = generate_request_id()
    
    try:
        from app.utils.cloudwatch_logger import log_to_cloudwatch
        
        log_to_cloudwatch('request_submitted', {
            'request_id': request_id,
            'resident_id': request.resident_id,
            'message_preview': request.message_text[:100] if len(request.message_text) > 100 else request.message_text,
            'message_length': len(request.message_text)
        })
        
        logger.info(f"Processing request {request_id} for resident: {request.resident_id}")
        _normalized_text = normalize_text(request.message_text)
        
        # Classification
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                classify_response = await client.post(
                    f"{AI_PROCESSING_URL}/api/v1/classify",
                    json={
                        "resident_id": request.resident_id,
                        "message_text": request.message_text
                    }
                )
                classify_response.raise_for_status()
                classification_data = classify_response.json()
        except httpx.HTTPError as e:
            logger.error(f"Classification service error: {e}")
            raise HTTPException(status_code=503, detail="Classification service unavailable")
        
        # Extract classification
        from app.models.schemas import IssueCategory, Urgency, Intent
        final_category = request.category if request.category else IssueCategory(classification_data["category"])
        final_urgency = request.urgency if request.urgency else Urgency(classification_data["urgency"])
        intent = Intent(classification_data["intent"])
        confidence = classification_data["confidence"]
        
        log_to_cloudwatch('request_classified', {
            'request_id': request_id,
            'resident_id': request.resident_id,
            'category': final_category.value,
            'urgency': final_urgency.value,
            'intent': intent.value,
            'confidence': round(confidence, 3)
        })
        
        # Handle ANSWER_QUESTION intent - return direct answer via RAG
        if intent == Intent.ANSWER_QUESTION:
            logger.info(f"Intent is ANSWER_QUESTION - using RAG to answer directly")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    answer_response = await client.post(
                        f"{DECISION_SIMULATION_URL}/api/v1/answer-question",
                        json={
                            "question": request.message_text,
                            "resident_id": request.resident_id,
                            "category": final_category.value if final_category else None,
                            "building_id": request.resident_id.split("_")[1] if "_" in request.resident_id else None
                        }
                    )
                    answer_response.raise_for_status()
                    answer_data = answer_response.json()
                    
                    # Create a request record for tracking
                    now = datetime.now(timezone.utc)
                    resident_request = ResidentRequest(
                        request_id=request_id,
                        resident_id=request.resident_id,
                        message_text=request.message_text,
                        category=final_category,
                        urgency=final_urgency,
                        intent=intent,
                        status=Status.RESOLVED,  # Questions are immediately resolved
                        risk_forecast=None,
                        classification_confidence=confidence,
                        simulated_options=None,
                        created_at=now,
                        updated_at=now
                    )
                    create_request(resident_request)
                    
                    return {
                        "status": "answered",
                        "message": "Question answered successfully",
                        "request_id": request_id,
                        "classification": {
                            "category": final_category.value,
                            "urgency": final_urgency.value,
                            "intent": intent.value,
                            "confidence": confidence
                        },
                        "answer": {
                            "text": answer_data.get("answer", "I couldn't generate an answer."),
                            "source_docs": answer_data.get("source_docs", []),
                            "confidence": answer_data.get("confidence", 0.0)
                        }
                    }
            except httpx.HTTPError as e:
                logger.error(f"Answer question service error: {e}")
                # Fallback to normal flow if answer service fails
                logger.warning("Falling back to normal request flow")
            except Exception as answer_error:
                logger.error(f"Error answering question: {answer_error}")
                # Fallback to normal flow
        
        # Risk Prediction
        risk_score = None
        recurrence_prob = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                risk_response = await client.post(
                    f"{AI_PROCESSING_URL}/api/v1/predict-risk",
                    json={
                        "category": classification_data["category"],
                        "urgency": classification_data["urgency"],
                        "intent": classification_data["intent"],
                        "confidence": confidence,
                        "message_text": request.message_text
                    }
                )
                risk_response.raise_for_status()
                risk_data = risk_response.json()
                risk_score = risk_data.get("risk_forecast")
                recurrence_prob = risk_data.get("recurrence_probability")
                rec_str = f"{recurrence_prob:.4f}" if recurrence_prob is not None else "N/A"
                logger.info(f"Risk prediction successful: risk={risk_score:.4f}, recurrence={rec_str}")
        except Exception as risk_error:
            logger.warning(f"Risk prediction failed (non-critical): {risk_error}")
        
        # Generate Resolution Options
        simulation_result = None
        simulated_options = None
        llm_generation_failed = False
        llm_error_message = None
        is_recurring = False  # Default to False
        
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
                for req in resident_history[-5:]
            ]
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                simulate_response = await client.post(
                    f"{DECISION_SIMULATION_URL}/api/v1/simulate",
                    json={
                        "category": final_category.value,
                        "urgency": final_urgency.value,
                        "message_text": request.message_text,
                        "resident_id": request.resident_id,
                        "risk_score": risk_score if risk_score is not None else 0.5,
                        "resident_history": resident_history_dicts if resident_history_dicts else None
                    }
                )
                simulate_response.raise_for_status()
                simulation_data = simulate_response.json()
                
                # Extract is_recurring flag from simulation response
                is_recurring = simulation_data.get("is_recurring", False)
                
                simulated_options = [
                    {
                        "option_id": opt["option_id"],
                        "action": opt["action"],
                        "estimated_cost": opt["estimated_cost"],
                        "estimated_time": opt["estimated_time"],
                        "reasoning": opt["reasoning"],
                        "source_doc_ids": opt.get("source_doc_ids", []),
                        "resident_satisfaction_impact": opt.get("resident_satisfaction_impact"),
                        "steps": opt.get("steps", [])
                    }
                    for opt in simulation_data["options"]
                ]
                logger.info(f"Simulation generated {len(simulated_options)} options")
        
        except httpx.HTTPStatusError as http_error:
            llm_generation_failed = True
            error_detail = http_error.response.json() if http_error.response else {}
            llm_error_message = error_detail.get('detail', 'Unable to generate resolution options.')
            logger.error(f"LLM generation failed: {llm_error_message}")
        except Exception as sim_error:
            llm_generation_failed = True
            llm_error_message = 'We encountered an unexpected error while analyzing your request. Please escalate this issue to a human administrator.'
            logger.error(f"Simulation failed: {sim_error}")
        
        # If LLM generation failed, still create request in database for escalation
        if llm_generation_failed:
            now = datetime.now(timezone.utc)
            resident_request = ResidentRequest(
                request_id=request_id,
                resident_id=request.resident_id,
                message_text=request.message_text,
                category=final_category,
                urgency=final_urgency,
                intent=intent,
                status=Status.SUBMITTED,
                risk_forecast=risk_score,
                classification_confidence=confidence,
                simulated_options=None,
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
                        "intent": intent.value,
                        "risk_forecast": risk_score,
                        "simulated_options": None,
                        "submitted_at": now.isoformat(),
                        "llm_generation_failed": True
                    }
                    sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
                except Exception as sqs_error:
                    logger.warning(f"SQS enqueue failed (non-critical): {sqs_error}")
            
            return {
                "status": "error",
                "error_type": "LLM_GENERATION_FAILED",
                "message": llm_error_message,
                "escalation_required": True,
                "request_id": request_id,
                "classification": {
                    "category": final_category.value,
                    "urgency": final_urgency.value,
                    "intent": intent.value,
                    "confidence": confidence
                },
                "risk_assessment": {
                    "risk_forecast": risk_score,
                    "recurrence_probability": recurrence_prob,
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
            intent=intent,
            status=Status.SUBMITTED,
            risk_forecast=risk_score,
            classification_confidence=confidence,
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
                    "intent": intent.value,
                    "risk_forecast": risk_score,
                    "simulated_options": simulated_options,
                    "submitted_at": now.isoformat(),
                }
                sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
            except Exception as sqs_error:
                logger.warning(f"SQS enqueue failed (non-critical): {sqs_error}")
        
        # Get AI recommendation
        recommended_option_id = None
        decision_data = None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                decision_response = await client.post(
                    f"{DECISION_SIMULATION_URL}/api/v1/decide",
                    json={
                        "classification": classification_data,
                        "simulation": simulation_data,
                        "weights": {
                            "urgency_weight": 0.4,
                            "cost_weight": 0.3,
                            "time_weight": 0.2,
                            "satisfaction_weight": 0.1
                        },
                        "config": {
                            "max_cost": 1000.0,
                            "max_time": 72.0
                        }
                    }
                )
                decision_response.raise_for_status()
                decision_data = decision_response.json()
                recommended_option_id = decision_data.get("chosen_option_id")
                logger.info(f"AI recommended option: {recommended_option_id}")
        except Exception as decision_error:
            logger.warning(f"Decision recommendation failed (non-critical): {decision_error}")
        
        # Store recommended option in database
        if recommended_option_id:
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
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Request {request_id} processed in {processing_time:.2f}ms")
        

        # Log request completion summary
        log_to_cloudwatch('request_completed', {
            'request_id': request_id,
            'resident_id': request.resident_id,
            'category': final_category.value,
            'urgency': final_urgency.value,
            'intent': intent.value,
            'risk_score': round(risk_score, 3) if risk_score else None,
            'options_count': len(simulated_options) if simulated_options else 0,
            'recommended_option': recommended_option_id,
            'processing_time_ms': round(processing_time, 2),
            'status': 'success'
        })
        
        response = {
            "status": "submitted",
            "message": "Request submitted successfully!",
            "request_id": request_id,
            "classification": {
                "category": final_category.value,
                "urgency": final_urgency.value,
                "intent": intent.value,
                "confidence": confidence
            },
            "risk_assessment": {
                "risk_forecast": risk_score,
                "recurrence_probability": recurrence_prob,
                "risk_level": "High" if risk_score and risk_score > 0.7 else "Medium" if risk_score and risk_score > 0.3 else "Low" if risk_score else "Unknown"
            } if risk_score is not None else None,
            "simulation": {
                "options_generated": len(simulated_options),
                "options": simulated_options,
                "recommended_option_id": recommended_option_id,
                "is_recurring": is_recurring
            }
        }
        
        # Add decision data if available
        if decision_data:
            response["decision"] = decision_data
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.post("/select-option")
async def select_option(selection: SelectOptionRequest):
    """
    Resident selects an option from the simulated options, or escalates to human.
    This triggers execution.
    """
    try:
        from app.utils.cloudwatch_logger import log_to_cloudwatch
        
        # Get the request
        request = get_request_by_id(selection.request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Special handling for human escalation
        if selection.selected_option_id == "escalate_to_human":
            log_to_cloudwatch('request_escalated', {
                'request_id': selection.request_id,
                'escalation_type': 'manual',
                'reason': 'User selected escalation option'
            })
            
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
        
        log_to_cloudwatch('option_selected', {
            'request_id': selection.request_id,
            'selected_option_id': selection.selected_option_id,
            'option_action': selected_option.get('action', 'Unknown')[:100],
            'estimated_cost': selected_option.get('estimated_cost'),
            'estimated_time': selected_option.get('estimated_time')
        })
        
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
        
        # Execute the selected option (Execution Service)
        try:
            from app.models.schemas import IssueCategory
            category = IssueCategory(request.get('category', 'Maintenance'))
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                execution_response = await client.post(
                    f"{EXECUTION_URL}/api/v1/execute",
                    json={
                        "chosen_action": selected_option['action'],
                        "chosen_option_id": selection.selected_option_id,
                        "reasoning": selected_option.get('reasoning', ''),
                        "alternatives_considered": [],
                        "category": category.value
                    }
                )
                execution_response.raise_for_status()
                execution_result = execution_response.json()
        except Exception as exec_error:
            logger.warning(f"Execution service failed (non-critical): {exec_error}")
            execution_result = {
                "status": "executed",
                "action_taken": selected_option['action'],
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
        from app.utils.cloudwatch_logger import log_to_cloudwatch
        
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
        
        log_to_cloudwatch('request_resolved', {
            'request_id': resolve_data.request_id,
            'resolved_by': resolve_data.resolved_by,
            'resolution_notes': resolve_data.resolution_notes[:100] if resolve_data.resolution_notes else None
        })
        
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
