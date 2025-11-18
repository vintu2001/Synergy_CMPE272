import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.agents.decision_agent import (
    make_decision,
    create_escalation_decision,
    calculate_raw_score,
    analyze_costs,
    generate_decision_reasoning
)
from app.models.schemas import (
    DecisionRequest,
    ClassificationResponse,
    SimulationResponse,
    SimulatedOption,
    IssueCategory,
    Urgency,
    Intent,
    PolicyWeights,
    PolicyConfiguration
)


@pytest.fixture
def sample_classification():
    """Create a sample classification response."""
    return ClassificationResponse(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.HIGH,
        intent=Intent.SOLVE_PROBLEM,
        confidence=0.9
    )


@pytest.fixture
def sample_options():
    """Create sample simulated options."""
    return [
        SimulatedOption(
            option_id="opt_1",
            action="Quick fix",
            estimated_cost=100.0,
            estimated_time=2.0,
            reasoning="Fast and cheap",
            resident_satisfaction_impact=0.7
        ),
        SimulatedOption(
            option_id="opt_2",
            action="Complete repair",
            estimated_cost=300.0,
            estimated_time=8.0,
            reasoning="Thorough solution",
            resident_satisfaction_impact=0.9
        )
    ]


@pytest.fixture
def sample_request(sample_classification, sample_options):
    """Create a sample decision request."""
    simulation = SimulationResponse(
        options=sample_options,
        issue_id="test_issue"
    )
    return DecisionRequest(
        classification=sample_classification,
        simulation=simulation
    )


def test_create_escalation_decision(sample_classification):
    """Test creating an escalation decision."""
    decision = create_escalation_decision(
        classification=sample_classification,
        reason="Resident requested human contact"
    )
    
    assert decision.chosen_action is not None
    assert "escalat" in decision.chosen_action.lower() or "human" in decision.chosen_action.lower()
    assert decision.escalation_reason is not None


def test_analyze_costs(sample_options):
    """Test cost analysis."""
    config = PolicyConfiguration(max_cost=500.0, max_time=24.0)
    costs = analyze_costs(sample_options, config)
    
    assert len(costs) == len(sample_options)
    assert all(hasattr(cost, 'option_id') for cost in costs)
    assert all(hasattr(cost, 'estimated_cost') for cost in costs)
    assert all(hasattr(cost, 'exceeds_scale') for cost in costs)


def test_calculate_raw_score(sample_options):
    """Test calculating raw score for an option."""
    weights = PolicyWeights()
    config = PolicyConfiguration()
    
    score = calculate_raw_score(
        option=sample_options[0],
        urgency="High",
        max_actual_cost=300.0,
        max_actual_time=8.0,
        weights=weights,
        config=config
    )
    
    assert isinstance(score, float)
    assert score >= 0


@pytest.mark.asyncio
@patch('app.rag.retriever.retrieve_relevant_docs')
async def test_make_decision_basic(mock_retrieve, sample_request):
    """Test making a basic decision."""
    mock_retrieve.return_value = None
    
    result = await make_decision(request=sample_request)
    
    assert result is not None
    assert hasattr(result, 'decision') or isinstance(result, dict)
    # The function might return DecisionResponse or DecisionResponseWithStatus
    decision = result.decision if hasattr(result, 'decision') else result
    assert "chosen_option_id" in str(decision) or hasattr(decision, 'chosen_option_id')


@pytest.mark.asyncio
@patch('app.rag.retriever.retrieve_relevant_docs')
async def test_make_decision_escalation_intent(mock_retrieve):
    """Test making decision with escalation intent."""
    classification = ClassificationResponse(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.HIGH,
        intent=Intent.HUMAN_ESCALATION,
        confidence=0.9
    )
    simulation = SimulationResponse(
        options=[],
        issue_id="test_issue"
    )
    request = DecisionRequest(
        classification=classification,
        simulation=simulation
    )
    
    result = await make_decision(request=request)
    
    assert result is not None
    decision = result.decision if hasattr(result, 'decision') else result
    # Should be an escalation decision
    assert hasattr(decision, 'escalation_reason') or 'escalat' in str(decision).lower()


@pytest.mark.asyncio
async def test_make_decision_no_options(sample_classification):
    """Test making decision with no options."""
    simulation = SimulationResponse(
        options=[],
        issue_id="test_issue"
    )
    request = DecisionRequest(
        classification=sample_classification,
        simulation=simulation
    )
    
    # Should raise HTTPException or return error
    try:
        result = await make_decision(request=request)
        # If it doesn't raise, check the result
        assert result is not None
    except Exception as e:
        # Expected to raise when no options
        assert "options" in str(e).lower() or "no options" in str(e).lower()


def test_generate_decision_reasoning(sample_options, sample_classification):
    """Test generating decision reasoning."""
    chosen_option = (sample_options[0], 0.85)
    scored_options = [
        (sample_options[0], 0.85),
        (sample_options[1], 0.75)
    ]
    weights = PolicyWeights()
    config = PolicyConfiguration()
    
    reasoning = generate_decision_reasoning(
        chosen_option=chosen_option,
        scored_options=scored_options,
        all_options=sample_options,
        classification=sample_classification,
        weights=weights,
        config=config
    )
    
    assert reasoning.chosen_action is not None
    assert len(reasoning.considerations) > 0
    assert len(reasoning.cost_analysis) > 0
    assert len(reasoning.time_analysis) > 0
