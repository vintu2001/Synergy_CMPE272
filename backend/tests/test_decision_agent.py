"""
Test suite for Decision Agent (Ticket 13)
Tests core decision logic, policy-based scoring, and integration with other components.
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.asyncio  # Mark all test cases as async
from app.models.schemas import (
    ClassificationResponse, SimulationResponse, SimulatedOption,
    PolicyWeights, PolicyConfiguration, Intent, Urgency, IssueCategory,
    DecisionRequest, DecisionResponseWithStatus
)
from app.agents.decision_agent import (
    calculate_raw_score, analyze_costs, analyze_times,
    generate_decision_reasoning, make_decision
)

client = TestClient(app)

# Test Data
SAMPLE_CLASSIFICATION = ClassificationResponse(
    category=IssueCategory.MAINTENANCE,
    urgency=Urgency.HIGH,
    intent=Intent.SOLVE_PROBLEM,
    confidence=0.95,
    message_text="AC not working"
)

SAMPLE_OPTIONS = [
    SimulatedOption(
        option_id="opt1",
        action="Replace AC filter",
        estimated_cost=100.0,
        time_to_resolution=2.0,
        resident_satisfaction_impact=0.8
    ),
    SimulatedOption(
        option_id="opt2",
        action="Full AC maintenance",
        estimated_cost=500.0,
        time_to_resolution=8.0,
        resident_satisfaction_impact=0.9
    ),
    SimulatedOption(
        option_id="opt3",
        action="Replace AC unit",
        estimated_cost=2000.0,
        time_to_resolution=24.0,
        resident_satisfaction_impact=1.0
    )
]

SAMPLE_SIMULATION = SimulationResponse(
    options=SAMPLE_OPTIONS,
    issue_id="test_issue"
)

# Test Core Decision Logic
def test_calculate_raw_score():
    """Test raw score calculation with different weights and configurations."""
    option = SAMPLE_OPTIONS[0]
    max_cost = max(opt.estimated_cost for opt in SAMPLE_OPTIONS)
    max_time = max(opt.time_to_resolution for opt in SAMPLE_OPTIONS)
    
    # Test with default weights
    score = calculate_raw_score(
        option=option,
        urgency="High",
        max_actual_cost=max_cost,
        max_actual_time=max_time
    )
    assert 0 <= score <= 1, "Score should be between 0 and 1"
    
    # Test with custom weights prioritizing cost
    custom_weights = PolicyWeights(
        cost_weight=0.5,
        urgency_weight=0.2,
        time_weight=0.2,
        satisfaction_weight=0.1
    )
    score_cost_priority = calculate_raw_score(
        option=option,
        urgency="High",
        max_actual_cost=max_cost,
        max_actual_time=max_time,
        weights=custom_weights
    )
    assert 0 <= score_cost_priority <= 1, "Score should be between 0 and 1"

def test_analyze_costs():
    """Test cost analysis with different thresholds."""
    config = PolicyConfiguration(max_cost=1000.0)
    
    analysis = analyze_costs(SAMPLE_OPTIONS, config)
    assert len(analysis) == len(SAMPLE_OPTIONS)
    
    # Check scaling and threshold detection
    assert any(a.exceeds_scale for a in analysis), "Should detect options exceeding threshold"
    assert all(a.scaled_cost <= config.max_cost for a in analysis), "Scaled costs should not exceed max"

def test_analyze_times():
    """Test time analysis with different thresholds."""
    config = PolicyConfiguration(max_time=12.0)
    
    analysis = analyze_times(SAMPLE_OPTIONS, config)
    assert len(analysis) == len(SAMPLE_OPTIONS)
    
    # Check scaling and threshold detection
    assert any(a.exceeds_scale for a in analysis), "Should detect options exceeding threshold"
    assert all(a.scaled_time <= config.max_time for a in analysis), "Scaled times should not exceed max"

# Test Decision Pipeline
    @pytest.mark.asyncio
    async def test_make_decision_normal():
        """Test normal decision-making flow."""
        request = DecisionRequest(
            classification=SAMPLE_CLASSIFICATION,
            simulation=SAMPLE_SIMULATION
        )
        decision = await make_decision(request=request)
    
        assert isinstance(decision, DecisionResponseWithStatus)
        assert decision.chosen_action is not None
        assert decision.policy_scores is not None
        # Verify all options except the chosen one are listed in considerations
        alternative_options = [opt for opt in decision.alternatives_considered 
                             if opt.startswith('- ') and 'score:' in opt]
        assert len(alternative_options) == len(SAMPLE_OPTIONS) - 1
        assert decision.escalation_reason is None
        assert decision.processing_time > 0
        assert decision.request_id is not None
        assert decision.timestamp is not None
        assert decision.status == "success"@pytest.mark.asyncio
async def test_make_decision_escalation():
    """Test escalation path."""
    escalation_classification = ClassificationResponse(
        category=IssueCategory.SECURITY,
        urgency=Urgency.HIGH,
        intent=Intent.HUMAN_ESCALATION,
        confidence=0.95,
        message_text="Need to speak with manager"
    )
    
    request = DecisionRequest(
        classification=escalation_classification,
        simulation=SAMPLE_SIMULATION
    )
    decision = await make_decision(request=request)
    
    assert isinstance(decision, DecisionResponseWithStatus)
    assert decision.escalation_reason is not None
    assert "manager" in decision.chosen_action.lower()
    assert decision.processing_time > 0
    assert decision.request_id is not None
    assert decision.status == "success"

def test_generate_decision_reasoning():
    """Test decision reasoning generation."""
    option = SAMPLE_OPTIONS[0]
    score = 0.85
    
    reasoning = generate_decision_reasoning(
        chosen_option=(option, score),
        scored_options=[(opt, 0.5) for opt in SAMPLE_OPTIONS],
        all_options=SAMPLE_OPTIONS,
        classification=SAMPLE_CLASSIFICATION
    )
    
    assert reasoning.chosen_action == option.action
    assert len(reasoning.policy_scores) == len(SAMPLE_OPTIONS)
    assert reasoning.cost_analysis is not None
    assert reasoning.time_analysis is not None

# Test Error Handling
    @pytest.mark.asyncio
    async def test_make_decision_no_options():
        """Test handling of empty options list."""
        empty_simulation = SimulationResponse(options=[], issue_id="test_issue")
        request = DecisionRequest(
            classification=SAMPLE_CLASSIFICATION,
            simulation=empty_simulation
        )
    
        with pytest.raises(Exception) as exc_info:
            await make_decision(request=request)
        assert "No options provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_decision_invalid_weights():
        """Test handling of invalid policy weights."""
        with pytest.raises(ValueError) as exc_info:
            invalid_weights = PolicyWeights(
                urgency_weight=2.0,  # Invalid: > 1.0
                cost_weight=0.3,
                time_weight=0.2,
                satisfaction_weight=0.1
            )
        assert "Input should be less than or equal to 1" in str(exc_info.value)# Integration Tests
def test_decision_endpoint():
    """Test the decision endpoint through the API."""
    request_data = {
        "classification": {
            "category": "Maintenance",
            "urgency": "High",
            "intent": "solve_problem",
            "confidence": 0.95,
            "message_text": "AC not working"
        },
        "simulation": {
            "options": [{
                "option_id": "opt1",
                "action": "Replace filter",
                "estimated_cost": 100.0,
                "time_to_resolution": 2.0,
                "resident_satisfaction_impact": 0.8
            }],
            "issue_id": "test_issue"
        }
    }
    
    response = client.post("/api/v1/decide", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "chosen_action" in data
    assert "request_id" in data
    assert "processing_time" in data
    assert "status" in data
    assert data["status"] == "success"
    assert isinstance(data["processing_time"], (int, float))
    assert data["processing_time"] > 0

def test_decision_api_integration():
    """Test direct integration with decision API endpoint."""
    request_data = {
        "classification": {
            "category": "Maintenance",
            "urgency": "High",
            "intent": "solve_problem",
            "confidence": 0.95,
            "message_text": "AC not working"
        },
        "simulation": {
            "options": [{
                "option_id": "opt1",
                "action": "Replace filter",
                "estimated_cost": 100.0,
                "time_to_resolution": 2.0,
                "resident_satisfaction_impact": 0.8
            }],
            "issue_id": "test_issue"
        }
    }
    
    response = client.post("/api/v1/decide", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "chosen_action" in data
    assert "request_id" in data
    assert "processing_time" in data
    assert "status" in data
    assert data["status"] == "success"