"""
Decision & Simulation API routes
Handles resolution option simulation, decision making, and question answering.
"""
import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.schemas import (
    SimulationRequest, SimulationResponse, DecisionRequest, DecisionResponse,
    IssueCategory, Urgency
)
from app.agents.simulation_agent import simulator
from app.agents.decision_agent import make_decision
from app.rag.retriever import answer_question
from app.utils.cloudwatch_logger import log_to_cloudwatch

router = APIRouter()
logger = logging.getLogger(__name__)


class AnswerQuestionRequest(BaseModel):
    question: str = Field(..., description="The question to answer")
    resident_id: str = Field(..., description="Resident identifier")
    category: Optional[str] = Field(None, description="Optional category for filtering")
    building_id: Optional[str] = Field(None, description="Optional building ID for context")


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_endpoint(request: SimulationRequest) -> SimulationResponse:
    """
    Generate resolution options using simulation agent.
    """
    try:
        category = IssueCategory(request.category)
        urgency = Urgency(request.urgency)
        
        result = await simulator.generate_options(
            category=category,
            urgency=urgency,
            message_text=request.message_text,
            resident_id=request.resident_id,
            risk_score=request.risk_score,
            resident_history=request.resident_history
        )
        
        options = result.get('options', [])
        is_recurring = result.get('is_recurring', False)
        
        issue_id = f"agentic_{category.value}_{urgency.value}_{request.resident_id}"
        
        log_to_cloudwatch('simulation_completed', {
            'resident_id': request.resident_id,
            'category': category.value,
            'urgency': urgency.value,
            'risk_score': round(request.risk_score, 3) if request.risk_score else None,
            'options_generated': len(options),
            'option_actions': [opt.action[:50] if hasattr(opt, 'action') else str(opt)[:50] for opt in options[:3]],
            'issue_id': issue_id
        })

        return SimulationResponse(
            options=options,
            issue_id=issue_id,
            is_recurring=is_recurring
        )
        
    except Exception as e:
        log_to_cloudwatch('simulation_error', {
            'resident_id': request.resident_id,
            'category': request.category,
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/decide", response_model=DecisionResponse)
async def decide_endpoint(request: DecisionRequest) -> DecisionResponse:
    """
    Make a decision on which option to choose.
    """
    try:
        result = await make_decision(request=request)
        logger.info(f"✓ Decision result received: {result.decision.chosen_option_id if result and result.decision else 'None'}")
        
        try:
            log_to_cloudwatch('decision_made', {
                'chosen_option_id': result.decision.chosen_option_id,
                'chosen_action': result.decision.chosen_action[:100],
                'estimated_cost': result.decision.estimated_cost,
                'estimated_time': result.decision.estimated_time,
                'alternatives_considered': len(result.decision.alternatives_considered) if result.decision.alternatives_considered else 0,
                'reasoning_preview': result.decision.reasoning[:150] if result.decision.reasoning else None
            })
        except Exception as cw_error:
            logger.warning(f"CloudWatch logging failed (non-critical): {cw_error}")
        
        return result.decision
    except Exception as e:
        logger.error(f"❌ Decision endpoint failed: {str(e)}", exc_info=True)
        try:
            log_to_cloudwatch('decision_error', {
                'error': str(e)
            })
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Decision failed: {str(e)}")


@router.post("/answer-question")
async def answer_question_endpoint(request: AnswerQuestionRequest) -> Dict[str, Any]:
    """
    Answer a resident's question directly using RAG retrieval.
    This endpoint is used when intent is ANSWER_QUESTION.
    """
    try:
        result = await answer_question(
            question=request.question,
            building_id=request.building_id,
            category=request.category,
            top_k=5
        )
        
        log_to_cloudwatch('question_answered', {
            'resident_id': request.resident_id,
            'question_preview': request.question[:100],
            'category': request.category,
            'sources_count': len(result.get('sources', [])),
            'answer_length': len(result.get('answer', ''))
        })
        
        return result
    except Exception as e:
        log_to_cloudwatch('question_answer_error', {
            'resident_id': request.resident_id,
            'question_preview': request.question[:100],
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")
