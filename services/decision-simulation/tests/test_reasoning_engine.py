import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.reasoning_engine import MultiStepReasoner, multi_step_reasoner, ReasoningStep


@pytest.fixture
def reasoner():
    """Create a reasoning engine instance."""
    return MultiStepReasoner()


@pytest.mark.asyncio
async def test_analyze_complexity_disabled(reasoner):
    """Test complexity analysis when LLM is disabled."""
    with patch.object(reasoner.llm_client, 'enabled', False):
        result = await reasoner.analyze_complexity(
            message_text="Simple issue",
            category="Maintenance",
            urgency="Low",
            tools_data={}
        )
        
        assert result["is_complex"] == False
        assert result["complexity_score"] == 0.0


@pytest.mark.asyncio
async def test_analyze_complexity_simple(reasoner):
    """Test complexity analysis for simple issues."""
    mock_response = MagicMock()
    mock_response.text = '{"is_complex": false, "complexity_score": 0.3, "reasoning_required": "single_step", "complexity_factors": [], "recommended_steps": 1}'
    
    with patch.object(reasoner.llm_client, 'enabled', True):
        with patch.object(reasoner.llm_client, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            result = await reasoner.analyze_complexity(
                message_text="Dripping faucet",
                category="Maintenance",
                urgency="Low",
                tools_data={}
            )
            
            assert "is_complex" in result
            assert "complexity_score" in result
            assert "reasoning_required" in result


@pytest.mark.asyncio
async def test_analyze_complexity_complex(reasoner):
    """Test complexity analysis for complex issues."""
    mock_response = MagicMock()
    mock_response.text = '{"is_complex": true, "complexity_score": 0.8, "reasoning_required": "multi_step", "complexity_factors": ["multiple systems"], "recommended_steps": 3}'
    
    with patch.object(reasoner.llm_client, 'enabled', True):
        with patch.object(reasoner.llm_client, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            result = await reasoner.analyze_complexity(
                message_text="Water leak affecting electrical system",
                category="Maintenance",
                urgency="High",
                tools_data={}
            )
            
            assert result["is_complex"] == True
            assert result["complexity_score"] > 0.7


@pytest.mark.asyncio
async def test_analyze_complexity_error(reasoner):
    """Test complexity analysis error handling."""
    with patch.object(reasoner.llm_client, 'enabled', True):
        with patch.object(reasoner.llm_client, 'model') as mock_model:
            mock_model.generate_content.side_effect = Exception("API error")
            
            result = await reasoner.analyze_complexity(
                message_text="Test",
                category="Maintenance",
                urgency="High",
                tools_data={}
            )
            
            assert result["is_complex"] == False
            assert result["reasoning_required"] == "single_step"


@pytest.mark.asyncio
async def test_generate_reasoning_chain_not_complex(reasoner):
    """Test reasoning chain generation for non-complex issues."""
    complexity_analysis = {"is_complex": False}
    
    result = await reasoner.generate_reasoning_chain(
        message_text="Simple issue",
        category="Maintenance",
        urgency="Low",
        risk_score=0.3,
        tools_data={},
        complexity_analysis=complexity_analysis
    )
    
    assert result["reasoning_type"] == "single_step"
    assert len(result["steps"]) == 0


@pytest.mark.asyncio
async def test_generate_reasoning_chain_complex(reasoner):
    """Test reasoning chain generation for complex issues."""
    complexity_analysis = {
        "is_complex": True,
        "complexity_score": 0.8,
        "recommended_steps": 3
    }
    
    mock_response = MagicMock()
    mock_response.text = """{
        "steps": [
            {"step_number": 1, "type": "diagnose", "action": "Assess damage", "estimated_time_hours": 2, "estimated_cost": 100, "risk_level": "low"},
            {"step_number": 2, "type": "execute", "action": "Repair issue", "estimated_time_hours": 4, "estimated_cost": 200, "risk_level": "medium"},
            {"step_number": 3, "type": "verify", "action": "Test solution", "estimated_time_hours": 1, "estimated_cost": 50, "risk_level": "low"}
        ],
        "total_estimated_time": 7,
        "total_estimated_cost": 350,
        "success_probability": 0.9
    }"""
    
    with patch.object(reasoner.llm_client, 'enabled', True):
        with patch.object(reasoner.llm_client, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            result = await reasoner.generate_reasoning_chain(
                message_text="Complex multi-system issue",
                category="Maintenance",
                urgency="High",
                risk_score=0.7,
                tools_data={},
                complexity_analysis=complexity_analysis
            )
            
            assert "steps" in result
            assert len(result["steps"]) == 3


@pytest.mark.asyncio
async def test_generate_reasoning_chain_error(reasoner):
    """Test reasoning chain generation error handling."""
    complexity_analysis = {"is_complex": True}
    
    with patch.object(reasoner.llm_client, 'enabled', True):
        with patch.object(reasoner.llm_client, 'model') as mock_model:
            mock_model.generate_content.side_effect = Exception("API error")
            
            result = await reasoner.generate_reasoning_chain(
                message_text="Test",
                category="Maintenance",
                urgency="High",
                risk_score=0.5,
                tools_data={},
                complexity_analysis=complexity_analysis
            )
            
            assert "error" in result
            assert len(result["steps"]) == 0


@pytest.mark.asyncio
async def test_create_phased_options_empty(reasoner):
    """Test creating phased options from empty reasoning chain."""
    reasoning_chain = {"steps": []}
    
    result = await reasoner.create_phased_options(
        reasoning_chain=reasoning_chain,
        category="Maintenance",
        urgency="High"
    )
    
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_phased_options_success(reasoner):
    """Test creating phased options successfully."""
    reasoning_chain = {
        "steps": [
            {
                "step_number": 1,
                "type": "diagnose",
                "action": "Assess the problem",
                "estimated_time_hours": 2.0,
                "estimated_cost": 100.0,
                "risk_level": "low"
            },
            {
                "step_number": 2,
                "type": "execute",
                "action": "Fix the issue",
                "estimated_time_hours": 4.0,
                "estimated_cost": 200.0,
                "risk_level": "medium"
            },
            {
                "step_number": 3,
                "type": "verify",
                "action": "Test the solution",
                "estimated_time_hours": 1.0,
                "estimated_cost": 50.0,
                "risk_level": "low"
            }
        ],
        "total_estimated_time": 7.0,
        "total_estimated_cost": 350.0
    }
    
    result = await reasoner.create_phased_options(
        reasoning_chain=reasoning_chain,
        category="Maintenance",
        urgency="High"
    )
    
    assert len(result) == 3
    assert result[0]["option_id"] == "opt_phased_complete"
    assert result[1]["option_id"] == "opt_phased_expedited"
    assert result[2]["option_id"] == "opt_phased_emergency"
    assert "action" in result[0]
    assert "estimated_cost" in result[0]
    assert "time_to_resolution" in result[0]


def test_format_phased_action(reasoner):
    """Test formatting phased action descriptions."""
    steps = [
        {"action": "Step 1", "type": "diagnose"},
        {"action": "Step 2", "type": "execute"}
    ]
    
    result = reasoner._format_phased_action(steps, "complete")
    assert isinstance(result, str)
    assert "coordinated steps" in result or "professional" in result


def test_format_phased_action_empty(reasoner):
    """Test formatting phased action with empty steps."""
    result = reasoner._format_phased_action([], "complete")
    assert isinstance(result, str)


def test_format_detailed_phases(reasoner):
    """Test formatting detailed phases for UI."""
    steps = [
        {
            "type": "diagnose",
            "action": "Assess the problem",
            "estimated_time_hours": 2.0,
            "estimated_cost": 100.0,
            "risk_level": "low"
        },
        {
            "type": "execute",
            "action": "Fix the issue",
            "estimated_time_hours": 4.0,
            "estimated_cost": 200.0,
            "risk_level": "medium"
        }
    ]
    
    result = reasoner._format_detailed_phases(steps)
    
    assert len(result) == 2
    assert result[0]["step"] == 1
    assert result[1]["step"] == 2
    assert "title" in result[0]
    assert "description" in result[0]
    assert "time" in result[0]
    assert "cost" in result[0]


def test_format_detailed_phases_empty(reasoner):
    """Test formatting detailed phases with empty steps."""
    result = reasoner._format_detailed_phases([])
    assert len(result) == 0

