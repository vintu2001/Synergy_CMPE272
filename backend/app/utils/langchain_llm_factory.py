"""
LangChain LLM Factory for Google Gemini.

Factory pattern for creating ChatGoogleGenerativeAI instances with
centralized configuration, timeout handling, and safety settings.
"""
import logging
from typing import Optional, Dict, Any, Type
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)


# Safety level mapping
SAFETY_LEVELS = {
    "BLOCK_NONE": HarmBlockThreshold.BLOCK_NONE,
    "BLOCK_ONLY_HIGH": HarmBlockThreshold.BLOCK_ONLY_HIGH,
    "BLOCK_MEDIUM_AND_ABOVE": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    "BLOCK_LOW_AND_ABOVE": HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}


def get_safety_settings(level: str) -> Dict[HarmCategory, HarmBlockThreshold]:
    """
    Get safety settings based on configured level.
    
    Args:
        level: Safety level name (BLOCK_NONE, BLOCK_ONLY_HIGH, etc.)
        
    Returns:
        Dictionary of safety settings for all harm categories
    """
    threshold = SAFETY_LEVELS.get(level, HarmBlockThreshold.BLOCK_ONLY_HIGH)
    
    return {
        HarmCategory.HARM_CATEGORY_HARASSMENT: threshold,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: threshold,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: threshold,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: threshold,
    }


def create_gemini_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    model: Optional[str] = None,
    safety_level: Optional[str] = None
) -> ChatGoogleGenerativeAI:
    """
    Factory function to create configured ChatGoogleGenerativeAI instance.
    
    This factory:
    - Reads configuration from centralized settings
    - Allows optional parameter overrides
    - Configures timeouts and safety settings
    - Provides consistent LLM setup across application
    
    Args:
        temperature: Optional override for temperature (0-2)
        max_tokens: Optional override for max output tokens
        timeout: Optional override for request timeout (seconds)
        model: Optional override for model name
        safety_level: Optional override for safety filtering level
        
    Returns:
        Configured ChatGoogleGenerativeAI instance
        
    Raises:
        ValueError: If GOOGLE_API_KEY is not configured
        
    Example:
        >>> llm = create_gemini_llm()
        >>> response = llm.invoke("Hello, world!")
        
        >>> # With overrides
        >>> llm = create_gemini_llm(temperature=0.7, model="gemini-2.5-flash")
    """
    settings = get_settings()
    
    # Verify API key is configured
    if not settings.GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not configured. "
            "Please set GOOGLE_API_KEY environment variable."
        )
    
    # Use settings or provided overrides
    final_model = model or settings.GEMINI_MODEL
    final_temperature = temperature if temperature is not None else settings.TEMPERATURE
    final_max_tokens = max_tokens or settings.GEMINI_MAX_TOKENS
    final_timeout = timeout or settings.GEMINI_TIMEOUT
    final_safety_level = safety_level or settings.GEMINI_SAFETY_LEVEL
    
    # Get safety settings
    safety_settings = get_safety_settings(final_safety_level)
    
    logger.info(
        f"Creating Gemini LLM: model={final_model}, "
        f"temperature={final_temperature}, "
        f"max_tokens={final_max_tokens}, "
        f"timeout={final_timeout}s, "
        f"safety={final_safety_level}"
    )
    
    # Create LangChain ChatGoogleGenerativeAI instance
    llm = ChatGoogleGenerativeAI(
        model=final_model,
        temperature=final_temperature,
        max_output_tokens=final_max_tokens,
        timeout=final_timeout,
        google_api_key=settings.GOOGLE_API_KEY,
        safety_settings=safety_settings,
        # Additional LangChain parameters
        convert_system_message_to_human=True,  # Gemini doesn't support system messages
    )
    
    return llm


def create_gemini_llm_for_json(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> ChatGoogleGenerativeAI:
    """
    Create Gemini LLM configured for JSON output.
    
    Uses temperature=0 by default for deterministic JSON generation.
    
    Args:
        temperature: Optional override (default: 0.0 for consistency)
        max_tokens: Optional override for max output tokens
        **kwargs: Additional arguments passed to create_gemini_llm
        
    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    # Force temperature to 0 for JSON unless explicitly overridden
    if temperature is None:
        temperature = 0.0
    
    return create_gemini_llm(
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def create_gemini_llm_with_schema(
    schema: Type[BaseModel],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    model: Optional[str] = None,
    **kwargs
):
    """
    Create Gemini LLM configured for structured output with Pydantic schema.
    
    NOTE: ChatGoogleGenerativeAI does not currently support with_structured_output().
    This factory creates a base LLM configured for structured output but does NOT
    wrap it with with_structured_output(). Instead, use parse_with_reprompt()
    from app.utils.parse_utils to handle response parsing and validation.
    
    This function exists for future compatibility when LangChain adds native
    structured output support for Gemini, and to maintain a consistent API.
    
    Args:
        schema: Pydantic BaseModel class defining the output structure
        temperature: Optional override for temperature (0-2)
        max_tokens: Optional override for max output tokens
        timeout: Optional override for request timeout (seconds)
        model: Optional override for model name
        **kwargs: Additional keyword arguments passed to create_gemini_llm
        
    Returns:
        LLM instance configured for JSON output (NOT wrapped with structured output)
        
    Raises:
        ValueError: If schema is not a Pydantic BaseModel subclass
        
    Example:
        >>> from app.models.structured_schemas import SimulationOutputSchema
        >>> from app.utils.parse_utils import parse_with_reprompt
        >>> 
        >>> llm = create_gemini_llm_with_schema(SimulationOutputSchema)
        >>> result = await parse_with_reprompt(
        ...     llm=llm,
        ...     initial_prompt="Generate 2 maintenance options",
        ...     schema=SimulationOutputSchema,
        ...     context={'test': 'example'},
        ...     log_error_fn=log_function
        ... )
        >>> if result['success']:
        ...     options = result['data']['options']
    """
    if not issubclass(schema, BaseModel):
        raise ValueError(f"Schema must be a Pydantic BaseModel subclass, got {type(schema)}")
    
    # Create base LLM configured for JSON responses
    # Use temperature=0 by default for more deterministic structured output
    base_llm = create_gemini_llm(
        temperature=temperature if temperature is not None else 0.0,
        max_tokens=max_tokens,
        timeout=timeout,
        model=model,
        **kwargs
    )
    
    logger.info(
        f"Created LLM for structured output with schema: {schema.__name__}. "
        f"Note: Use parse_with_reprompt() for response parsing and validation."
    )
    
    return base_llm


def get_available_models() -> Dict[str, str]:
    """
    Get available Gemini model names and descriptions.
    
    Returns:
        Dictionary of model names and their descriptions
    """
    return {
        "gemini-2.5-flash": "Fast, cost-efficient model for high-volume tasks",
        "gemini-2.5-pro": "Most capable model for complex reasoning tasks",
        "gemini-1.5-flash": "Previous generation fast model",
        "gemini-1.5-pro": "Previous generation capable model",
    }


def validate_model_name(model: str) -> bool:
    """
    Validate if model name is supported.
    
    Args:
        model: Model name to validate
        
    Returns:
        True if model is supported
    """
    return model in get_available_models()
