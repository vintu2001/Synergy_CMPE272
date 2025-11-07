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
from app.services.governance import log_decision  # Added for Ticket 15
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
                await update_request_status(request_id, new_status)
                
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


@router.post("/select-option")
async def select_option(selection: SelectOptionRequest):
    """
    Resident selects an option from the 3 simulated options, or escalates to human.
    This triggers execution and governance logging.
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
                    "time_to_resolution": 24.0,
                    "resident_satisfaction_impact": 0.95
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
            "estimated_time": selected_option['time_to_resolution'],
            "message": f"Executing: {selected_option['action']}"
        }
        
        # Log to governance system
        try:
            from app.models.schemas import DecisionResponse, ClassificationResponse, IssueCategory, Urgency, Intent
            
            # Create a decision response from user's selection
            decision_result = DecisionResponse(
                chosen_action=selected_option['action'],
                chosen_option_id=selection.selected_option_id,
                reasoning=f"User selected this option from {len(simulated_options)} available options.",
                alternatives_considered=[opt['option_id'] for opt in simulated_options if opt['option_id'] != selection.selected_option_id],
                policy_scores={opt['option_id']: 0.0 for opt in simulated_options},
                escalation_reason=None
            )
            
            # Reconstruct classification
            classification = ClassificationResponse(
                category=IssueCategory(request['category']),
                urgency=Urgency(request['urgency']),
                intent=Intent(request['intent']),
                confidence=request.get('classification_confidence', 0.9),
                message_text=request.get('message_text', '')
            )
            
            # Log decision
            estimated_cost = selected_option['estimated_cost']
            estimated_time = selected_option['time_to_resolution']
            config = PolicyConfiguration()
            
            await log_decision(
                request_id=selection.request_id,
                resident_id=request['resident_id'],
                decision=decision_result,
                classification=classification,
                risk_score=request.get('risk_forecast'),
                total_options_simulated=len(simulated_options),
                estimated_cost=estimated_cost,
                estimated_time=estimated_time,
                exceeds_budget_threshold=estimated_cost > config.max_cost,
                exceeds_time_threshold=estimated_time > config.max_time,
                policy_weights=PolicyWeights().dict()
            )
            
            logger.info(f"User selection logged to governance for request {selection.request_id}")
        except Exception as gov_error:
            logger.warning(f"Governance logging failed (non-critical): {gov_error}")
        
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
