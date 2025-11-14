"""
Simulation prompt template for generating resolution options.

Citation-first design with strict output contract requiring sources[] field.
"""
from typing import List, Dict, Any, Optional
import json

from app.prompts.base import BasePromptTemplate


class SimulationPrompt(BasePromptTemplate):
    """
    Prompt template for simulation agent to generate resolution options.
    
    Sections:
    - Issue: Problem description with metadata
    - Context: Retrieved KB documents with [Source DOC_ID] citations
    - Instructions: Task specification with output format
    - Output Contract: JSON schema for 3-5 options with sources[]
    - Critical Rules: Forbids outside knowledge, requires citations
    """
    
    def __init__(
        self,
        issue_text: str,
        category: str,
        urgency: str,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        risk_score: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize simulation prompt template.
        
        Args:
            issue_text: Resident's issue description
            category: Issue category (Maintenance, Billing, etc.)
            urgency: Urgency level (High, Medium, Low)
            retrieved_docs: List of KB documents from RAG retrieval
            risk_score: Risk prediction score (0-1)
            max_tokens: Maximum token limit
        """
        super().__init__(max_tokens=max_tokens, truncate_context=True)
        
        self.issue_text = issue_text
        self.category = category
        self.urgency = urgency
        self.retrieved_docs = retrieved_docs or []
        self.risk_score = risk_score
    
    def build_sections(self) -> Dict[str, str]:
        """Build all prompt sections."""
        return {
            'issue': self._build_issue_section(),
            'context': self.format_context_section(
                self.retrieved_docs,
                title="CONTEXT (Knowledge Base Documents)"
            ),
            'instructions': self._build_instructions_section(),
            'output_contract': self._build_output_contract_section(),
            'rules': self._build_rules_section()
        }
    
    def _build_issue_section(self) -> str:
        """Build issue description section."""
        risk_info = ""
        if self.risk_score is not None:
            risk_info = f"\nRisk Score: {self.risk_score:.2f}"
        
        return f"""=== ISSUE ===
Resident Report: {self.issue_text}
Category: {self.category}
Urgency: {self.urgency}{risk_info}"""
    
    def _build_instructions_section(self) -> str:
        """Build task instructions."""
        if not self.retrieved_docs or len(self.retrieved_docs) == 0:
            # No context documents available - must escalate to human
            return """=== INSTRUCTIONS ===
CRITICAL: No relevant knowledge base documents were found for this issue.

You MUST generate exactly ONE escalation option with the following details:
- Explain that no policy documentation is available
- Indicate that human review is required
- Set estimated_cost to 0.00
- Set estimated_time to 0.5 hours (30 minutes for human review)
- Use empty sources[] array
- Use empty preconditions[] array

Do NOT attempt to resolve this issue without documentation.
Do NOT use general knowledge or make assumptions.
ONLY generate a human escalation option."""
        else:
            # Context documents available - use them
            return """=== INSTRUCTIONS ===
Generate 3-5 resolution options for this issue using ONLY the Context documents above.

Each option should:
- Be actionable and specific to this situation
- Include realistic cost and time estimates
- Explain reasoning based on Context policies/procedures
- List preconditions if any (e.g., "requires approval", "resident must be present")
- Cite the source document IDs that informed this option

Provide a range of options:
- Fast/Premium option (higher cost, faster resolution)
- Standard option (balanced cost and time)
- Budget option (lower cost, may take longer)
- Additional alternatives as appropriate"""
    
    def _build_output_contract_section(self) -> str:
        """Build output format specification."""
        schema = self.get_output_schema()
        schema_json = json.dumps(schema, indent=2)
        
        return f"""=== OUTPUT FORMAT ===
Return valid JSON matching this exact schema:

{schema_json}

Field requirements:
- option_id: Unique identifier ("opt_1", "opt_2", etc.)
- action: Brief description (1-2 sentences max)
- estimated_cost: Dollar amount as number (e.g., 150.00)
- estimated_time: Hours as number (e.g., 2.5)
- reasoning: Explanation based on Context (cite specific policies/procedures)
- preconditions: Array of strings, empty array [] if none
- sources: Array of doc_ids from Context that informed this option (REQUIRED)"""
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for output."""
        if not self.retrieved_docs or len(self.retrieved_docs) == 0:
            # No documents - expect single escalation option
            return {
                "options": [
                    {
                        "option_id": "string (opt_escalate_1)",
                        "action": "string (escalation message explaining no documentation available)",
                        "estimated_cost": "number (0.00)",
                        "estimated_time": "number (0.5)",
                        "reasoning": "string (explain why escalation is needed)",
                        "preconditions": [],
                        "sources": []
                    }
                ]
            }
        else:
            # Documents available - expect 3-5 options
            return {
                "options": [
                    {
                        "option_id": "string (opt_1, opt_2, etc.)",
                        "action": "string (brief description)",
                        "estimated_cost": "number (dollar amount)",
                        "estimated_time": "number (hours)",
                        "reasoning": "string (explanation from Context)",
                        "preconditions": ["string (condition1)", "string (condition2)"],
                        "sources": ["string (doc_id1)", "string (doc_id2)"]
                    }
                ]
            }
    
    def _build_rules_section(self) -> str:
        """Build rules section that enforces strict RAG-only approach."""
        if not self.retrieved_docs or len(self.retrieved_docs) == 0:
            # No context documents - must escalate
            return """=== CRITICAL RULES ===
1. NO policy documentation is available for this issue
2. You MUST NOT use general knowledge or external information
3. You MUST NOT make assumptions about procedures or policies
4. Generate ONLY a human escalation option
5. Return valid JSON matching the Output Format exactly"""
        else:
            # Context documents available - restrict to context only
            return """=== CRITICAL RULES ===
1. Use ONLY information from the Context section above
2. Cite source document IDs (doc_id) in your response
3. Do NOT use outside knowledge or make assumptions
4. Return valid JSON matching the Output Format exactly
5. If Context is insufficient, indicate limitations in your response"""

    def get_metadata(self) -> Dict[str, Any]:
        """Get prompt metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "issue_category": self.category,
            "issue_urgency": self.urgency,
            "context_docs_count": len(self.retrieved_docs),
            "risk_score": self.risk_score
        })
        return metadata
