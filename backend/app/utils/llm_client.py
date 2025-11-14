"""
LLM Client for Agentic Option Generation
Uses LangChain with Google Gemini for dynamic, context-aware decision making.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.utils.langchain_llm_factory import (
    create_gemini_llm,
    create_gemini_llm_for_json,
    create_gemini_llm_with_schema
)
from app.utils.langchain_errors import (
    LLMTimeoutError,
    LLMSafetyError,
    LLMAPIError,
    LLMConfigurationError,
    create_error_response
)
from app.utils.parse_utils import parse_with_reprompt
from app.models.structured_schemas import SimulationOutputSchema

logger = logging.getLogger(__name__)

# Configure settings
settings = get_settings()

# CloudWatch client for error logging
cloudwatch_logs = boto3.client('logs', region_name=settings.AWS_REGION)
LOG_GROUP_NAME = '/aam/llm-errors'
LOG_STREAM_NAME = f'llm-errors-{datetime.now(timezone.utc).strftime("%Y-%m-%d")}'

# Ensure log group and stream exist
def ensure_cloudwatch_log_stream():
    """Create CloudWatch log group and stream if they don't exist."""
    try:
        try:
            cloudwatch_logs.create_log_group(logGroupName=LOG_GROUP_NAME)
        except cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
            pass
        
        try:
            cloudwatch_logs.create_log_stream(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=LOG_STREAM_NAME
            )
        except cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
            pass
    except Exception as e:
        logger.warning(f"Could not create CloudWatch log stream: {e}")


async def log_error_to_cloudwatch(error_type: str, error_message: str, context: Dict[str, Any]):
    """Log LLM errors to CloudWatch for monitoring."""
    try:
        ensure_cloudwatch_log_stream()
        
        log_event = {
            'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
            'message': json.dumps({
                'error_type': error_type,
                'error_message': error_message,
                'context': context,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
        cloudwatch_logs.put_log_events(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=LOG_STREAM_NAME,
            logEvents=[log_event]
        )
        logger.info(f"Error logged to CloudWatch: {error_type}")
    except Exception as e:
        logger.error(f"Failed to log to CloudWatch: {e}")


class LLMClient:
    """Client for interacting with Gemini LLM via LangChain for agentic decision-making."""
    
    def __init__(self):
        """Initialize LLM client with LangChain."""
        try:
            # Create LangChain LLM instance using factory
            self.llm = create_gemini_llm_for_json()
            self.enabled = True
            logger.info(f"LLMClient initialized with model: {settings.GEMINI_MODEL}")
        except ValueError as e:
            logger.warning(f"Failed to initialize LLM: {e}. LLM features will be disabled.")
            self.llm = None
            self.enabled = False
    
    async def generate_options(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        resident_id: str,
        resident_history: Optional[List[Dict]] = None,
        tools_data: Optional[Dict[str, Any]] = None,
        rag_context: Optional[Any] = None  # RAG integration
    ) -> Dict[str, Any]:
        """
        Generate resolution options using LLM with structured output.
        
        Uses LangChain's with_structured_output() for type-safe responses.
        Includes automatic reprompt on parse failures.
        
        Args:
            message_text: The resident's issue description
            category: Issue category (Maintenance, Billing, etc.)
            urgency: Urgency level (High, Medium, Low)
            risk_score: Risk prediction score (0-1)
            resident_id: Resident identifier
            resident_history: Past requests from this resident
            tools_data: Real-time data from tools (availability, weather, etc.)
            rag_context: Retrieved documents from knowledge base (RAG)
        
        Returns:
            Dict with 'options' list or 'error' dict
        """
        if not self.enabled:
            error_msg = "LLM service is not configured (missing GEMINI_API_KEY)"
            log_error_to_cloudwatch(
                error_type="LLM_NOT_CONFIGURED",
                error_message=error_msg,
                context={'resident_id': resident_id, 'category': category}
            )
            return {
                'error': {
                    'type': 'LLM_NOT_CONFIGURED',
                    'message': error_msg,
                    'user_message': 'We are unable to generate resolution options at this time. Please escalate this issue to a human administrator for immediate assistance.'
                }
            }
        
        try:
            # Create LLM with structured output for SimulationOutputSchema
            structured_llm = create_gemini_llm_with_schema(
                schema=SimulationOutputSchema,
                temperature=0.0,  # Deterministic for JSON
                model="gemini-2.5-flash"  # Use flash for faster responses
            )
            
            # Build prompt using template system
            prompt = self._build_simulation_prompt_template(
                message_text, category, urgency, risk_score, rag_context
            )
            
            # Parse with automatic reprompt on failure
            result = await parse_with_reprompt(
                llm=structured_llm,
                initial_prompt=prompt,
                schema=SimulationOutputSchema,
                context={
                    'resident_id': resident_id,
                    'category': category,
                    'urgency': urgency,
                    'risk_score': risk_score
                },
                log_error_fn=log_error_to_cloudwatch,
                max_attempts=2
            )
            
            # Check if parsing succeeded
            if result['success']:
                options = result['data']['options']
                reprompt_count = result['reprompt_count']
                
                logger.info(
                    f"Successfully generated {len(options)} options for {resident_id} "
                    f"(reprompt_count={reprompt_count})"
                )
                
                return {'options': options}
            else:
                # Parsing failed after all attempts
                error_dict = result['error']
                logger.error(
                    f"Failed to generate options for {resident_id} after "
                    f"{result['reprompt_count']} reprompt(s): {error_dict['message']}"
                )
                return {'error': error_dict}
                
        except LLMTimeoutError as e:
            logger.error(f"LLM timeout for {resident_id}: {str(e)}")
            return e.to_dict()
            
        except LLMSafetyError as e:
            logger.error(f"LLM safety block for {resident_id}: {str(e)}")
            return e.to_dict()
            
        except LLMAPIError as e:
            logger.error(f"LLM API error for {resident_id}: {str(e)}")
            return e.to_dict()
            
        except Exception as e:
            error_msg = f"Unexpected error during LLM generation: {str(e)}"
            logger.error(error_msg)
            log_error_to_cloudwatch(
                error_type="UNEXPECTED_ERROR",
                error_message=error_msg,
                context={
                    'resident_id': resident_id,
                    'category': category,
                    'urgency': urgency,
                    'error_class': e.__class__.__name__
                }
            )
            return {
                'error': {
                    'type': 'UNEXPECTED_ERROR',
                    'message': error_msg,
                    'user_message': 'An unexpected error occurred while processing your request. Please escalate this issue to a human administrator for immediate assistance.'
                }
            }
    
    async def extract_rules(
        self,
        category: str,
        urgency: str,
        rag_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Extract decision-making rules from policy documents using structured output.
        
        Uses RulesPrompt template and with_structured_output(RulesOutputSchema)
        to parse policy rules into weights, caps, and escalation criteria.
        
        Args:
            category: Issue category (Maintenance, Billing, etc.)
            urgency: Urgency level (High, Medium, Low)
            rag_context: Retrieved policy documents from knowledge base
            
        Returns:
            Dict with 'rules' dict containing weights/caps/escalation or 'error' dict
            
        Example:
            >>> result = await client.extract_rules(
            ...     category="Maintenance",
            ...     urgency="High",
            ...     rag_context=rag_docs
            ... )
            >>> if 'rules' in result:
            ...     weights = result['rules']['weights']
            ...     caps = result['rules']['caps']
        """
        if not self.enabled:
            return {
                'error': {
                    'type': 'LLM_NOT_CONFIGURED',
                    'message': 'LLM service is not configured',
                    'user_message': 'Unable to extract policy rules at this time'
                }
            }
        
        try:
            from app.models.structured_schemas import RulesOutputSchema
            from app.prompts.rules_prompt import RulesPrompt
            
            # Create LLM with structured output for RulesOutputSchema
            structured_llm = create_gemini_llm_with_schema(
                schema=RulesOutputSchema,
                temperature=0.0,  # Deterministic for rule extraction
                model="gemini-2.5-flash"
            )
            
            # Extract documents from RAG context
            retrieved_docs = []
            if rag_context and hasattr(rag_context, 'retrieved_docs'):
                retrieved_docs = rag_context.retrieved_docs
            
            # Build prompt using RulesPrompt template
            rules_prompt = RulesPrompt(
                category=category,
                urgency=urgency,
                retrieved_docs=retrieved_docs
            )
            prompt_text = rules_prompt.format()
            
            # Parse with automatic reprompt on failure
            result = await parse_with_reprompt(
                llm=structured_llm,
                initial_prompt=prompt_text,
                schema=RulesOutputSchema,
                context={
                    'category': category,
                    'urgency': urgency,
                    'doc_count': len(retrieved_docs)
                },
                log_error_fn=log_error_to_cloudwatch,
                max_attempts=2
            )
            
            # Check if parsing succeeded
            if result['success']:
                rules_data = result['data']
                reprompt_count = result['reprompt_count']
                
                logger.info(
                    f"Successfully extracted rules for {category}/{urgency} "
                    f"(reprompt_count={reprompt_count}, sources={len(rules_data.get('sources', []))})"
                )
                
                return {'rules': rules_data}
            else:
                # Parsing failed after all attempts
                error_dict = result['error']
                logger.error(
                    f"Failed to extract rules for {category}/{urgency} after "
                    f"{result['reprompt_count']} reprompt(s): {error_dict['message']}"
                )
                return {'error': error_dict}
                
        except Exception as e:
            error_msg = f"Unexpected error during rules extraction: {str(e)}"
            logger.error(error_msg)
            log_error_to_cloudwatch(
                error_type="RULES_EXTRACTION_ERROR",
                error_message=error_msg,
                context={
                    'category': category,
                    'urgency': urgency,
                    'error_class': e.__class__.__name__
                }
            )
            return {
                'error': {
                    'type': 'RULES_EXTRACTION_ERROR',
                    'message': error_msg,
                    'user_message': 'Unable to extract policy rules from documents'
                }
            }
    
    def _build_simulation_prompt_template(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        rag_context: Optional[Any] = None
    ) -> str:
        """
        Build simulation prompt using new template system.
        
        Uses SimulationPrompt template with citation-first design.
        Falls back to simple prompt if template fails.
        """
        try:
            from app.prompts import SimulationPrompt
            
            # Extract documents from RAG context
            retrieved_docs = []
            if rag_context and hasattr(rag_context, 'retrieved_docs'):
                retrieved_docs = rag_context.retrieved_docs
            
            # Create template
            template = SimulationPrompt(
                issue_text=message_text,
                category=category,
                urgency=urgency,
                retrieved_docs=retrieved_docs,
                risk_score=risk_score
            )
            
            # Render prompt
            prompt = template.render()
            logger.info(f"Using SimulationPrompt template ({template.get_metadata()})")
            return prompt
            
        except Exception as e:
            logger.warning(f"Failed to use SimulationPrompt template: {e}. Falling back to simple prompt.")
            # Fall back to simple prompt
            return self._build_simple_prompt(
                message_text, category, urgency, risk_score, rag_context
            )
    
    def _build_simple_prompt(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        rag_context: Optional[Any] = None
    ) -> str:
        """Build minimal prompt to avoid safety blocks while still being effective."""
        
        # Build RAG context section if available
        rag_section = ""
        if rag_context and hasattr(rag_context, 'retrieved_docs') and rag_context.retrieved_docs:
            rag_section = "\n\nRelevant KB Documents:\n"
            for i, doc in enumerate(rag_context.retrieved_docs[:3], 1):  # Top 3 docs
                doc_id = doc.get('doc_id', 'N/A')
                text_preview = doc.get('text', '')[:200]  # First 200 chars
                rag_section += f"{i}. [{doc_id}] {text_preview}...\n"
            rag_section += "\nUse these KB documents to inform your options. Cite doc IDs when relevant.\n"
        
        prompt = f"""Generate exactly 3 different resolution options for: "{message_text}"
Category: {category}, Urgency: {urgency}
{rag_section}
IMPORTANT: You must provide exactly 3 options - no more, no less.

Return JSON with this exact structure:
{{
  "options": [
    {{
      "option_id": "opt_1",
      "action": "First resolution approach",
      "estimated_cost": 100,
      "estimated_time": 2,
      "reasoning": "Why this option is good",
      "sources": []
    }},
    {{
      "option_id": "opt_2",
      "action": "Second resolution approach",
      "estimated_cost": 200,
      "estimated_time": 4,
      "reasoning": "Why this option is better",
      "sources": []
    }},
    {{
      "option_id": "opt_3",
      "action": "Third resolution approach",
      "estimated_cost": 300,
      "estimated_time": 8,
      "reasoning": "Why this option is best",
      "sources": []
    }}
  ]
}}

Keep action and reasoning brief but provide exactly 3 different options."""
        
        return prompt
    
    def _build_agentic_prompt(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        resident_id: str,
        resident_history: Optional[List[Dict]],
        tools_data: Optional[Dict[str, Any]],
        rag_context: Optional[Any] = None
    ) -> str:
        """Build comprehensive agentic prompt with all context."""
        
        # Build history context
        history_context = ""
        if resident_history and len(resident_history) > 0:
            recent_issues = []
            for req in resident_history[-5:]:
                recent_issues.append(
                    f"  - {req.get('category', 'Unknown')}: \"{req.get('message_text', '')[:50]}...\" "
                    f"(Status: {req.get('status', 'Unknown')})"
                )
            history_context = "\n".join(recent_issues)
        
        # Build tools context
        tools_context = ""
        if tools_data:
            tools_context = "\n\nReal-Time Data Available:"
            if 'availability' in tools_data:
                tools_context += f"\n- Technician Availability: {tools_data['availability']}"
            if 'weather' in tools_data:
                tools_context += f"\n- Weather Conditions: {tools_data['weather']}"
            if 'pricing' in tools_data:
                tools_context += f"\n- Dynamic Pricing: {tools_data['pricing']}"
            if 'inventory' in tools_data:
                tools_context += f"\n- Parts Inventory: {tools_data['inventory']}"
            if 'past_solutions' in tools_data:
                tools_context += f"\n- Similar Past Solutions: {tools_data['past_solutions']}"
        
        # Build RAG context from knowledge base
        rag_section = ""
        if rag_context and hasattr(rag_context, 'retrieved_docs') and rag_context.retrieved_docs:
            rag_section = "\n\n=== KNOWLEDGE BASE DOCUMENTS ===\n"
            rag_section += "The following documents were retrieved from our knowledge base based on this issue:\n\n"
            for i, doc in enumerate(rag_context.retrieved_docs, 1):
                doc_id = doc.get('doc_id', 'Unknown')
                doc_type = doc.get('type', 'document')
                text = doc.get('text', '')
                score = doc.get('score', 0)
                rag_section += f"{i}. [{doc_id}] (relevance: {score:.2f}, type: {doc_type})\n"
                rag_section += f"   {text[:300]}...\n\n"
            rag_section += "IMPORTANT: Use these KB documents to inform your decisions. Reference doc IDs in your reasoning when applicable.\n"
        
        prompt = f"""You are an expert AI apartment management agent with advanced reasoning capabilities.

MISSION: Generate 3 distinct, context-specific resolution options for this resident's issue.

=== CURRENT ISSUE ===
Resident ID: {resident_id}
Issue Description: {message_text}
Category: {category}
Urgency Level: {urgency}
Risk Score: {risk_score:.2f}/1.0 (0=low risk, 1=high risk)

=== RESIDENT HISTORY ===
{history_context if history_context else "No previous issues on record."}
{tools_context}
{rag_section}

=== YOUR TASK ===
As an intelligent agent, you must:

1. ANALYZE the issue deeply:
   - What is the root cause?
   - What are the immediate vs long-term needs?
   - Consider urgency, risk, and resident history
   - Think about cost-effectiveness vs resident satisfaction

2. REASON about the best approaches:
   - What are the tradeoffs (cost/time/quality)?
   - Should we prioritize speed or cost?
   - Is this a recurring issue that needs a permanent solution?
   - Can the resident handle any part of this themselves?

3. GENERATE 3 distinct options with clear differentiation:
   - Option 1: Premium/Fast (higher cost, faster resolution, higher satisfaction)
   - Option 2: Balanced (moderate cost, reasonable time, good satisfaction)
   - Option 3: Budget/DIY (lower cost, longer time OR self-service element)

4. BE SPECIFIC AND ACTIONABLE:
   - Don't use generic templates
   - Tailor actions to the exact issue described
   - Provide realistic cost and time estimates
   - Explain WHY each option makes sense

=== CRITICAL REQUIREMENTS ===
- Make options SPECIFIC to "{message_text}" (not generic)
- Consider the {urgency} urgency and {risk_score:.2f} risk score
- If history shows recurring issues, suggest permanent solutions
- All costs must be realistic for apartment maintenance
- All times must be in hours (decimals allowed)
- Satisfaction scores must be 0.0-1.0

=== OUTPUT FORMAT (JSON) ===
{{
  "reasoning": "Your step-by-step analysis of the issue and why you chose these options",
  "options": [
    {{
      "option_id": "opt_1",
      "action": "Detailed, specific action description (3-5 sentences)",
      "estimated_cost": 250.00,
      "time_to_resolution": 4.0,
      "resident_satisfaction_impact": 0.85,
      "reasoning": "Why this option is good for this specific situation",
      "is_permanent_solution": false,
      "requires_resident_action": false
    }},
    {{
      "option_id": "opt_2",
      "action": "Different approach with different tradeoffs",
      "estimated_cost": 150.00,
      "time_to_resolution": 8.0,
      "resident_satisfaction_impact": 0.75,
      "reasoning": "Why this balanced option makes sense",
      "is_permanent_solution": false,
      "requires_resident_action": false
    }},
    {{
      "option_id": "opt_3",
      "action": "Budget-friendly or DIY-assisted option",
      "estimated_cost": 80.00,
      "time_to_resolution": 12.0,
      "resident_satisfaction_impact": 0.65,
      "reasoning": "Why this economical option is viable",
      "is_permanent_solution": false,
      "requires_resident_action": true
    }}
  ],
  "escalation_recommended": false,
  "escalation_reason": null
}}

=== ESCALATION LOGIC ===
Set "escalation_recommended": true if:
- Issue is life-threatening or emergency safety concern
- Problem requires skills beyond standard maintenance
- Legal or regulatory compliance issue
- Conflict between residents

Think carefully and be creative. Generate options now."""

        return prompt
    
    async def analyze_feedback(
        self,
        request_id: str,
        chosen_option: Dict,
        outcome: Dict,
        resident_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze feedback from completed requests for learning (Level 4).
        
        Args:
            request_id: The completed request ID
            chosen_option: The option that was selected
            outcome: Actual cost, time, satisfaction from resolution
            resident_feedback: Optional text feedback from resident
        
        Returns:
            Analysis with improvement suggestions
        """
        if not self.enabled:
            return {'analysis': 'LLM not configured', 'improvements': []}
        
        try:
            prompt = f"""You are analyzing the outcome of a maintenance request to learn and improve.

REQUEST: {request_id}

OPTION CHOSEN:
- Action: {chosen_option.get('action')}
- Estimated Cost: ${chosen_option.get('estimated_cost')}
- Estimated Time: {chosen_option.get('time_to_resolution')}h
- Expected Satisfaction: {chosen_option.get('resident_satisfaction_impact')}

ACTUAL OUTCOME:
- Actual Cost: ${outcome.get('actual_cost', 'N/A')}
- Actual Time: {outcome.get('actual_time', 'N/A')}h
- Actual Satisfaction: {outcome.get('actual_satisfaction', 'N/A')}
- Resident Feedback: "{resident_feedback or 'None provided'}"

ANALYZE:
1. Was the estimate accurate?
2. What went better or worse than expected?
3. What can we learn for future similar issues?
4. Should we adjust cost/time estimates for this type of issue?

Output JSON:
{{
  "accuracy_score": 0.85,
  "lessons_learned": ["lesson 1", "lesson 2"],
  "cost_adjustment": 0.0,
  "time_adjustment": 0.0,
  "strategy_improvements": ["improvement 1"]
}}"""
            
            # Use LangChain to invoke LLM
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return json.loads(response_text)
        
        except Exception as e:
            logger.error(f"Feedback analysis failed: {e}")
            return {'analysis': 'Failed', 'error': str(e)}


# Global instance
llm_client = LLMClient()

