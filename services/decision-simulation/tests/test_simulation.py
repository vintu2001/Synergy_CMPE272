import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.agents.simulation_agent import AgenticResolutionSimulator, simulator
from app.models.schemas import IssueCategory, Urgency, SimulatedOption


@pytest.fixture
def mock_simulator():
    """Create a mock simulator instance."""
    with patch('app.agents.simulation_agent.llm_client') as mock_llm:
        with patch('app.agents.simulation_agent.agent_tools') as mock_tools:
            with patch('app.agents.simulation_agent.multi_step_reasoner') as mock_reasoner:
                with patch('app.agents.simulation_agent.learning_engine') as mock_learning:
                    simulator = AgenticResolutionSimulator()
                    simulator.llm_client = mock_llm
                    simulator.agent_tools = mock_tools
                    simulator.multi_step_reasoner = mock_reasoner
                    simulator.learning_engine = mock_learning
                    # Make learning_engine methods async
                    mock_learning.get_learning_insights_for_request = AsyncMock(return_value={
                        'has_insights': False
                    })
                    yield simulator


@pytest.mark.asyncio
async def test_generate_options_basic(mock_simulator):
    """Test basic option generation."""
    mock_simulator.llm_client.enabled = True
    mock_simulator.llm_client.generate_options = AsyncMock(return_value={
        "options": [
            {
                "option_id": "opt_1",
                "action": "Fix AC",
                "estimated_cost": 100.0,
                "time_to_resolution": 2.0,
                "resident_satisfaction_impact": 0.8,
                "reasoning": "Quick fix"
            }
        ]
    })
    mock_simulator.agent_tools.execute_tools = AsyncMock(return_value={})
    mock_simulator.multi_step_reasoner.analyze_complexity = AsyncMock(return_value={
        "is_complex": False
    })
    
    options = await mock_simulator.generate_options(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.HIGH,
        message_text="AC is broken",
        resident_id="R001",
        risk_score=0.5
    )
    
    assert len(options) > 0
    assert isinstance(options[0], SimulatedOption)


@pytest.mark.asyncio
async def test_generate_options_with_tools(mock_simulator):
    """Test option generation with tool data."""
    mock_simulator.llm_client.enabled = True
    mock_simulator.llm_client.generate_options = AsyncMock(return_value={
        "options": [
            {
                "option_id": "opt_1",
                "action": "Fix AC",
                "estimated_cost": 100.0,
                "time_to_resolution": 2.0,
                "resident_satisfaction_impact": 0.8,
                "reasoning": "Quick fix"
            }
        ]
    })
    mock_simulator.agent_tools.execute_tools = AsyncMock(return_value={
        "availability": {"available_techs": 2},
        "pricing": {"estimated_cost_mid": 100.0}
    })
    mock_simulator.multi_step_reasoner.analyze_complexity = AsyncMock(return_value={
        "is_complex": False
    })
    
    options = await mock_simulator.generate_options(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.HIGH,
        message_text="AC is broken",
        resident_id="R001",
        risk_score=0.5
    )
    
    assert len(options) > 0
    mock_simulator.agent_tools.execute_tools.assert_called_once()


@pytest.mark.asyncio
async def test_generate_options_complex_issue(mock_simulator):
    """Test option generation for complex issues."""
    mock_simulator.llm_client.enabled = True
    mock_simulator.llm_client.generate_options = AsyncMock(return_value={
        "options": []
    })
    mock_simulator.agent_tools.execute_tools = AsyncMock(return_value={})
    mock_simulator.multi_step_reasoner.analyze_complexity = AsyncMock(return_value={
        "is_complex": True,
        "complexity_score": 0.8
    })
    mock_simulator.multi_step_reasoner.generate_reasoning_chain = AsyncMock(return_value={
        "steps": [
            {
                "step_number": 1,
                "type": "diagnose",
                "action": "Assess",
                "estimated_time_hours": 2.0,
                "estimated_cost": 100.0,
                "risk_level": "low"
            }
        ],
        "total_estimated_time": 2.0,
        "total_estimated_cost": 100.0
    })
    # Fix: create_phased_options is async, so use AsyncMock
    mock_simulator.multi_step_reasoner.create_phased_options = AsyncMock(return_value=[
        {
            "option_id": "opt_phased_1",
            "action": "Phased approach",
            "estimated_cost": 100.0,
            "time_to_resolution": 2.0,
            "resident_satisfaction_impact": 0.8,
            "reasoning": "Multi-step"
        }
    ])
    
    options = await mock_simulator.generate_options(
        category=IssueCategory.MAINTENANCE,
        urgency=Urgency.HIGH,
        message_text="Complex multi-system issue",
        resident_id="R001",
        risk_score=0.7
    )
    
    assert len(options) > 0
    mock_simulator.multi_step_reasoner.generate_reasoning_chain.assert_called_once()
