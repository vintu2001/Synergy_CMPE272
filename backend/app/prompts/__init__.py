"""
Prompt templates for Synergy Agentic Apartment Manager.

Citation-first prompt templates with strict token limits and output contracts.
"""
from app.prompts.base import BasePromptTemplate
from app.prompts.simulation_prompt import SimulationPrompt
from app.prompts.rules_prompt import RulesPrompt
from app.prompts.classification_prompt import ClassificationPrompt
from app.prompts.utils import (
    estimate_tokens,
    validate_token_limit,
    truncate_context_documents,
    format_citations,
    format_citation,
    build_json_schema
)

__all__ = [
    "BasePromptTemplate",
    "SimulationPrompt",
    "RulesPrompt",
    "ClassificationPrompt",
    "estimate_tokens",
    "validate_token_limit",
    "truncate_context_documents",
    "format_citations",
    "format_citation",
    "build_json_schema"
]
