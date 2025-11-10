"""
LLM Client for Agentic Option Generation
Uses Google Gemini for dynamic, context-aware decision making.
"""
import google.generativeai as genai
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set. LLM features will be disabled.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# CloudWatch client for error logging
cloudwatch_logs = boto3.client('logs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
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


def log_error_to_cloudwatch(error_type: str, error_message: str, context: Dict[str, Any]):
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
    """Client for interacting with Gemini LLM for agentic decision-making."""
    
    def __init__(self):
        # Using gemini-2.5-flash for faster, cost-effective generation
        # Flash model is optimized for speed while maintaining good quality
        self.model = genai.GenerativeModel('gemini-2.5-flash') if GEMINI_API_KEY else None
        self.enabled = GEMINI_API_KEY is not None
    
    async def generate_options(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        resident_id: str,
        resident_history: Optional[List[Dict]] = None,
        tools_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate resolution options using LLM with full context.
        
        Args:
            message_text: The resident's issue description
            category: Issue category (Maintenance, Billing, etc.)
            urgency: Urgency level (High, Medium, Low)
            risk_score: Risk prediction score (0-1)
            resident_id: Resident identifier
            resident_history: Past requests from this resident
            tools_data: Real-time data from tools (availability, weather, etc.)
        
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
            # Use simplified prompt to avoid safety blocks
            prompt = self._build_simple_prompt(
                message_text, category, urgency, risk_score
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.6,
                    max_output_tokens=2048  # Increased to avoid truncation
                )
            )
            
            # Check finish reason
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                if finish_reason == 2:  # MAX_TOKENS
                    raise ValueError("Response was truncated due to token limit")
                elif finish_reason == 3:  # SAFETY
                    raise ValueError("Response blocked by safety filters")
                elif finish_reason == 4:  # RECITATION
                    raise ValueError("Response blocked due to recitation")
            
            if not response or not response.text:
                raise ValueError("Empty response from LLM")
            
            result = json.loads(response.text)
            
            # Handle both formats: {"options": [...]} and [...]
            if isinstance(result, list):
                # LLM returned array directly
                options = result
            elif isinstance(result, dict) and 'options' in result:
                # LLM returned object with 'options' key
                options = result['options']
            else:
                raise ValueError(f"Invalid response structure: expected list or dict with 'options', got {type(result)}")
            
            if not isinstance(options, list):
                raise ValueError(f"Options must be a list, got {type(options)}")
            
            if len(options) < 3:
                raise ValueError(f"Insufficient options generated: {len(options)} (expected 3)")
            
            # Validate each option
            for idx, option in enumerate(options):
                required_fields = ['option_id', 'action', 'estimated_cost', 'time_to_resolution', 'resident_satisfaction_impact']
                for field in required_fields:
                    if field not in option:
                        raise ValueError(f"Option {idx+1} missing required field: {field}")
            
            logger.info(f"Successfully generated {len(options)} options for {resident_id}")
            # Return in consistent format
            return {'options': options}
        
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
            logger.error(error_msg)
            log_error_to_cloudwatch(
                error_type="JSON_PARSE_ERROR",
                error_message=error_msg,
                context={
                    'resident_id': resident_id,
                    'category': category,
                    'urgency': urgency,
                    'response_text': response.text if response else None
                }
            )
            return {
                'error': {
                    'type': 'JSON_PARSE_ERROR',
                    'message': error_msg,
                    'user_message': 'We encountered an error processing your request. Please escalate this issue to a human administrator for immediate assistance.'
                }
            }
        
        except ValueError as e:
            error_msg = f"LLM response validation failed: {str(e)}"
            logger.error(error_msg)
            log_error_to_cloudwatch(
                error_type="VALIDATION_ERROR",
                error_message=error_msg,
                context={
                    'resident_id': resident_id,
                    'category': category,
                    'urgency': urgency
                }
            )
            return {
                'error': {
                    'type': 'VALIDATION_ERROR',
                    'message': error_msg,
                    'user_message': 'We were unable to generate valid resolution options for your issue. Please escalate this to a human administrator who can assist you immediately.'
                }
            }
        
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
    
    def _build_simple_prompt(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float
    ) -> str:
        """Build minimal prompt to avoid safety blocks while still being effective."""
        return f"""Generate 3 resolution options for: "{message_text}"
Category: {category}, Urgency: {urgency}

Return JSON with 3 options (fast/standard/budget):
- option_id: "opt_1", "opt_2", "opt_3"
- action: brief description (max 2 sentences)
- estimated_cost: number
- time_to_resolution: hours (number)
- resident_satisfaction_impact: 0-1 (number)
- reasoning: brief reason (max 1 sentence)

Keep action and reasoning SHORT."""
    
    def _build_agentic_prompt(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        resident_id: str,
        resident_history: Optional[List[Dict]],
        tools_data: Optional[Dict[str, Any]]
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
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
        
        except Exception as e:
            logger.error(f"Feedback analysis failed: {e}")
            return {'analysis': 'Failed', 'error': str(e)}


# Global instance
llm_client = LLMClient()

