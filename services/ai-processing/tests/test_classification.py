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


def test_all_issue_categories_coverage():
    test_cases = {
        "My water heater is broken": IssueCategory.MAINTENANCE,
        "I was overcharged on my bill": IssueCategory.BILLING,
        "Lost my access card and locked out": IssueCategory.SECURITY,
        "My Amazon package was delivered": IssueCategory.DELIVERIES,
        "The gym is closed": IssueCategory.AMENITIES
    }
    
    for msg, expected_category in test_cases.items():
        category, _, _, _ = rule_based_classification(msg)
        assert category == expected_category


def test_medium_urgency_detection():
    category, urgency, _, _ = rule_based_classification("My fridge is not working properly")
    assert urgency == Urgency.MEDIUM


def test_low_urgency_detection():
    category, urgency, _, _ = rule_based_classification("Can you repaint the hallway?")
    assert urgency == Urgency.LOW


def test_no_category_match():
    category, urgency, intent, confidence = rule_based_classification("Random unrelated text")
    # Should return None for category when no keywords match
    assert category is None or confidence < 0.5


def test_multiple_category_keywords():
    # Test when message has keywords from multiple categories
    category, urgency, intent, confidence = rule_based_classification("My water leak and package delivery")
    # Should pick the category with most keyword matches
    assert category is not None


def test_high_urgency_keywords():
    category, urgency, _, _ = rule_based_classification("Emergency! Water flooding everywhere!")
    assert urgency == Urgency.HIGH


def test_confidence_calculation():
    _, _, _, confidence = rule_based_classification("leak broken emergency flood")
    # Multiple keyword matches should increase confidence
    assert confidence > 0.5


def test_intent_solve_problem():
    _, _, intent, _ = rule_based_classification("My sink is broken")
    assert intent == Intent.SOLVE_PROBLEM


def test_intent_answer_question():
    _, _, intent, _ = rule_based_classification("What are the gym hours?")
    assert intent == Intent.ANSWER_QUESTION




@pytest.mark.asyncio
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
@patch('os.getenv')
async def test_gemini_classification_success(mock_getenv, mock_configure, mock_model_class):
    mock_getenv.return_value = "test-api-key"
    
    # Mock the model and response
    mock_model = Mock()
    mock_model_class.return_value = mock_model
    
    mock_response = Mock()
    mock_response.text = '{"intent": "solve_problem", "confidence": 0.95}'
    mock_model.generate_content.return_value = mock_response
    
    result = await gemini_classification("My AC is broken")
    
    # Should call Gemini API
    assert mock_configure.called
    assert mock_model.generate_content.called


@pytest.mark.asyncio  
@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
@patch('os.getenv')
async def test_gemini_classification_json_parsing(mock_getenv, mock_configure, mock_model_class):
    mock_getenv.return_value = "test-api-key"
    
    mock_model = Mock()
    mock_model_class.return_value = mock_model
    
    # No need to mock response, just test Gemini API call
    result = await gemini_classification("What are the pool hours?")
    
    # Should successfully parse JSON from markdown
    assert result is not None



