"""
Parse utilities with reprompt logic for LLM structured output.

Handles parsing failures with automatic reprompting and comprehensive logging.
"""
import logging
from typing import Type, Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, ValidationError
import json

logger = logging.getLogger(__name__)


async def parse_with_reprompt(
    llm: Any,
    initial_prompt: str,
    schema: Type[BaseModel],
    context: Dict[str, Any],
    log_error_fn: Callable[[str, str, Dict[str, Any]], Awaitable[None]],
    max_attempts: int = 2
) -> Dict[str, Any]:
    """
    Parse LLM response with automatic reprompt on failure.
    
    This utility:
    1. Invokes LLM with initial prompt
    2. On parse/validation failure, logs REPROMPT_ATTEMPTED
    3. Retries with simplified "JSON only" prompt
    4. Returns clean error dict if all attempts fail
    
    Args:
        llm: LLM instance (with or without structured output)
        initial_prompt: Initial prompt to send to LLM
        schema: Pydantic schema for validation (can be None if llm has structured output)
        context: Context dict for error logging (resident_id, category, etc.)
        log_error_fn: Async function to log errors to CloudWatch
        max_attempts: Maximum number of attempts (default: 2)
        
    Returns:
        Dict with either:
        - {'success': True, 'data': parsed_model_dict, 'reprompt_count': 0|1}
        - {'success': False, 'error': {...}, 'reprompt_count': attempts}
        
    Example:
        >>> llm = create_gemini_llm_with_schema(SimulationOutputSchema)
        >>> result = await parse_with_reprompt(
        ...     llm=llm,
        ...     initial_prompt="Generate options",
        ...     schema=SimulationOutputSchema,
        ...     context={'resident_id': 'test'},
        ...     log_error_fn=log_error_to_cloudwatch
        ... )
        >>> if result['success']:
        ...     options = result['data']['options']
    """
    reprompt_count = 0
    last_error = None
    
    for attempt in range(max_attempts):
        # Determine which prompt to use
        if attempt == 0:
            prompt = initial_prompt
        else:
            # Reprompt with simplified instruction
            reprompt_count = attempt
            logger.warning(
                f"LLM_REPROMPT_ATTEMPTED (attempt {attempt + 1}/{max_attempts}): "
                f"Previous attempt failed, retrying with simplified prompt. "
                f"Context: {context}"
            )
            
            # Log reprompt event to CloudWatch
            await log_error_fn(
                error_type="LLM_REPROMPT_ATTEMPTED",
                error_message=f"Parse failure on attempt {attempt}, retrying with simplified prompt",
                context={
                    **context,
                    'attempt': attempt + 1,
                    'max_attempts': max_attempts,
                    'previous_error': str(last_error) if last_error else None
                }
            )
            
            prompt = f"""{initial_prompt}

CRITICAL: Your previous response could not be parsed.
Return ONLY valid JSON matching the required schema.
Do NOT include markdown code blocks (```json).
Do NOT include any explanations before or after the JSON.
Return raw JSON only."""
            
        try:
            # Invoke LLM
            response = await llm.ainvoke(prompt)
            print(f"[DEBUG] LLM response received, type: {type(response)}")
            print(f"[DEBUG] Response object: {response}")
            print(f"[DEBUG] Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            # If schema was used and LLM has structured output, response might be the schema directly
            # Check if response is an instance of the expected schema (not just any Pydantic model)
            if schema and isinstance(response, schema):
                # Pydantic model of expected type returned directly
                return {
                    'success': True,
                    'data': response.dict(),
                    'reprompt_count': reprompt_count
                }
            
            # Otherwise, parse manually from content
            # Handle different response structures
            print(f"[DEBUG] Checking for content attribute...")
            if hasattr(response, 'content'):
                print(f"[DEBUG] Has content, type: {type(response.content)}")
                try:
                    response_text = response.content
                    print(f"[DEBUG] Got response.content successfully: {type(response_text)}")
                except Exception as content_error:
                    print(f"[DEBUG] Error accessing response.content: {content_error}")
                    raise IndexError(f"Could not access response.content: {content_error}")
            elif hasattr(response, 'text'):
                response_text = response.text
                print(f"[DEBUG] Got response.text: {type(response_text)}")
            else:
                response_text = str(response)
                print(f"[DEBUG] Using str(response): {type(response_text)}")
            
            # Ensure response_text is a string
            if not isinstance(response_text, str):
                print(f"[DEBUG] response_text is not string, converting from {type(response_text)}")
                response_text = str(response_text)
            
            # Step 4: Strip markdown
            try:
                response_text = response_text.strip()
                if len(response_text) >= 7 and response_text.startswith('```json'):
                    response_text = response_text[7:]
                elif len(response_text) >= 3 and response_text.startswith('```'):
                    response_text = response_text[3:]
                if len(response_text) >= 3 and response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                print(f"[DEBUG] Step 4 (strip markdown) completed, cleaned length: {len(response_text)}")
            except Exception as e:
                print(f"[DEBUG] Step 4 (strip markdown) failed: {e}")
                raise e
            
            # Step 5: Parse JSON
            try:
                parsed_json = json.loads(response_text)
                print(f"[DEBUG] Step 5 (parse JSON) completed")
            except Exception as e:
                print(f"[DEBUG] Step 5 (parse JSON) failed: {e}")
                raise e
            
            # Step 6: Validate schema
            try:
                if schema:
                    validated_model = schema(**parsed_json)
                    return {
                        'success': True,
                        'data': validated_model.dict(),
                        'reprompt_count': reprompt_count
                    }
                else:
                    return {
                        'success': True,
                        'data': parsed_json,
                        'reprompt_count': reprompt_count
                    }
                print(f"[DEBUG] Step 6 (validate schema) completed")
            except Exception as e:
                print(f"[DEBUG] Step 6 (validate schema) failed: {e}")
                raise e
                
        except IndexError as e:
            last_error = e
            error_msg = f"List index out of range error: {str(e)}"
            print(f"[DEBUG] IndexError caught: {error_msg}")
            logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt == max_attempts - 1:
                # Final attempt failed
                await log_error_fn(
                    error_type="INDEX_ERROR_FINAL",
                    error_message=f"All {max_attempts} parse attempts failed: {error_msg}",
                    context={
                        **context,
                        'reprompt_count': reprompt_count,
                        'final_error': str(e)
                    }
                )
                
        except json.JSONDecodeError as e:
            last_error = e
            error_msg = f"JSON parse error: {str(e)}"
            logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt == max_attempts - 1:
                # Final attempt failed
                await log_error_fn(
                    error_type="JSON_PARSE_ERROR_FINAL",
                    error_message=f"All {max_attempts} parse attempts failed: {error_msg}",
                    context={
                        **context,
                        'reprompt_count': reprompt_count,
                        'final_error': str(e)
                    }
                )
                
        except ValidationError as e:
            last_error = e
            error_msg = f"Schema validation error: {str(e)}"
            logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt == max_attempts - 1:
                # Final attempt failed
                await log_error_fn(
                    error_type="VALIDATION_ERROR_FINAL",
                    error_message=f"All {max_attempts} validation attempts failed: {error_msg}",
                    context={
                        **context,
                        'reprompt_count': reprompt_count,
                        'validation_errors': e.errors()
                    }
                )
                
        except Exception as e:
            last_error = e
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt == max_attempts - 1:
                # Final attempt failed
                await log_error_fn(
                    error_type="PARSE_ERROR_FINAL",
                    error_message=f"All {max_attempts} attempts failed: {error_msg}",
                    context={
                        **context,
                        'reprompt_count': reprompt_count,
                        'error_type': type(e).__name__
                    }
                )
    
    # All attempts exhausted, return clean error
    return {
        'success': False,
        'error': {
            'type': 'PARSE_FAILURE',
            'message': f'Failed to parse LLM response after {max_attempts} attempts',
            'user_message': 'We encountered an error processing your request. Please escalate this issue to a human administrator for immediate assistance.',
            'technical_details': str(last_error) if last_error else 'Unknown error'
        },
        'reprompt_count': reprompt_count
    }


def create_fallback_response(
    error_type: str,
    error_message: str,
    user_message: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized fallback response for parse failures.
    
    Args:
        error_type: Type of error (e.g., 'JSON_PARSE_ERROR', 'VALIDATION_ERROR')
        error_message: Technical error message
        user_message: User-friendly error message
        context: Optional context dict with additional details
        
    Returns:
        Standardized error response dict
    """
    return {
        'success': False,
        'error': {
            'type': error_type,
            'message': error_message,
            'user_message': user_message
        },
        'context': context or {}
    }
