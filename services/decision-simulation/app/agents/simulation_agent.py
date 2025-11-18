"""
Simulation Agent - AGENTIC VERSION
Generates context-aware resolution options using LLM and real-time tools.
No static templates - fully dynamic and intelligent.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import ClassificationResponse, SimulationResponse, SimulatedOption, IssueCategory, Urgency
from app.utils.llm_client import llm_client
from app.agents.tools import agent_tools
from app.agents.reasoning_engine import multi_step_reasoner
from app.agents.learning_engine import learning_engine
from app.rag.retriever import retrieve_relevant_docs  # RAG integration
from typing import List, Dict, Any, Optional
import logging
import os

import simpy
import random

logger = logging.getLogger(__name__)
router = APIRouter()


class AgenticResolutionSimulator:
    """
    Agentic Resolution Simulator - Generates options dynamically using LLM.
    Uses real-time tools to gather context and make intelligent decisions.
    """
    
    def __init__(self):
        self.llm_client = llm_client
        self.agent_tools = agent_tools
        self.multi_step_reasoner = multi_step_reasoner
        self.learning_engine = learning_engine
    
    async def generate_options(
        self, 
        category: IssueCategory, 
        urgency: Urgency,
        message_text: str,
        resident_id: str,
        risk_score: float = 0.5,
        resident_history: Optional[List[Dict]] = None
    ) -> List[SimulatedOption]:
        """
        Generate resolution options using LLM and real-time tools.
        This is the AGENTIC approach - no static templates!
        
        Args:
            category: Issue category
            urgency: Urgency level
            message_text: Original resident message
            resident_id: Resident identifier
            risk_score: Risk prediction score
            resident_history: Past requests from resident
        
        Returns:
            List of SimulatedOption objects
        
        Raises:
            HTTPException: If LLM fails and cannot generate options
        """
        logger.info(f"Generating agentic options for {category.value}/{urgency.value} (resident: {resident_id})")
        
        try:
            tools_data = await self.agent_tools.execute_tools(
                resident_id=resident_id,
                category=category,
                urgency=urgency.value,
                message_text=message_text
            )
            
            logger.info(f"Tools executed: {list(tools_data.keys())}")
            
            message_keywords = message_text.lower().split()[:10]
            learning_insights = await self.learning_engine.get_learning_insights_for_request(
                category=category.value,
                urgency=urgency.value,
                message_keywords=message_keywords
            )
            
            logger.info(f"Learning insights: {learning_insights.get('has_insights', False)}")
            
            tools_data['learning_insights'] = learning_insights
            
            complexity_analysis = await self.multi_step_reasoner.analyze_complexity(
                message_text=message_text,
                category=category.value,
                urgency=urgency.value,
                tools_data=tools_data
            )
            
            logger.info(f"Complexity analysis: {complexity_analysis.get('reasoning_required', 'single_step')} (score: {complexity_analysis.get('complexity_score', 0):.2f})")
            
            if complexity_analysis.get('is_complex') and complexity_analysis.get('complexity_score', 0) > 0.7:
                logger.info("Using multi-step reasoning for complex issue")
                
                reasoning_chain = await self.multi_step_reasoner.generate_reasoning_chain(
                    message_text=message_text,
                    category=category.value,
                    urgency=urgency.value,
                    risk_score=risk_score,
                    tools_data=tools_data,
                    complexity_analysis=complexity_analysis
                )
                
                phased_options = await self.multi_step_reasoner.create_phased_options(
                    reasoning_chain=reasoning_chain,
                    category=category.value,
                    urgency=urgency.value
                )
                
                if phased_options:
                    options = []
                    for phased_opt in phased_options:
                        option = SimulatedOption(
                            option_id=phased_opt['option_id'],
                            action=phased_opt['action'],
                            estimated_cost=float(phased_opt['estimated_cost']),
                            estimated_time=float(phased_opt.get('time_to_resolution', phased_opt.get('estimated_time', 1.0))),
                            reasoning=phased_opt.get('reasoning', 'Multi-step phased resolution approach'),
                            source_doc_ids=None
                        )
                        options.append(option)
                    
                    is_recurring_from_tools = tools_data.get('recurring', {}).get('is_recurring', False)
                    
                    logger.info(f"Generated {len(options)} phased options from multi-step reasoning (is_recurring={is_recurring_from_tools})")
                    return {
                        'options': options,
                        'is_recurring': is_recurring_from_tools
                    }
            
            rag_context = None
            building_id = None
            if resident_id and resident_id.startswith('RES_'):
                parts = resident_id.split('_')
                if len(parts) >= 3:
                    building_id = parts[1]
                    logger.info(f"Extracted building_id: {building_id} from resident_id: {resident_id}")
            
            rag_enabled = os.getenv('RAG_ENABLED', 'false').lower() == 'true'
            
            if rag_enabled:
                try:
                    rag_context = await retrieve_relevant_docs(
                        query=message_text,
                        category=category.value,
                        building_id=building_id,
                        top_k=int(os.getenv('RAG_TOP_K', '5')),
                        similarity_threshold=0.4
                    )
                    
                    if not rag_context or len(rag_context.retrieved_docs) == 0:
                        logger.warning(f"No RAG documents found with threshold 0.4, trying 0.3 for: '{message_text[:50]}...'")
                        rag_context = await retrieve_relevant_docs(
                            query=message_text,
                            category=category.value,
                            building_id=building_id,
                            top_k=int(os.getenv('RAG_TOP_K', '5')) * 2,
                            similarity_threshold=0.3
                        )
                    
                    if rag_context:
                        logger.info(f"RAG retrieval successful: {rag_context.total_retrieved} documents retrieved")
                    else:
                        logger.info("RAG retrieval returned no context (RAG may be disabled or unavailable)")
                
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}. Continuing without RAG context.")
                    rag_context = None
            else:
                logger.info("RAG is disabled (RAG_ENABLED=false)")
            
            llm_response = await self.llm_client.generate_options(
                message_text=message_text,
                category=category.value,
                urgency=urgency.value,
                risk_score=risk_score,
                resident_id=resident_id,
                resident_history=resident_history,
                tools_data=tools_data,
                rag_context=rag_context  # Pass RAG context to LLM
            )
            
            if 'error' in llm_response:
                error_info = llm_response['error']
                logger.error(f"LLM generation failed: {error_info['type']}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        'error_type': error_info['type'],
                        'error_message': error_info['message'],
                        'user_message': error_info['user_message'],
                        'escalation_required': True
                    }
                )
            
            is_recurring_from_tools = tools_data.get('recurring', {}).get('is_recurring', False)
            is_recurring_from_llm = llm_response.get('is_recurring', False)
            is_recurring = is_recurring_from_tools or is_recurring_from_llm
            
            if is_recurring_from_tools:
                logger.info(f"Recurring issue detected by tools: {tools_data.get('recurring')}")
            if is_recurring_from_llm:
                logger.info(f"Recurring issue detected by LLM")
            
            source_doc_ids = []
            if rag_context and rag_context.retrieved_docs:
                source_doc_ids = [doc['doc_id'] for doc in rag_context.retrieved_docs if 'doc_id' in doc]
            
            rag_fallback_needed = False
            if rag_enabled and (not rag_context or not rag_context.retrieved_docs or len(source_doc_ids) == 0):
                logger.warning(f"RAG enabled but no KB documents retrieved for category={category.value}, building_id={building_id}")
                logger.warning("Adding human escalation fallback due to missing KB context")
                rag_fallback_needed = True
            
            options = []
            for llm_option in llm_response['options']:
                # Create simple details for UI dropdown (single-step breakdown)
                simple_details = [{
                    'step': 1,
                    'title': 'What we\'ll do',
                    'description': llm_option['action'],
                    'time': f"{float(llm_option['time_to_resolution']):.1f}h",
                    'cost': f"${float(llm_option['estimated_cost']):.2f}"
                }]
                
                # Get satisfaction from LLM response
                llm_satisfaction = llm_option.get('resident_satisfaction_impact')
                if llm_satisfaction is None:
                    logger.warning(f"LLM did not provide resident_satisfaction_impact for {llm_option['option_id']}. Raw option: {llm_option}")
                    llm_satisfaction = 0.75  # Fallback only if LLM doesn't provide it
                
                # Get steps from LLM response
                llm_steps = llm_option.get('steps')
                if llm_steps and isinstance(llm_steps, list):
                    steps = llm_steps[:5]  # Limit to 5 steps
                else:
                    steps = None
                
                option = SimulatedOption(
                    option_id=llm_option['option_id'],
                    action=llm_option['action'],
                    estimated_cost=float(llm_option['estimated_cost']),
                    estimated_time=float(llm_option.get('time_to_resolution', llm_option.get('estimated_time', 1.0))),
                    reasoning=llm_option.get('reasoning', llm_option.get('action', 'Automated resolution option')),
                    source_doc_ids=source_doc_ids if source_doc_ids else None,  # RAG sources
                    resident_satisfaction_impact=float(llm_satisfaction),
                    steps=steps
                )
                options.append(option)
            
            if rag_fallback_needed:
                escalation_option = SimulatedOption(
                    option_id=f"OPT_ESCALATE_{len(options) + 1}",
                    action=f"Escalate to Human Administrator - No policy documentation found for this {category.value} issue. A human administrator should review this request to ensure proper handling according to building procedures.",
                    estimated_cost=75.0,  
                    estimated_time=1.5,  
                    reasoning="No relevant policy documents found in knowledge base. Human review required for proper handling.",
                    source_doc_ids=None,  # No KB sources available
                    resident_satisfaction_impact=0.85  # Human attention generally high satisfaction
                )
                options.append(escalation_option)
                logger.info(f"Added human escalation option due to missing RAG context (total options: {len(options)})")
            
            occurrence_count = None
            if is_recurring:
                occurrence_count = tools_data.get('recurring', {}).get('occurrence_count', 2)
                logger.info(f"Recurring issue detected (occurrence_count={occurrence_count}). Escalate to human option should be recommended.")
            
            logger.info(f"Successfully generated {len(options)} agentic options with {len(source_doc_ids)} RAG sources (is_recurring={is_recurring}, rag_fallback={rag_fallback_needed})")
            
            return {
                'options': options,
                'is_recurring': is_recurring,
                'occurrence_count': occurrence_count
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in agentic option generation: {e}")
            from app.utils.llm_client import log_error_to_cloudwatch
            log_error_to_cloudwatch(
                error_type="SIMULATOR_ERROR",
                error_message=str(e),
                context={
                    'resident_id': resident_id,
                    'category': category.value,
                    'urgency': urgency.value
                }
            )
            
            raise HTTPException(
                status_code=503,
                detail={
                    'error_type': 'SIMULATOR_ERROR',
                    'error_message': str(e),
                    'user_message': 'We encountered an unexpected error while analyzing your request. Please escalate this issue to a human administrator who can assist you immediately.',
                    'escalation_required': True
                }
            )


simulator = AgenticResolutionSimulator()


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_resolutions(
    classification: ClassificationResponse,
    message_text: str,
    resident_id: str,
    risk_score: float = 0.5,
    resident_history: Optional[List[Dict]] = None
) -> SimulationResponse:
    """
    Generate resolution options using AGENTIC approach (LLM + Tools).
    NO FALLBACK TO TEMPLATES - If LLM fails, returns error.
    
    Args:
        classification: Classified message with category, urgency
        message_text: Original resident message text
        resident_id: Resident identifier
        risk_score: Risk forecast score (0.0-1.0)
        resident_history: Past requests from resident (optional)
    
    Returns:
        SimulationResponse with 3 dynamically generated options
    
    Raises:
        HTTPException: If LLM fails to generate options
    """
    try:
        options = await simulator.generate_options(
            category=classification.category,
            urgency=classification.urgency,
            message_text=message_text,
            resident_id=resident_id,
            risk_score=risk_score,
            resident_history=resident_history
        )
        
        logger.info(f"Generated {len(options)} agentic options for {classification.category.value}/{classification.urgency.value}")
        
        return SimulationResponse(
            options=options,
            issue_id=f"agentic_{classification.category.value}_{classification.urgency.value}_{resident_id}"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in simulation endpoint: {e}")
        from app.utils.llm_client import log_error_to_cloudwatch
        log_error_to_cloudwatch(
            error_type="SIMULATION_ENDPOINT_ERROR",
            error_message=str(e),
            context={
                'resident_id': resident_id,
                'category': classification.category.value,
                'urgency': classification.urgency.value
            }
        )
        
        raise HTTPException(
            status_code=503,
            detail={
                'error_type': 'SIMULATION_ENDPOINT_ERROR',
                'error_message': str(e),
                'user_message': 'We are unable to process your request at this time. Please escalate this issue to a human administrator for immediate assistance.',
                'escalation_required': True
            }
        )

