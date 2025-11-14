"""
Rules normalization prompt template for decision-making.

Extracts policy rules, weights, caps, and escalation criteria from KB documents.
"""
from typing import List, Dict, Any, Optional
import json

from app.prompts.base import BasePromptTemplate


class RulesPrompt(BasePromptTemplate):
    """
    Prompt template for extracting decision rules from policy documents.
    
    Sections:
    - Context: Policy/SLA documents with [Source DOC_ID] citations
    - Instructions: Extract weights, caps, escalation rules
    - Output Contract: Strict JSON schema with normalized weights (sum=1.0)
    - Critical Rules: Forbids outside knowledge, requires citations
    """
    
    def __init__(
        self,
        category: str,
        urgency: str,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize rules normalization prompt template.
        
        Args:
            category: Issue category (for context)
            urgency: Urgency level (for context)
            retrieved_docs: List of policy/SLA documents from RAG retrieval
            max_tokens: Maximum token limit
        """
        super().__init__(max_tokens=max_tokens, truncate_context=True)
        
        self.category = category
        self.urgency = urgency
        self.retrieved_docs = retrieved_docs or []
    
    def build_sections(self) -> Dict[str, str]:
        """Build all prompt sections."""
        return {
            'context': self.format_context_section(
                self.retrieved_docs,
                title="CONTEXT (Policy Rules and SLAs)"
            ),
            'instructions': self._build_instructions_section(),
            'output_contract': self._build_output_contract_section(),
            'rules': self.format_rules_section()
        }
    
    def _build_instructions_section(self) -> str:
        """Build task instructions."""
        return f"""=== INSTRUCTIONS ===
Extract decision-making rules from the Context documents for {self.category} issues at {self.urgency} urgency.

Your task:
1. Identify decision weights (urgency, cost, time, satisfaction) - must sum to 1.0
2. Extract cost and time thresholds/caps
3. Identify escalation triggers and conditions
4. Cite all source document IDs used

If specific values are not in Context, use reasonable defaults based on general patterns
described in the documents, but indicate which values are inferred vs. explicit."""
    
    def _build_output_contract_section(self) -> str:
        """Build output format specification."""
        schema = self.get_output_schema()
        schema_json = json.dumps(schema, indent=2)
        
        return f"""=== OUTPUT FORMAT ===
Return valid JSON matching this exact schema:

{schema_json}

Field requirements:
- weights: All values 0-1, MUST sum to exactly 1.0
  * urgency_weight: Priority based on urgency level
  * cost_weight: Importance of minimizing cost
  * time_weight: Importance of fast resolution
  * satisfaction_weight: Importance of resident satisfaction
  
- caps: Maximum thresholds for filtering options
  * max_cost: Maximum allowable cost (dollars)
  * max_time: Maximum allowable time (hours)
  
- escalation: When to escalate to human
  * cost_threshold: Cost above which human approval needed
  * time_threshold: Time above which human approval needed
  * conditions: Array of text conditions from policies
  
- sources: Array of doc_ids from Context (REQUIRED)
- explicit_values: Array of field names that were explicitly stated in Context
- inferred_values: Array of field names that were inferred/defaulted"""
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for output."""
        return {
            "weights": {
                "urgency_weight": "number (0-1)",
                "cost_weight": "number (0-1)",
                "time_weight": "number (0-1)",
                "satisfaction_weight": "number (0-1)"
            },
            "caps": {
                "max_cost": "number (dollars)",
                "max_time": "number (hours)"
            },
            "escalation": {
                "cost_threshold": "number (dollars)",
                "time_threshold": "number (hours)",
                "conditions": ["string (condition1)", "string (condition2)"]
            },
            "sources": ["string (doc_id1)", "string (doc_id2)"],
            "explicit_values": ["string (field_name1)"],
            "inferred_values": ["string (field_name1)"]
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get prompt metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "category": self.category,
            "urgency": self.urgency,
            "context_docs_count": len(self.retrieved_docs)
        })
        return metadata
