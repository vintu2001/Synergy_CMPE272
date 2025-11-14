"""
Classification prompt template for categorizing resident issues.

Citation-first design with emergency detection and human escalation triggers.
"""
from typing import List, Dict, Any, Optional
import json

from app.prompts.base import BasePromptTemplate


class ClassificationPrompt(BasePromptTemplate):
    """
    Prompt template for classification agent to categorize issues.
    
    Sections:
    - Context: Emergency policies and urgency matrices with citations
    - Issue: Resident message to classify
    - Instructions: Categorization task with output format
    - Output Contract: JSON schema with category, urgency, human_escalation
    - Critical Rules: Forbids outside knowledge, requires citations
    """
    
    def __init__(
        self,
        message_text: str,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize classification prompt template.
        
        Args:
            message_text: Resident's message to classify
            retrieved_docs: List of policy documents (emergency matrices, etc.)
            max_tokens: Maximum token limit
        """
        super().__init__(max_tokens=max_tokens, truncate_context=True)
        
        self.message_text = message_text
        self.retrieved_docs = retrieved_docs or []
    
    def build_sections(self) -> Dict[str, str]:
        """Build all prompt sections."""
        return {
            'context': self.format_context_section(
                self.retrieved_docs,
                title="CONTEXT (Emergency Policies and Urgency Matrices)"
            ),
            'issue': self._build_issue_section(),
            'instructions': self._build_instructions_section(),
            'output_contract': self._build_output_contract_section(),
            'rules': self.format_rules_section()
        }
    
    def _build_issue_section(self) -> str:
        """Build issue section."""
        return f"""=== ISSUE ===
Resident Message: {self.message_text}"""
    
    def _build_instructions_section(self) -> str:
        """Build task instructions."""
        return """=== INSTRUCTIONS ===
Classify this resident message using ONLY the Context documents above.

Determine:
1. Category: Maintenance, Billing, Community, Amenities, or Delivery
2. Urgency: High, Medium, or Low (based on emergency policies in Context)
3. Human Escalation: true if this requires immediate human attention per Context policies
4. Reasoning: Brief explanation citing specific policies

Emergency indicators (if mentioned in Context):
- Safety hazards (gas leaks, electrical, water flooding)
- Security issues (break-ins, suspicious activity)
- Health risks (mold, pest infestations)
- Extreme weather impacts
- Service outages affecting many residents"""
    
    def _build_output_contract_section(self) -> str:
        """Build output format specification."""
        schema = self.get_output_schema()
        schema_json = json.dumps(schema, indent=2)
        
        return f"""=== OUTPUT FORMAT ===
Return valid JSON matching this exact schema:

{schema_json}

Field requirements:
- category: One of [Maintenance, Billing, Community, Amenities, Delivery]
- urgency: One of [High, Medium, Low] based on Context policies
- human_escalation: Boolean - true if Context indicates immediate human review needed
- reasoning: Explanation based on Context (cite specific policies/criteria)
- confidence: 0-1 score indicating classification confidence
- sources: Array of doc_ids from Context that informed this classification (REQUIRED)"""
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for output."""
        return {
            "category": "string (Maintenance|Billing|Community|Amenities|Delivery)",
            "urgency": "string (High|Medium|Low)",
            "human_escalation": "boolean",
            "reasoning": "string (explanation from Context)",
            "confidence": "number (0-1)",
            "sources": ["string (doc_id1)", "string (doc_id2)"]
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get prompt metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "message_length": len(self.message_text),
            "context_docs_count": len(self.retrieved_docs)
        })
        return metadata
