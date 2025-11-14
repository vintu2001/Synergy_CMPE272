"""
Multi-Step Reasoning Engine (Level 3)
Implements Chain-of-Thought and ReAct pattern for complex decision-making.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from app.models.schemas import IssueCategory, Urgency
from app.utils.llm_client import llm_client
from app.utils.langchain_llm_factory import create_gemini_llm_with_schema
from app.models.structured_schemas import ComplexityAnalysisSchema, ReasoningChainSchema
from app.utils.parse_utils import parse_with_reprompt
import logging
import json

logger = logging.getLogger(__name__)


class ReasoningStep(str, Enum):
    """Types of reasoning steps in the ReAct pattern."""
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    OBSERVE = "observe"
    REFLECT = "reflect"


class MultiStepReasoner:
    """
    Implements multi-step reasoning for complex issues.
    Uses Chain-of-Thought and ReAct pattern.
    """
    
    def __init__(self):
        self.llm_client = llm_client
    
    async def analyze_complexity(
        self,
        message_text: str,
        category: str,
        urgency: str,
        tools_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze issue complexity using structured output.
        Uses ComplexityAnalysisSchema for type-safe responses.
        
        Returns:
            Dict with complexity analysis or fallback to simple
        """
        if not self.llm_client.enabled:
            return {
                'complexity_level': 'simple',
                'reasoning_required': False,
                'factors': ['LLM disabled'],
                'confidence': 0.0
            }
        
        try:
            # Create LLM with structured output
            structured_llm = create_gemini_llm_with_schema(
                schema=ComplexityAnalysisSchema,
                temperature=0.0,
                model="gemini-2.5-flash"
            )
            
            prompt = f"""Analyze this apartment issue for complexity.

Issue: "{message_text}"
Category: {category}, Urgency: {urgency}

Mark as COMPLEX if:
- Multiple systems affected (e.g., "water AND electrical")
- Safety hazard (e.g., "sparking", "gas leak", "flooding")
- Structural damage (e.g., "ceiling collapse", "foundation")
- Affects multiple units
- Recurring issue (happened 3+ times)

Mark as SIMPLE if:
- Single component fix (e.g., "dripping faucet", "broken lock")
- Standard maintenance
- Clear root cause

Return JSON matching ComplexityAnalysisSchema:
- complexity_level: "simple", "moderate", or "complex"
- reasoning_required: true if multi-step needed, false otherwise
- factors: array of factors contributing to complexity
- confidence: 0.0-1.0

Be conservative - most issues are simple."""
            
            # Use structured output with reprompt
            from app.utils.llm_client import log_error_to_cloudwatch
            result = await parse_with_reprompt(
                llm=structured_llm,
                initial_prompt=prompt,
                schema=ComplexityAnalysisSchema,
                context={
                    'category': category,
                    'urgency': urgency
                },
                log_error_fn=log_error_to_cloudwatch,
                max_attempts=2
            )
            
            if result['success']:
                data = result['data']
                logger.info(
                    f"Complexity analysis: {data['complexity_level']} "
                    f"(reasoning_required={data['reasoning_required']}, "
                    f"confidence={data['confidence']:.2f})"
                )
                return data
            else:
                # Fallback to simple on parse failure
                logger.error(f"Complexity analysis failed: {result['error']['message']}")
                return {
                    'complexity_level': 'simple',
                    'reasoning_required': False,
                    'factors': ['Parse failure - defaulting to simple'],
                    'confidence': 0.0
                }
        
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            return {
                'complexity_level': 'simple',
                'reasoning_required': False,
                'factors': [f'Error: {str(e)}'],
                'confidence': 0.0
            }
    
    async def generate_reasoning_chain(
        self,
        message_text: str,
        category: str,
        urgency: str,
        risk_score: float,
        tools_data: Dict[str, Any],
        complexity_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate multi-step reasoning chain using structured output.
        Uses ReasoningChainSchema for type-safe responses.
        
        Returns:
            Dict with 'steps', 'final_recommendation', 'confidence' or error
        """
        if not complexity_analysis.get('reasoning_required'):
            return {'steps': [], 'reasoning_type': 'single_step'}
        
        try:
            # Create LLM with structured output
            structured_llm = create_gemini_llm_with_schema(
                schema=ReasoningChainSchema,
                temperature=0.0,
                model="gemini-2.5-flash"
            )
            
            prompt = f"""Create a multi-step reasoning plan for this complex issue:

"{message_text}"
Category: {category}, Urgency: {urgency}, Risk: {risk_score}

Generate 2-4 sequential reasoning steps. For each step, provide:
- step: Brief description of what to analyze or do
- rationale: Why this step is necessary

Then provide:
- final_recommendation: Overall recommendation based on the reasoning
- confidence: 0.0-1.0 confidence in the reasoning chain

Return JSON matching ReasoningChainSchema.

Keep descriptions concise but actionable."""
            
            # Use structured output with reprompt
            from app.utils.llm_client import log_error_to_cloudwatch
            result = await parse_with_reprompt(
                llm=structured_llm,
                initial_prompt=prompt,
                schema=ReasoningChainSchema,
                context={
                    'category': category,
                    'urgency': urgency,
                    'risk_score': risk_score
                },
                log_error_fn=log_error_to_cloudwatch,
                max_attempts=2
            )
            
            if result['success']:
                data = result['data']
                logger.info(f"Generated {len(data['steps'])} reasoning steps (confidence={data['confidence']:.2f})")
                return data
            else:
                # Fallback to empty on parse failure
                logger.error(f"Reasoning chain generation failed: {result['error']['message']}")
                return {'steps': [], 'final_recommendation': 'Unable to generate reasoning chain', 'confidence': 0.0}
        
        except Exception as e:
            logger.error(f"Reasoning chain generation failed: {e}")
            return {'steps': [], 'final_recommendation': f'Error: {str(e)}', 'confidence': 0.0}
    
    async def create_phased_options(
        self,
        reasoning_chain: Dict[str, Any],
        category: str,
        urgency: str
    ) -> List[Dict[str, Any]]:
        """
        Create phased resolution options from reasoning chain.
        Each option represents a different execution strategy.
        
        Returns:
            List of 3 options with phased approaches
        """
        if not reasoning_chain.get('steps'):
            return []
        
        try:
            steps = reasoning_chain['steps']
            total_time = reasoning_chain.get('total_estimated_time', 0)
            total_cost = reasoning_chain.get('total_estimated_cost', 0)
            
            # Option 1: Full phased approach (all steps)
            option_1 = {
                'option_id': 'opt_phased_complete',
                'action': self._format_phased_action(steps, 'complete'),
                'estimated_cost': total_cost,
                'time_to_resolution': total_time,
                'resident_satisfaction_impact': 0.90,
                'reasoning': f"Most thorough solution with {len(steps)} coordinated steps for permanent fix",
                'details': self._format_detailed_phases(steps),  # For UI dropdown
                'phases': steps,
                'is_permanent_solution': True,
                'requires_resident_action': False
            }
            
            # Option 2: Expedited (skip non-critical steps)
            critical_steps = [s for s in steps if s.get('risk_level') != 'low']
            expedited_time = total_time * 0.6
            expedited_cost = total_cost * 0.75
            
            option_2 = {
                'option_id': 'opt_phased_expedited',
                'action': self._format_phased_action(critical_steps, 'expedited'),
                'estimated_cost': expedited_cost,
                'time_to_resolution': expedited_time,
                'resident_satisfaction_impact': 0.80,
                'reasoning': f"Faster resolution focusing on essential repairs first",
                'details': self._format_detailed_phases(critical_steps if critical_steps else steps),  # For UI dropdown
                'phases': critical_steps,
                'is_permanent_solution': True,
                'requires_resident_action': False
            }
            
            # Option 3: Emergency immediate action + follow-up
            first_step = steps[0] if steps else None
            emergency_time = first_step.get('estimated_time_hours', 2.0) if first_step else 2.0
            emergency_cost = first_step.get('estimated_cost', 150.0) if first_step else 150.0
            
            # Format emergency details differently (immediate + follow-up)
            emergency_details = []
            if first_step:
                emergency_details.append({
                    'step': 1,
                    'title': '🚨 Immediate Emergency Response',
                    'description': first_step.get('action', 'Secure area and prevent further damage'),
                    'time': f"{first_step.get('estimated_time_hours', 2.0):.1f}h",
                    'status': 'immediate'
                })
            emergency_details.append({
                'step': 2,
                'title': '📅 Scheduled Follow-Up',
                'description': 'Complete comprehensive repair and permanent fix',
                'time': '24-48 hours',
                'status': 'scheduled'
            })
            
            option_3 = {
                'option_id': 'opt_phased_emergency',
                'action': self._format_phased_action(steps, 'emergency'),
                'estimated_cost': emergency_cost * 1.2,  # Emergency premium
                'time_to_resolution': emergency_time,
                'resident_satisfaction_impact': 0.75,
                'reasoning': "Quickest response to handle immediate safety concerns",
                'details': emergency_details,  # For UI dropdown
                'phases': [first_step] if first_step else [],
                'follow_up_required': True,
                'is_permanent_solution': False,
                'requires_resident_action': False
            }
            
            return [option_1, option_2, option_3]
        
        except Exception as e:
            logger.error(f"Failed to create phased options: {e}")
            return []
    
    def _format_phased_action(self, steps: List[Dict], approach_type: str) -> str:
        """Format steps into a simple, user-friendly description."""
        if not steps:
            return "Multi-phase resolution approach"
        
        # Extract key actions and summarize
        first_action = steps[0].get('action', '') if len(steps) > 0 else ''
        num_phases = len(steps)
        
        # Create user-friendly descriptions based on approach type
        if approach_type == 'complete':
            return f"Full professional repair with {num_phases} coordinated steps to completely resolve the issue and prevent recurrence"
        elif approach_type == 'expedited':
            return f"Fast-track repair focusing on critical fixes to restore functionality quickly"
        elif approach_type == 'emergency':
            return f"Immediate emergency response to secure the area and prevent further damage, with detailed follow-up scheduled"
        else:
            return f"{num_phases}-step professional repair process"
    
    def _format_detailed_phases(self, steps: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format steps into structured details for UI dropdown.
        Returns a list of phase objects with step number, title, description, and time.
        """
        if not steps:
            return []
        
        detailed_phases = []
        for i, step in enumerate(steps, 1):
            # Create user-friendly phase titles based on step type
            step_type = step.get('type', 'execute')
            title_map = {
                'diagnose': f'Step {i}: Diagnosis & Assessment',
                'coordinate': f'Step {i}: Coordination & Setup',
                'execute': f'Step {i}: Repair & Execution',
                'verify': f'Step {i}: Testing & Verification'
            }
            
            phase = {
                'step': i,
                'title': title_map.get(step_type, f'Step {i}: Action'),
                'description': step.get('action', 'Perform necessary repairs'),
                'time': f"{step.get('estimated_time_hours', 2.0):.1f}h",
                'cost': f"${step.get('estimated_cost', 100.0):.2f}",
                'risk': step.get('risk_level', 'medium')
            }
            detailed_phases.append(phase)
        
        return detailed_phases


# Global instance
multi_step_reasoner = MultiStepReasoner()

