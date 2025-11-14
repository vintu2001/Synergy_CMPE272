"""
LangChain/LLM error handling utilities.

Provides user-friendly error messages for LLM failures including
timeouts, safety blocks, and API errors.
"""
import logging
from typing import Dict, Any, Optional
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    
    def __init__(
        self,
        message: str,
        error_type: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.user_message = user_message
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.user_message,
                "details": str(self)
            }
        }


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    
    def __init__(self, timeout: int, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"LLM request timed out after {timeout} seconds",
            error_type="LLM_TIMEOUT",
            user_message=(
                "The request took too long to process. "
                "Please try again or contact support if the issue persists."
            ),
            context=context
        )
        self.timeout = timeout


class LLMSafetyError(LLMError):
    """Raised when content is blocked by safety filters."""
    
    def __init__(self, reason: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Content blocked by safety filters: {reason}",
            error_type="LLM_SAFETY_BLOCK",
            user_message=(
                "Unable to process this request due to content safety policies. "
                "Please rephrase your message and try again."
            ),
            context=context
        )
        self.reason = reason


class LLMAPIError(LLMError):
    """Raised when LLM API returns an error."""
    
    def __init__(self, api_error: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"LLM API error: {api_error}",
            error_type="LLM_API_ERROR",
            user_message=(
                "Unable to generate a response at this time. "
                "Please try again later or escalate to a human administrator."
            ),
            context=context
        )
        self.api_error = api_error


class LLMConfigurationError(LLMError):
    """Raised when LLM is not properly configured."""
    
    def __init__(self, issue: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"LLM configuration error: {issue}",
            error_type="LLM_NOT_CONFIGURED",
            user_message=(
                "The AI service is not properly configured. "
                "Please contact an administrator."
            ),
            context=context
        )
        self.issue = issue


def handle_llm_errors(func):
    """
    Decorator to handle LLM errors and convert to user-friendly responses.
    
    Usage:
        @handle_llm_errors
        async def my_llm_function(...):
            ...
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.TimeoutError as e:
            timeout = kwargs.get('timeout', 60)
            error = LLMTimeoutError(timeout=timeout)
            logger.error(f"LLM timeout: {error}", exc_info=True)
            return error.to_dict()
        except ValueError as e:
            if "safety" in str(e).lower() or "blocked" in str(e).lower():
                error = LLMSafetyError(reason=str(e))
                logger.warning(f"LLM safety block: {error}")
                return error.to_dict()
            else:
                error = LLMAPIError(api_error=str(e))
                logger.error(f"LLM API error: {error}", exc_info=True)
                return error.to_dict()
        except Exception as e:
            error = LLMAPIError(api_error=str(e))
            logger.error(f"Unexpected LLM error: {error}", exc_info=True)
            return error.to_dict()
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except asyncio.TimeoutError as e:
            timeout = kwargs.get('timeout', 60)
            error = LLMTimeoutError(timeout=timeout)
            logger.error(f"LLM timeout: {error}", exc_info=True)
            return error.to_dict()
        except ValueError as e:
            if "safety" in str(e).lower() or "blocked" in str(e).lower():
                error = LLMSafetyError(reason=str(e))
                logger.warning(f"LLM safety block: {error}")
                return error.to_dict()
            else:
                error = LLMAPIError(api_error=str(e))
                logger.error(f"LLM API error: {error}", exc_info=True)
                return error.to_dict()
        except Exception as e:
            error = LLMAPIError(api_error=str(e))
            logger.error(f"Unexpected LLM error: {error}", exc_info=True)
            return error.to_dict()
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def parse_llm_response_error(response: Any) -> Optional[LLMError]:
    """
    Parse LLM response for errors (safety blocks, etc.).
    
    Args:
        response: LLM response object
        
    Returns:
        LLMError if error detected, None otherwise
    """
    # Check for safety blocks in Gemini response
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        
        # Check finish reason
        if hasattr(candidate, 'finish_reason'):
            finish_reason = candidate.finish_reason
            
            if finish_reason == 3:  # SAFETY
                return LLMSafetyError(reason="Content blocked by safety filters")
            elif finish_reason == 4:  # RECITATION
                return LLMSafetyError(reason="Content blocked due to recitation")
            elif finish_reason == 2:  # MAX_TOKENS
                return LLMAPIError(api_error="Response truncated due to token limit")
    
    return None


def create_error_response(
    error_type: str,
    user_message: str,
    technical_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standardized error response dictionary.
    
    Args:
        error_type: Error type identifier
        user_message: User-friendly error message
        technical_message: Optional technical details
        
    Returns:
        Dictionary with error information
    """
    response = {
        "error": {
            "type": error_type,
            "message": user_message
        }
    }
    
    if technical_message:
        response["error"]["details"] = technical_message
    
    return response
