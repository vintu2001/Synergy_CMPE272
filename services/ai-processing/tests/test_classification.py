"""
Tests for AI Classification Agent
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.agents.classification_agent import (
    classify_message, 
    rule_based_classification,
    gemini_classification
)
from app.models.schemas import MessageRequest, IssueCategory, Urgency, Intent


@pytest.fixture
def maintenance_message():
    return MessageRequest(
        resident_id="RES123",
        message_text="Water is leaking from my ceiling"
    )


@pytest.fixture
def billing_message():
    return MessageRequest(
        resident_id="RES456",
        message_text="I was charged twice for rent this month"
    )


@pytest.fixture
def question_message():
    return MessageRequest(
        resident_id="RES789",
        message_text="What are the pool hours?"
    )


@pytest.fixture
def escalation_message():
    return MessageRequest(
        resident_id="RES999",
        message_text="This is unacceptable, I want to speak to the manager"
    )




def test_rule_based_classification_escalation():
    category, urgency, intent, confidence = rule_based_classification(
        "I want to speak to a manager about this issue"
    )
    
    assert intent == Intent.HUMAN_ESCALATION
    assert confidence > 0.5


def test_rule_based_classification_question():
    category, urgency, intent, confidence = rule_based_classification(
        "What are the gym hours?"
    )
    
    assert intent == Intent.ANSWER_QUESTION


def test_rule_based_classification_deliveries():
    category, urgency, intent, confidence = rule_based_classification(
        "My package was delivered but I can't find it"
    )
    
    assert category == IssueCategory.DELIVERIES
    assert confidence > 0.5


def test_rule_based_classification_amenities():
    category, urgency, intent, confidence = rule_based_classification(
        "The pool is dirty and needs cleaning"
    )
    
    assert category == IssueCategory.AMENITIES


@pytest.mark.asyncio
async def test_classify_message_high_confidence(maintenance_message):
    with patch('app.agents.classification_agent.rule_based_classification') as mock_rule:
        mock_rule.return_value = (
            IssueCategory.MAINTENANCE,
            Urgency.HIGH,
            Intent.SOLVE_PROBLEM,
            0.95
        )
        
        result = await classify_message(maintenance_message)
        
        assert result.category == IssueCategory.MAINTENANCE
        assert result.urgency == Urgency.HIGH
        assert result.intent == Intent.SOLVE_PROBLEM
        assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_classify_message_low_confidence_triggers_gemini(maintenance_message):
    with patch('app.agents.classification_agent.rule_based_classification') as mock_rule:
        mock_rule.return_value = (None, None, Intent.SOLVE_PROBLEM, 0.3)
        
        with patch('app.agents.classification_agent.gemini_classification') as mock_gemini:
            mock_gemini.return_value = AsyncMock(
                category=IssueCategory.MAINTENANCE,
                urgency=Urgency.HIGH,
                intent=Intent.SOLVE_PROBLEM,
                confidence=0.92
            )
            
            result = await classify_message(maintenance_message)
            
            mock_gemini.assert_called_once()
            assert result.confidence == 0.92


@pytest.mark.asyncio
async def test_gemini_classification_error_fallback():
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_model.return_value.generate_content.side_effect = Exception("API Error")
        
        result = await gemini_classification("Test message")
        
        assert result.category == IssueCategory.MAINTENANCE
        assert result.urgency == Urgency.MEDIUM
        assert result.confidence == 0.5


def test_urgency_keywords_detected():
    high_urgency_messages = [
        "Emergency! Water flooding my apartment",
        "Gas leak smell in kitchen",
        "Fire alarm going off"
    ]
    
    for msg in high_urgency_messages:
        _, urgency, _, _ = rule_based_classification(msg)
        assert urgency == Urgency.HIGH



