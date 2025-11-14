"""
Simulation Agent - AGENTIC VERSION
Generates context-aware resolution options using LLM and real-time tools.
No static templates - fully dynamic and intelligent.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import ClassificationResponse, SimulationResponse, SimulatedOption, IssueCategory, Urgency
from app.utils.llm_client import llm_client
from app.agents.tools import agent_tools
from app.agents.reasoning_engine import multi_step_reasoner  # Level 3
from app.agents.learning_engine import learning_engine  # Level 4
from app.rag.retriever import retrieve_for_simulation  # RAG integration with MMR
from app.prompts.utils import truncate_context_documents  # Step 10.2: Context truncation
from app.utils.numerics_calculator import add_numerics_to_option, calculate_satisfaction  # Step 10.4: Numerics
from typing import List, Dict, Any, Optional
import logging
import time  # Step 10.8: Performance logging

from app.config import get_settings

import simpy
import random

logger = logging.getLogger(__name__)
router = APIRouter()

# Get configuration from centralized settings
settings = get_settings()


class AgenticResolutionSimulator:
    """
    Agentic Resolution Simulator - Generates options dynamically using LLM.
    Uses real-time tools to gather context and make intelligent decisions.
    """
    
    def __init__(self):
        self.llm_client = llm_client
        self.agent_tools = agent_tools
        self.multi_step_reasoner = multi_step_reasoner  # Level 3
        self.learning_engine = learning_engine  # Level 4
    
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
        
        # Step 10.8: Start performance timer
        pipeline_start_time = time.time()
        
        try:
            # Step 1: Execute tools to gather real-time context (Level 2)
            tools_data = await self.agent_tools.execute_tools(
                resident_id=resident_id,
                category=category,
                urgency=urgency.value,
                message_text=message_text
            )
            
            logger.info(f"Tools executed: {list(tools_data.keys())}")
            
            # Step 2: Get learning insights from historical data (Level 4)
            message_keywords = message_text.lower().split()[:10]  # First 10 words
            learning_insights = await self.learning_engine.get_learning_insights_for_request(
                category=category.value,
                urgency=urgency.value,
                message_keywords=message_keywords
            )
            
            logger.info(f"Learning insights: {learning_insights.get('has_insights', False)}")
            
            # Add learning insights to tools_data
            tools_data['learning_insights'] = learning_insights
            
            # Step 3: Analyze complexity for multi-step reasoning (Level 3)
            complexity_analysis = await self.multi_step_reasoner.analyze_complexity(
                message_text=message_text,
                category=category.value,
                urgency=urgency.value,
                tools_data=tools_data
            )
            
            logger.info(f"Complexity analysis: {complexity_analysis.get('reasoning_required', 'single_step')} (score: {complexity_analysis.get('complexity_score', 0):.2f})")
            
            # Step 4: If complex (score > 0.7), generate multi-step reasoning chain (Level 3)
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
                
                # Generate phased options from reasoning chain
                phased_options = await self.multi_step_reasoner.create_phased_options(
                    reasoning_chain=reasoning_chain,
                    category=category.value,
                    urgency=urgency.value
                )
                
                if phased_options:
                    # Convert phased options to SimulatedOption objects
                    options = []
                    for phased_opt in phased_options:
                        option = SimulatedOption(
                            option_id=phased_opt['option_id'],
                            action=phased_opt['action'],
                            estimated_cost=float(phased_opt['estimated_cost']),
                            estimated_time=float(phased_opt.get('time_to_resolution', phased_opt.get('estimated_time', 1.0))),
                            reasoning=phased_opt.get('reasoning', 'Multi-step phased resolution approach'),
                            source_doc_ids=None  # Phased options from reasoning, not RAG
                        )
                        options.append(option)
                    
                    logger.info(f"Generated {len(options)} phased options from multi-step reasoning")
                    return options
            
            # Step 5: Retrieve relevant documents from knowledge base (RAG integration)
            rag_context = None
            building_id = None
            
            # Extract building_id from resident_id (format: RES_BuildingXYZ_1001)
            if resident_id and resident_id.startswith('RES_'):
                parts = resident_id.split('_')
                if len(parts) >= 3:
                    building_id = parts[1]
                    logger.info(f"Extracted building_id: {building_id} from resident_id: {resident_id}")
            
            # Check if RAG is enabled
            rag_enabled = settings.RAG_ENABLED
            
            if rag_enabled:
                try:
                    # Step 10.1: Retrieve relevant documents using MMR for diverse simulation options
                    # Explicitly request policy, SOP, and cost documents for grounded options
                    rag_context = await retrieve_for_simulation(
                        issue_text=message_text,
                        building_id=building_id,
                        category=category.value,
                        doc_types=["policy", "sop", "cost"],  # Explicit doc types for Step 10
                        k=settings.RETRIEVAL_K
                    )
                    
                    if rag_context:
                        logger.info(f"RAG retrieval successful: {rag_context.total_retrieved} documents retrieved (types: policy, sop, cost)")
                        
                        # Step 10.2: Truncate context to MAX_CONTEXT_TOKENS if needed
                        if rag_context.retrieved_docs:
                            original_count = len(rag_context.retrieved_docs)
                            truncated_docs = truncate_context_documents(
                                documents=rag_context.retrieved_docs,
                                max_tokens=settings.MAX_CONTEXT_TOKENS,
                                preserve_first=2  # Always keep at least 2 most relevant docs
                            )
                            rag_context.retrieved_docs = truncated_docs
                            
                            if len(truncated_docs) < original_count:
                                logger.info(
                                    f"Context truncated: {original_count} -> {len(truncated_docs)} docs "
                                    f"to fit MAX_CONTEXT_TOKENS={settings.MAX_CONTEXT_TOKENS}"
                                )
                    else:
                        logger.info("RAG retrieval returned no context (RAG may be disabled or unavailable)")
                
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}. Continuing without RAG context.")
                    rag_context = None
            else:
                logger.info("RAG is disabled (RAG_ENABLED=false)")
            
            # Step 6: Generate options using LLM with full context (Level 1)
            # This is used for non-complex issues or as fallback
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
            
            # Check for errors
            if 'error' in llm_response:
                error_info = llm_response['error']
                logger.error(f"LLM generation failed: {error_info['type']}")
                
                # Return error to be handled by caller - NO FALLBACK TO TEMPLATES
                raise HTTPException(
                    status_code=503,
                    detail={
                        'error_type': error_info['type'],
                        'error_message': error_info['message'],
                        'user_message': error_info['user_message'],
                        'escalation_required': True
                    }
                )
            
            # Step 7: Convert LLM response to SimulatedOption objects
            # Extract source document IDs from RAG context
            source_doc_ids = []
            if rag_context and rag_context.retrieved_docs:
                # Collect all document IDs from retrieved context
                source_doc_ids = [doc['doc_id'] for doc in rag_context.retrieved_docs if 'doc_id' in doc]
            
            # Step 7.1: Check for RAG fallback - if RAG enabled but no documents retrieved
            # This indicates the system lacks knowledge base context for this request
            rag_fallback_needed = False
            if rag_enabled and (not rag_context or not rag_context.retrieved_docs or len(source_doc_ids) == 0):
                logger.warning(f"RAG enabled but no KB documents retrieved for category={category.value}, building_id={building_id}")
                logger.warning("Adding human escalation fallback due to missing KB context")
                rag_fallback_needed = True
            
            options = []
            for llm_option in llm_response['options']:
                # Step 10.4: Add numerics (cost, eta, satisfaction) to each option
                enhanced_option = add_numerics_to_option(
                    option_dict=llm_option,
                    category=category.value,
                    urgency=urgency.value
                )
                
                # Create simple details for UI dropdown (single-step breakdown)
                simple_details = [{
                    'step': 1,
                    'title': 'What we\'ll do',
                    'description': enhanced_option['action'],
                    'time': f"{float(enhanced_option['estimated_time']):.1f}h",
                    'cost': f"${float(enhanced_option['estimated_cost']):.2f}"
                }]
                
                option = SimulatedOption(
                    option_id=enhanced_option['option_id'],
                    action=enhanced_option['action'],
                    estimated_cost=float(enhanced_option['estimated_cost']),
                    estimated_time=float(enhanced_option['estimated_time']),
                    reasoning=enhanced_option.get('reasoning', enhanced_option.get('action', 'Automated resolution option')),
                    source_doc_ids=source_doc_ids if source_doc_ids else None,  # RAG sources
                    satisfaction_score=float(enhanced_option['satisfaction_score'])  # Step 10.4
                )
                options.append(option)
            
            # Step 7.2: Add human escalation option if RAG fallback needed
            if rag_fallback_needed:
                escalation_option = SimulatedOption(
                    option_id=f"OPT_ESCALATE_{len(options) + 1}",
                    action=f"Escalate to Human Administrator - No policy documentation found for this {category.value} issue. A human administrator should review this request to ensure proper handling according to building procedures.",
                    estimated_cost=0.0,
                    estimated_time=0.5,  # 30 minutes for admin review
                    reasoning="No relevant policy documents found in knowledge base. Human review required for proper handling.",
                    source_doc_ids=None,  # No KB sources available
                    satisfaction_score=0.85  # Human escalation generally well-received
                )
                options.append(escalation_option)
                logger.info(f"Added human escalation option due to missing RAG context (total options: {len(options)})")
            
            # Step 10.6: Validate minimum 3 options
            if len(options) < 3:
                logger.warning(f"Only {len(options)} options generated, minimum is 3. Adding fallback options.")
                fallback_count = 3 - len(options)
                for i in range(fallback_count):
                    fallback_option = SimulatedOption(
                        option_id=f"OPT_FALLBACK_{len(options) + 1}",
                        action=f"Standard {category.value} Resolution - Apply standard procedure for {category.value} issues as per building policy.",
                        estimated_cost=200.0 + (i * 50),  # Vary cost slightly
                        estimated_time=24.0 - (i * 4),  # Vary time slightly
                        reasoning=f"Fallback option {i+1} - Standard resolution path when insufficient specific options generated.",
                        source_doc_ids=source_doc_ids[:1] if source_doc_ids else None,  # Use first doc if available
                        satisfaction_score=0.70 - (i * 0.05)  # Slightly lower satisfaction for fallbacks
                    )
                    options.append(fallback_option)
                logger.info(f"Added {fallback_count} fallback options to meet minimum requirement (total: {len(options)})")
            
            # Step 10.7: Validate doc_id citations - ensure each option has at least one source
            for option in options:
                if not option.source_doc_ids or len(option.source_doc_ids) == 0:
                    logger.warning(f"Option {option.option_id} has no source citations")
                    # Assign first available doc_id from RAG context as fallback
                    if source_doc_ids and len(source_doc_ids) > 0:
                        option.source_doc_ids = [source_doc_ids[0]]
                        logger.info(f"Assigned fallback doc_id to option {option.option_id}: {source_doc_ids[0]}")
                    else:
                        # No RAG docs available - mark with placeholder
                        option.source_doc_ids = ["NO_KB_SOURCE"]
                        logger.warning(f"Option {option.option_id} marked with NO_KB_SOURCE (no RAG documents available)")
            
            # Step 10.8: Log pipeline performance
            pipeline_duration = time.time() - pipeline_start_time
            logger.info(
                f"✓ Simulation pipeline completed in {pipeline_duration:.2f}s "
                f"({len(options)} options, {len(source_doc_ids)} RAG sources)"
            )
            
            # Warn if exceeding 3s budget for gemini-1.5-flash
            if pipeline_duration > 3.0:
                logger.warning(
                    f"⚠ Pipeline exceeded 3s budget: {pipeline_duration:.2f}s. "
                    f"Consider using gemini-1.5-flash or reducing retrieval K."
                )
            
            logger.info(f"Successfully generated {len(options)} agentic options with {len(source_doc_ids)} RAG sources (rag_fallback={rag_fallback_needed})")
            return options
        
        except HTTPException:
            # Re-raise HTTP exceptions (these are intended for the API)
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in agentic option generation: {e}")
            
            # Log to CloudWatch
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
            
            # Return user-friendly error - NO FALLBACK TO TEMPLATES
            raise HTTPException(
                status_code=503,
                detail={
                    'error_type': 'SIMULATOR_ERROR',
                    'error_message': str(e),
                    'user_message': 'We encountered an unexpected error while analyzing your request. Please escalate this issue to a human administrator who can assist you immediately.',
                    'escalation_required': True
                }
            )
    
    # LEGACY METHOD - KEPT FOR REFERENCE, NOT USED
    def _load_option_templates_DEPRECATED(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load resolution option templates for each category and urgency level."""
        return {
            "Maintenance": {
                "High": [
                    {
                        "action": "Dispatch Emergency Technician Immediately",
                        "base_cost": 400,
                        "base_time": 1.5,
                        "base_satisfaction": 0.95,
                        "resource_type": "emergency_tech"
                    },
                    {
                        "action": "Schedule Urgent Repair (within 4 hours)",
                        "base_cost": 250,
                        "base_time": 4.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "urgent_tech"
                    },
                    {
                        "action": "Send Maintenance Staff for Temporary Fix",
                        "base_cost": 100,
                        "base_time": 2.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "maintenance_staff"
                    }
                ],
                "Medium": [
                    {
                        "action": "Schedule Standard Repair (next business day)",
                        "base_cost": 180,
                        "base_time": 24.0,
                        "base_satisfaction": 0.75,
                        "resource_type": "standard_tech"
                    },
                    {
                        "action": "Add to Next Available Slot",
                        "base_cost": 150,
                        "base_time": 48.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "standard_tech"
                    },
                    {
                        "action": "Provide DIY Instructions and Monitor",
                        "base_cost": 10,
                        "base_time": 1.0,
                        "base_satisfaction": 0.45,
                        "resource_type": "support_staff"
                    }
                ],
                "Low": [
                    {
                        "action": "Schedule Routine Maintenance Visit",
                        "base_cost": 120,
                        "base_time": 72.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "standard_tech"
                    },
                    {
                        "action": "Send DIY Video Tutorial",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.50,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Add to Monthly Inspection List",
                        "base_cost": 20,
                        "base_time": 168.0,
                        "base_satisfaction": 0.40,
                        "resource_type": "routine"
                    }
                ]
            },
            "Security": {
                "High": [
                    {
                        "action": "Dispatch Security Team Immediately",
                        "base_cost": 300,
                        "base_time": 0.5,
                        "base_satisfaction": 0.95,
                        "resource_type": "security_team"
                    },
                    {
                        "action": "Alert On-Site Security and Monitor",
                        "base_cost": 100,
                        "base_time": 1.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "on_site_security"
                    },
                    {
                        "action": "Initiate Lockdown Protocol",
                        "base_cost": 500,
                        "base_time": 0.25,
                        "base_satisfaction": 0.90,
                        "resource_type": "emergency_protocol"
                    }
                ],
                "Medium": [
                    {
                        "action": "Schedule Security Assessment",
                        "base_cost": 150,
                        "base_time": 8.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "security_team"
                    },
                    {
                        "action": "Increase Patrol Frequency",
                        "base_cost": 80,
                        "base_time": 4.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "on_site_security"
                    },
                    {
                        "action": "Send Security Reminder Email",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.45,
                        "resource_type": "automated"
                    }
                ],
                "Low": [
                    {
                        "action": "Add to Next Security Walkthrough",
                        "base_cost": 50,
                        "base_time": 48.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "routine"
                    },
                    {
                        "action": "Send Security Best Practices Guide",
                        "base_cost": 5,
                        "base_time": 0.25,
                        "base_satisfaction": 0.50,
                        "resource_type": "automated"
                    }
                ]
            },
            "Billing": {
                "High": [
                    {
                        "action": "Immediate Manager Review and Adjustment",
                        "base_cost": 50,
                        "base_time": 2.0,
                        "base_satisfaction": 0.90,
                        "resource_type": "manager"
                    },
                    {
                        "action": "Expedited Billing Audit",
                        "base_cost": 30,
                        "base_time": 4.0,
                        "base_satisfaction": 0.80,
                        "resource_type": "billing_specialist"
                    },
                    {
                        "action": "Apply Credit and Investigate",
                        "base_cost": 20,
                        "base_time": 1.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "billing_staff"
                    }
                ],
                "Medium": [
                    {
                        "action": "Standard Billing Review",
                        "base_cost": 25,
                        "base_time": 24.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "billing_staff"
                    },
                    {
                        "action": "Automated System Check",
                        "base_cost": 5,
                        "base_time": 1.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Schedule Payment Plan Consultation",
                        "base_cost": 15,
                        "base_time": 48.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "billing_staff"
                    }
                ],
                "Low": [
                    {
                        "action": "Send Billing Explanation Email",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.55,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Add to Next Billing Cycle Review",
                        "base_cost": 10,
                        "base_time": 168.0,
                        "base_satisfaction": 0.50,
                        "resource_type": "routine"
                    }
                ]
            },
            "Deliveries": {
                "High": [
                    {
                        "action": "Immediate Package Location and Delivery",
                        "base_cost": 50,
                        "base_time": 1.0,
                        "base_satisfaction": 0.90,
                        "resource_type": "concierge"
                    },
                    {
                        "action": "Alert Concierge to Prioritize Search",
                        "base_cost": 20,
                        "base_time": 2.0,
                        "base_satisfaction": 0.75,
                        "resource_type": "concierge"
                    }
                ],
                "Medium": [
                    {
                        "action": "Check Package Room and Notify",
                        "base_cost": 15,
                        "base_time": 4.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "concierge"
                    },
                    {
                        "action": "Contact Carrier for Update",
                        "base_cost": 10,
                        "base_time": 8.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "support_staff"
                    },
                    {
                        "action": "Send Delivery Tracking Information",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.55,
                        "resource_type": "automated"
                    }
                ],
                "Low": [
                    {
                        "action": "Add to Next Concierge Rounds",
                        "base_cost": 10,
                        "base_time": 24.0,
                        "base_satisfaction": 0.50,
                        "resource_type": "routine"
                    },
                    {
                        "action": "Send Package Pickup Instructions",
                        "base_cost": 5,
                        "base_time": 0.25,
                        "base_satisfaction": 0.45,
                        "resource_type": "automated"
                    }
                ]
            },
            "Amenities": {
                "High": [
                    {
                        "action": "Immediate Staff Response and Resolution",
                        "base_cost": 80,
                        "base_time": 1.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "amenities_staff"
                    },
                    {
                        "action": "Temporary Closure and Alternative Arrangement",
                        "base_cost": 50,
                        "base_time": 2.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "amenities_staff"
                    }
                ],
                "Medium": [
                    {
                        "action": "Schedule Amenity Maintenance Check",
                        "base_cost": 40,
                        "base_time": 12.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "amenities_staff"
                    },
                    {
                        "action": "Update Amenity Schedule and Notify Residents",
                        "base_cost": 10,
                        "base_time": 1.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "support_staff"
                    }
                ],
                "Low": [
                    {
                        "action": "Send Amenity Hours and Rules Guide",
                        "base_cost": 5,
                        "base_time": 0.25,
                        "base_satisfaction": 0.60,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Add to Community Newsletter",
                        "base_cost": 5,
                        "base_time": 72.0,
                        "base_satisfaction": 0.45,
                        "resource_type": "routine"
                    },
                    {
                        "action": "Post Information on Resident Portal",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.55,
                        "resource_type": "automated"
                    }
                ]
            }
        }
    
    def simulate_resolution_process(self, template: Dict[str, Any], risk_score: float) -> Dict[str, float]:
        """
        Simulate a resolution option using SimPy.
        Adjusts parameters based on risk score.
        """
        env = simpy.Environment()
        
        results = {
            'cost': template['base_cost'],
            'time': template['base_time'],
            'satisfaction': template['base_satisfaction']
        }
        
        def resolution_process(env):
            travel_time = random.uniform(0.1, 0.5) if template['resource_type'] != 'automated' else 0
            yield env.timeout(travel_time)
            
            work_time = template['base_time'] * random.uniform(0.8, 1.2)
            yield env.timeout(work_time)
            
            results['time'] = travel_time + work_time
        
        env.process(resolution_process(env))
        env.run()
        
        # Adjust based on risk score
        if risk_score > 0.7:
            results['cost'] *= 1.2
            results['time'] *= 0.9
            results['satisfaction'] = min(results['satisfaction'] * 1.05, 1.0)
        elif risk_score < 0.4:
            results['cost'] *= 0.85
            results['time'] *= 1.1
            results['satisfaction'] *= 0.95
        
        # Add slight randomness
        results['cost'] *= random.uniform(0.95, 1.05)
        results['time'] *= random.uniform(0.9, 1.1)
        results['satisfaction'] = min(max(results['satisfaction'] * random.uniform(0.95, 1.02), 0.0), 1.0)
        
        return results


# Global instance - AGENTIC simulator
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
        # Re-raise HTTPExceptions (contain user-friendly error messages)
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in simulation endpoint: {e}")
        
        # Log to CloudWatch
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
        
        # NO FALLBACK - Return user-friendly error
        raise HTTPException(
            status_code=503,
            detail={
                'error_type': 'SIMULATION_ENDPOINT_ERROR',
                'error_message': str(e),
                'user_message': 'We are unable to process your request at this time. Please escalate this issue to a human administrator for immediate assistance.',
                'escalation_required': True
            }
        )

