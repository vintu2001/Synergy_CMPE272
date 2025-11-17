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
        # Using gemini-2.5-flash for faster generation
        # Note: If this model is not available, it will fall back to available models
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
        tools_data: Optional[Dict[str, Any]] = None,
        rag_context: Optional[Any] = None  # RAG integration
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
            # Use simplified prompt to avoid safety blocks
            prompt = self._build_agentic_prompt(
                message_text, category, urgency, risk_score, resident_id, 
                resident_history, tools_data, rag_context
            )
            
            # Use strict JSON mode and lower temperature for more reliable JSON
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Very low temperature for consistent JSON formatting
                    max_output_tokens=4096,
                    top_p=0.95,  # Reduce randomness
                    top_k=40,  # Further constrain token selection
                    response_mime_type="application/json"  # Request JSON response format
                )
            )
            
            # Check finish reason
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                logger.info(f"LLM finish reason: {finish_reason}")
                if finish_reason == 3:  # SAFETY
                    raise ValueError("Response blocked by safety filters")
                elif finish_reason == 4:  # RECITATION
                    raise ValueError("Response blocked due to recitation")
                # Note: finish_reason == 2 (MAX_TOKENS) is handled below - we'll try to parse anyway
            
            if not response or not response.text:
                logger.error(f"Empty response from LLM. Response: {response}")
                raise ValueError("Empty response from LLM")
            
            logger.info(f"Raw LLM response text (first 500 chars): {response.text[:500]}")
            
            # Try to extract JSON from response if it's wrapped in markdown code blocks
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()
            
            # Try to parse JSON, with automatic repair on failure
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Initial JSON parse failed: {json_err}. Attempting repair...")
                # Try to repair common JSON issues
                repaired_text = self._repair_json(response_text)
                try:
                    result = json.loads(repaired_text)
                    logger.info("✅ JSON successfully repaired and parsed")
                except json.JSONDecodeError as repair_err:
                    logger.error(f"JSON repair failed: {repair_err}")
                    logger.error(f"Original text: {response_text[:500]}...")
                    logger.error(f"Repaired text: {repaired_text[:500]}...")
                    raise repair_err  # Re-raise to trigger error handling below
            
            # Handle both formats: {"options": [...]} and [...]
            if isinstance(result, list):
                # LLM returned array directly
                options = result
                is_recurring = False
            elif isinstance(result, dict) and 'options' in result:
                # LLM returned object with 'options' key
                options = result['options']
                is_recurring = result.get('is_recurring', False)
            else:
                raise ValueError(f"Invalid response structure: expected list or dict with 'options', got {type(result)}")
            
            if not isinstance(options, list):
                raise ValueError(f"Options must be a list, got {type(options)}")
            
            if len(options) < 2:
                raise ValueError(f"Insufficient options generated: {len(options)} (expected at least 2)")
            
            # Validate each option
            for idx, option in enumerate(options):
                required_fields = ['option_id', 'action', 'estimated_cost', 'resident_satisfaction_impact']
                # Check for either new field names or old field names for backward compatibility
                if 'estimated_time' not in option and 'time_to_resolution' not in option:
                    raise ValueError(f"Option {idx+1} missing time field (estimated_time or time_to_resolution)")
                
                for field in required_fields:
                    if field not in option:
                        logger.error(f"Option {idx+1} missing required field: {field}. Full option: {option}")
                        raise ValueError(f"Option {idx+1} missing required field: {field}")
            
            logger.info(f"Successfully generated {len(options)} options for {resident_id} (is_recurring={is_recurring})")
            # Return in consistent format with is_recurring flag
            return {'options': options, 'is_recurring': is_recurring}
        
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
        risk_score: float,
        rag_context: Optional[Any] = None
    ) -> str:
        """Build minimal prompt to avoid safety blocks while still being effective."""
        
        # Build RAG context section if available
        rag_section = ""
        if rag_context and hasattr(rag_context, 'retrieved_docs') and rag_context.retrieved_docs:
            rag_section = "\nKB Docs:\n"
            for i, doc in enumerate(rag_context.retrieved_docs[:3], 1):
                doc_id = doc.get('doc_id', 'N/A')
                text_preview = doc.get('text', '')[:150]
                rag_section += f"{i}. [{doc_id}] {text_preview}...\n"
        
        prompt = f"""Generate 3 resolution options for apartment maintenance.

REQUEST: "{message_text}"
CATEGORY: {category} | URGENCY: {urgency}
{rag_section}

REQUIRED FIELDS (all mandatory):
- option_id: "opt_1", "opt_2", "opt_3"
- action: brief description (under 150 chars)
- estimated_cost: number (dollars)
- time_to_resolution: number (hours)
- resident_satisfaction_impact: 0.0-1.0 (faster=higher)
- reasoning: brief explanation (under 100 chars)
- steps: array of 3-5 action steps

JSON FORMAT RULES:
- Return ONLY valid JSON array with no markdown
- No newlines in strings
- Keep strings brief
- Escape special characters

Example:
[
  {{"option_id":"opt_1","action":"Fast repair","estimated_cost":300,"time_to_resolution":2,"resident_satisfaction_impact":0.85,"reasoning":"Quick fix","steps":["Step 1","Step 2","Step 3"]}},
  {{"option_id":"opt_2","action":"Standard repair","estimated_cost":150,"time_to_resolution":24,"resident_satisfaction_impact":0.75,"reasoning":"Balanced","steps":["Step 1","Step 2","Step 3"]}},
  {{"option_id":"opt_3","action":"Budget repair","estimated_cost":50,"time_to_resolution":48,"resident_satisfaction_impact":0.65,"reasoning":"Economical","steps":["Step 1","Step 2","Step 3"]}}
]

Generate valid JSON array now."""
        
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
            history_context = f"This resident has submitted {len(resident_history)} request(s) in the past month:\n"
            for i, req in enumerate(resident_history[-5:], 1):  # Show last 5
                history_context += f"{i}. [{req.get('category', 'Unknown')}] \"{req.get('message_text', '')[:60]}...\" "
                history_context += f"(Status: {req.get('status', 'Unknown')}, Created: {req.get('created_at', 'N/A')[:10]})\n"
            history_context += "\nIMPORTANT: Consider if this is a recurring issue that needs a permanent solution."
        
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
        
        prompt = f"""You are an AI apartment management agent. Generate 3 resolution options for this issue.

ISSUE: {message_text}
CATEGORY: {category} | URGENCY: {urgency} | RISK: {risk_score:.2f}/1.0
RESIDENT: {resident_id}

HISTORY:
{history_context if history_context else "No previous issues."}
{tools_context}
{rag_section}

TASK:
1. Check if recurring: Set is_recurring=true if resident has 2+ similar past issues OR message contains "again/still/keep happening"
2. Generate 3 options: Premium (fast/costly), Balanced (moderate), Budget (slow/cheap)
3. If is_recurring=true, include 1+ permanent solution option (is_permanent_solution=true)

REQUIREMENTS:
- Be specific to "{message_text}" not generic
- Costs realistic for apartment maintenance
- Times in hours (decimals OK)
- Satisfaction 0.0-1.0
- Keep all text brief and on single lines

JSON FORMAT (CRITICAL):
- Return ONLY valid JSON with no markdown or code blocks
- Keep action and reasoning under 150 characters each
- No newlines in strings - use spaces
- No unescaped quotes or special chars
- Ensure all brackets/braces closed

{{
  "reasoning": "Brief analysis on one line",
  "is_recurring": false,
  "options": [
    {{
      "option_id": "opt_1",
      "action": "Specific action 1-2 sentences",
      "estimated_cost": 250.00,
      "time_to_resolution": 4.0,
      "resident_satisfaction_impact": 0.85,
      "reasoning": "Why this option works",
      "is_permanent_solution": false,
      "requires_resident_action": false
    }},
    {{
      "option_id": "opt_2",
      "action": "Different approach 1-2 sentences",
      "estimated_cost": 150.00,
      "time_to_resolution": 8.0,
      "resident_satisfaction_impact": 0.75,
      "reasoning": "Why this option works",
      "is_permanent_solution": false,
      "requires_resident_action": false
    }},
    {{
      "option_id": "opt_3",
      "action": "Budget option 1-2 sentences",
      "estimated_cost": 80.00,
      "time_to_resolution": 12.0,
      "resident_satisfaction_impact": 0.65,
      "reasoning": "Why this option works",
      "is_permanent_solution": false,
      "requires_resident_action": true
    }}
  ],
  "escalation_recommended": false,
  "escalation_reason": null
}}

Set escalation_recommended=true only for: life-threatening, beyond maintenance skills, legal issues, or resident conflicts.

Generate concise, valid JSON now."""

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
                    temperature=0.6
                )
            )
            
            return json.loads(response.text)
        
        except Exception as e:
            logger.error(f"Feedback analysis failed: {e}")
            return {'analysis': 'Failed', 'error': str(e)}
    
    async def answer_question(
        self,
        question: str,
        rag_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a resident's question using RAG context.
        
        Args:
            question: The question to answer
            rag_context: Retrieved context from RAG system
        
        Returns:
            Dict with answer and confidence
        """
        if not self.enabled:
            return {
                'answer': 'I am currently unavailable. Please contact the property management office.',
                'confidence': 0.0,
                'error': 'LLM_DISABLED'
            }
        
        try:
            prompt = f"""You are a helpful apartment management assistant. Answer the resident's question based ONLY on the provided knowledge base context.

QUESTION:
{question}

KNOWLEDGE BASE CONTEXT:
{rag_context if rag_context else "No context available"}

CRITICAL INSTRUCTIONS:
1. Answer the question directly and concisely in plain, natural language
2. Use ONLY information from the context provided above
3. Write in complete sentences without any markdown formatting, asterisks, or special symbols
4. Do NOT use **, ##, *, or any other formatting symbols - use plain text only
5. Be friendly and conversational
6. If the context doesn't contain the answer, say "I don't have that information in my knowledge base"
7. Present policies and rules in a clear, easy-to-read way using simple paragraphs
8. Use proper punctuation and spacing

FORMATTING EXAMPLES:
BAD: "**Dogs:** Up to 2 per unit * Weight: 50 lbs max"
GOOD: "You can have up to 2 dogs per unit, with a maximum weight of 50 pounds each."

BAD: "## Pet Policy - ** No restrictions **"
GOOD: "According to our pet policy, there are no breed restrictions."

Return your response as a JSON object with these fields:
{{
  "answer": "your clean, well-formatted answer here in plain text",
  "confidence": a number between 0.0 and 1.0 indicating how confident you are
}}

Return ONLY the JSON object, no markdown formatting."""

            logger.info("Generating answer with Gemini (llm_client)")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3  # Lower temperature for factual answers
                )
            )
            
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            import re
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'^```\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            
            result = json.loads(result_text)
            
            return {
                'answer': result.get('answer', 'I couldn\'t generate a proper answer.'),
                'confidence': float(result.get('confidence', 0.5))
            }
        
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'answer': 'I encountered an error while trying to answer your question. Please try rephrasing or contact support.',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _repair_json(self, text: str) -> str:
        """
        Attempt to repair common JSON formatting errors from LLM responses.
        
        Common issues:
        - Unterminated strings
        - Missing closing quotes
        - Missing closing brackets/braces
        - Trailing commas
        - Unescaped quotes in strings
        
        Args:
            text: Potentially malformed JSON string
        
        Returns:
            Repaired JSON string
        """
        import re
        
        logger.info("🔧 Attempting JSON repair...")
        
        # Remove any text before first { or [
        match = re.search(r'[\{\[]', text)
        if match:
            text = text[match.start():]
            logger.debug(f"Stripped leading text, now starts with: {text[:50]}")
        
        # Remove any text after last } or ]
        last_brace = max(text.rfind('}'), text.rfind(']'))
        if last_brace > 0:
            text = text[:last_brace + 1]
            logger.debug(f"Stripped trailing text, now ends with: {text[-50:]}")
        
        # Fix unterminated strings by adding closing quote at end of line
        lines = text.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            # Count quotes (excluding escaped quotes)
            quote_count = len(re.findall(r'(?<!\\)"', line))
            # If odd number of quotes, likely unterminated string
            if quote_count % 2 != 0 and not line.strip().endswith('"'):
                # Add closing quote before any trailing comma or brace
                line = re.sub(r'([^"\\])(\s*[,\}\]]?\s*)$', r'\1"\2', line)
                logger.debug(f"Fixed unterminated string on line {i+1}")
            fixed_lines.append(line)
        text = '\n'.join(fixed_lines)
        
        # Fix trailing commas before closing brackets
        original_text = text
        text = re.sub(r',(\s*[\}\]])', r'\1', text)
        if text != original_text:
            logger.debug("Removed trailing commas")
        
        # Ensure proper closing brackets
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # Add missing closing characters
        if open_braces > 0:
            text += '}' * open_braces
            logger.debug(f"Added {open_braces} closing braces")
        if open_brackets > 0:
            text += ']' * open_brackets
            logger.debug(f"Added {open_brackets} closing brackets")
        
        logger.info(f"✅ JSON repair complete. Length: {len(text)} chars")
        
        return text


# Global instance
llm_client = LLMClient()


