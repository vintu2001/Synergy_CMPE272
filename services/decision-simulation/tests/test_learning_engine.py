import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from app.agents.learning_engine import LearningEngine, learning_engine


@pytest.fixture
def engine():
    """Create a learning engine instance."""
    return LearningEngine()


@pytest.mark.asyncio
async def test_track_outcome(engine):
    """Test tracking outcome of a decision."""
    outcome = await engine.track_outcome(
        request_id="req_001",
        chosen_option_id="opt_1",
        chosen_action="Fix AC",
        estimated_cost=100.0,
        estimated_time=2.0,
        estimated_satisfaction=0.8
    )
    
    assert outcome["request_id"] == "req_001"
    assert outcome["chosen_option_id"] == "opt_1"
    assert "estimated" in outcome
    assert "actual" in outcome
    assert "tracked_at" in outcome


@pytest.mark.asyncio
async def test_track_outcome_with_actuals(engine):
    """Test tracking outcome with actual values."""
    outcome = await engine.track_outcome(
        request_id="req_001",
        chosen_option_id="opt_1",
        chosen_action="Fix AC",
        estimated_cost=100.0,
        estimated_time=2.0,
        estimated_satisfaction=0.8,
        actual_cost=95.0,
        actual_time=1.8,
        actual_satisfaction=0.85,
        resident_feedback="Great service!"
    )
    
    assert "accuracy" in outcome
    assert "cost_accuracy" in outcome["accuracy"]
    assert "time_accuracy" in outcome["accuracy"]
    assert "satisfaction_accuracy" in outcome["accuracy"]




@pytest.mark.asyncio
@patch('app.agents.learning_engine.httpx.AsyncClient')
async def test_analyze_historical_performance_http_error(mock_client_class, engine):
    """Test analyzing historical performance with HTTP error."""
    import httpx
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.HTTPError("Connection error")
    mock_client_class.return_value = mock_client
    
    result = await engine.analyze_historical_performance()
    
    assert "error" in result
    assert result["total_requests"] == 0


def test_identify_patterns(engine):
    """Test identifying patterns in requests."""
    requests = [
        {
            "category": "Maintenance",
            "urgency": "High",
            "status": "Resolved"
        },
        {
            "category": "Maintenance",
            "urgency": "Medium",
            "status": "Resolved"
        },
        {
            "category": "Billing",
            "urgency": "Low",
            "status": "Escalated"
        }
    ]
    
    patterns = engine._identify_patterns(requests)
    
    assert "most_common_categories" in patterns
    assert "most_common_urgencies" in patterns
    assert "escalation_rate" in patterns
    assert patterns["most_common_categories"]["Maintenance"] == 2


def test_analyze_cost_trends(engine):
    """Test analyzing cost trends."""
    requests = [
        {
            "simulated_options": [
                {"estimated_cost": 100.0},
                {"estimated_cost": 150.0}
            ]
        },
        {
            "simulated_options": [
                {"estimated_cost": 200.0}
            ]
        }
    ]
    
    trends = engine._analyze_cost_trends(requests)
    
    assert "avg_cost" in trends
    assert "min_cost" in trends
    assert "max_cost" in trends
    assert trends["avg_cost"] > 0


def test_analyze_cost_trends_no_costs(engine):
    """Test analyzing cost trends with no cost data."""
    requests = [
        {"simulated_options": []}
    ]
    
    trends = engine._analyze_cost_trends(requests)
    
    assert trends["avg_cost"] == 0.0
    assert trends["total_requests_with_cost"] == 0


def test_analyze_time_trends(engine):
    """Test analyzing time trends."""
    requests = [
        {
            "simulated_options": [
                {"time_to_resolution": 2.0},
                {"estimated_time": 3.0}
            ]
        },
        {
            "simulated_options": [
                {"time_to_resolution": 4.0}
            ]
        }
    ]
    
    trends = engine._analyze_time_trends(requests)
    
    assert "avg_time_hours" in trends
    assert "min_time" in trends
    assert "max_time" in trends
    assert trends["avg_time_hours"] > 0


def test_analyze_time_trends_no_times(engine):
    """Test analyzing time trends with no time data."""
    requests = [
        {"simulated_options": []}
    ]
    
    trends = engine._analyze_time_trends(requests)
    
    assert trends["avg_time_hours"] == 0.0
    assert trends["total_requests_with_time"] == 0


def test_identify_success_factors(engine):
    """Test identifying success factors."""
    requests = [
        {"chosen_action": "Fix AC"},
        {"chosen_action": "Replace filter"},
        {"chosen_action": "Fix AC"}
    ]
    
    factors = engine._identify_success_factors(requests)
    
    assert "high_satisfaction_actions" in factors
    assert "quick_resolution_categories" in factors
    assert "cost_effective_approaches" in factors


def test_generate_recommendations(engine):
    """Test generating recommendations."""
    analysis = {
        "patterns": {
            "escalation_rate": 0.2,
            "most_common_categories": {"Maintenance": 10}
        },
        "cost_trends": {
            "avg_cost": 250.0
        }
    }
    
    recommendations = engine._generate_recommendations(analysis)
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0


def test_generate_recommendations_low_escalation(engine):
    """Test generating recommendations with low escalation rate."""
    analysis = {
        "patterns": {
            "escalation_rate": 0.05,
            "most_common_categories": {"Maintenance": 10}
        },
        "cost_trends": {
            "avg_cost": 100.0
        }
    }
    
    recommendations = engine._generate_recommendations(analysis)
    
    assert isinstance(recommendations, list)


@pytest.mark.asyncio
async def test_get_learning_insights_for_request(engine):
    """Test getting learning insights for a request."""
    with patch.object(engine, 'analyze_historical_performance') as mock_analyze:
        mock_analyze.return_value = {
            "total_requests": 10,
            "cost_trends": {"avg_cost": 150.0},
            "time_trends": {"avg_time_hours": 3.0},
            "patterns": {"escalation_rate": 0.1}
        }
        
        insights = await engine.get_learning_insights_for_request(
            category="Maintenance",
            urgency="High",
            message_keywords=["broken", "AC"]
        )
        
        assert "has_insights" in insights
        assert "historical_avg_cost" in insights
        assert "historical_avg_time" in insights
        assert "cost_adjustment_factor" in insights


@pytest.mark.asyncio
async def test_get_learning_insights_no_data(engine):
    """Test getting learning insights with no historical data."""
    with patch.object(engine, 'analyze_historical_performance') as mock_analyze:
        mock_analyze.return_value = {
            "total_requests": 0
        }
        
        insights = await engine.get_learning_insights_for_request(
            category="Maintenance",
            urgency="High",
            message_keywords=["broken"]
        )
        
        assert insights["has_insights"] == False


@pytest.mark.asyncio
async def test_get_learning_insights_error(engine):
    """Test getting learning insights with error."""
    with patch.object(engine, 'analyze_historical_performance') as mock_analyze:
        mock_analyze.side_effect = Exception("Error")
        
        insights = await engine.get_learning_insights_for_request(
            category="Maintenance",
            urgency="High",
            message_keywords=["broken"]
        )
        
        assert insights["has_insights"] == False
        assert "error" in insights

