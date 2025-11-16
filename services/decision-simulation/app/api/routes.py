"""
Decision & Simulation API routes
Handles resolution option simulation, decision making, and question answering.
"""
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

router = APIRouter()


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
        
        options = await simulator.generate_options(
            category=category,
            urgency=urgency,
            message_text=request.message_text,
            resident_id=request.resident_id,
            risk_score=request.risk_score,
            resident_history=request.resident_history
        )
        
        issue_id = f"agentic_{category.value}_{urgency.value}_{request.resident_id}"
        
        return SimulationResponse(
            options=options,
            issue_id=issue_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/decide", response_model=DecisionResponse)
async def decide_endpoint(request: DecisionRequest) -> DecisionResponse:
    """
    Make a decision on which option to choose.
    """
    try:
        result = await make_decision(request=request)
        # Extract the decision from DecisionResponseWithStatus
        return result.decision
    except Exception as e:
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
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")
