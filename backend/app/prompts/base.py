"""
Base class for prompt templates with citation-first design.

All prompts enforce token limits and require explicit output contracts.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

from app.config import get_settings
from app.prompts.utils import (
    estimate_tokens,
    validate_token_limit,
    truncate_context_documents,
    format_citations
)

logger = logging.getLogger(__name__)
settings = get_settings()


class BasePromptTemplate(ABC):
    """
    Abstract base class for all prompt templates.
    
    Enforces:
    - Token limit validation
    - Citation-first context formatting
    - Explicit output contracts
    - "Use only Context" instructions
    """
    
    def __init__(
        self,
        max_tokens: Optional[int] = None,
        truncate_context: bool = True
    ):
        """
        Initialize base template.
        
        Args:
            max_tokens: Maximum token limit (defaults to settings.MAX_CONTEXT_TOKENS)
            truncate_context: Whether to auto-truncate context to fit budget
        """
        self.max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS
        self.truncate_context = truncate_context
    
    @abstractmethod
    def build_sections(self) -> Dict[str, str]:
        """
        Build individual prompt sections.
        
        Returns:
            Dict mapping section names to content:
            - 'issue': Issue description
            - 'context': Context with citations
            - 'instructions': Task instructions
            - 'output_contract': Expected output format
            - 'rules': Critical rules and constraints
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for expected output.
        
        Returns:
            Dict representing output structure
        """
        pass
    
    def format_context_section(
        self,
        documents: List[Dict[str, Any]],
        title: str = "CONTEXT (Knowledge Base Documents)"
    ) -> str:
        """
        Format context section with citations.
        
        Args:
            documents: List of retrieved documents
            title: Section title
            
        Returns:
            Formatted context section with [Source DOC_ID] citations
        """
        if not documents:
            return f"=== {title} ===\nNo relevant documents found.\n"
        
        # Truncate if needed
        if self.truncate_context:
            # Reserve 30% of token budget for context
            context_budget = int(self.max_tokens * 0.3)
            documents = truncate_context_documents(documents, context_budget)
        
        citations = format_citations(documents, max_length=500)
        
        return f"=== {title} ===\n{citations}\n"
    
    def format_rules_section(self) -> str:
        """
        Format critical rules section (common to all prompts).
        
        Returns:
            Formatted rules section
        """
        return """=== CRITICAL RULES ===
1. Use ONLY information from the Context section above
2. Cite source document IDs (doc_id) in your response
3. Do NOT use outside knowledge or make assumptions
4. Return valid JSON matching the Output Format exactly
5. If Context is insufficient, indicate limitations in your response
"""
    
    def render(self) -> str:
        """
        Render complete prompt from sections.
        
        Returns:
            Complete prompt string
            
        Raises:
            ValueError: If prompt exceeds token limit
        """
        sections = self.build_sections()
        
        # Build prompt from sections
        prompt_parts = []
        
        # Add sections in order
        if 'issue' in sections:
            prompt_parts.append(sections['issue'])
        
        if 'context' in sections:
            prompt_parts.append(sections['context'])
        
        if 'instructions' in sections:
            prompt_parts.append(sections['instructions'])
        
        if 'output_contract' in sections:
            prompt_parts.append(sections['output_contract'])
        
        if 'rules' in sections:
            prompt_parts.append(sections['rules'])
        
        prompt = "\n\n".join(prompt_parts)
        
        # Validate token limit
        validate_token_limit(prompt, self.max_tokens, context="Prompt")
        
        return prompt
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get prompt metadata (for logging/debugging).
        
        Returns:
            Dict with prompt metadata
        """
        return {
            "template_class": self.__class__.__name__,
            "max_tokens": self.max_tokens,
            "truncate_context": self.truncate_context
        }
