import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
from app.agents.tools import AgentTools, agent_tools
from app.models.schemas import IssueCategory


@pytest.fixture
def tools():
    return AgentTools()


@pytest.mark.asyncio
async def test_execute_tools(tools):
    """Test executing all tools for a request."""
    result = await tools.execute_tools(
        resident_id="R001",
        category=IssueCategory.MAINTENANCE,
        urgency="High",
        message_text="AC is broken"
    )
    
    assert isinstance(result, dict)
    assert "availability" in result
    assert "pricing" in result
    assert "past_solutions" in result
    assert "recurring" in result
    assert "time_factors" in result
    assert "optimal_schedule" in result


def test_check_technician_availability(tools):
    """Test technician availability checking."""
    result = tools.check_technician_availability(
        category=IssueCategory.MAINTENANCE,
        urgency="High"
    )
    
    assert "available_techs" in result
    assert "estimated_wait_hours" in result
    assert "status" in result
    assert "next_available_slot" in result
    assert result["available_techs"] >= 0
    assert result["estimated_wait_hours"] > 0


def test_check_technician_availability_different_urgencies(tools):
    """Test availability with different urgency levels."""
    high_result = tools.check_technician_availability(
        category=IssueCategory.MAINTENANCE,
        urgency="High"
    )
    low_result = tools.check_technician_availability(
        category=IssueCategory.MAINTENANCE,
        urgency="Low"
    )
    
    # High urgency should generally have better availability
    assert high_result["available_techs"] >= 0
    assert low_result["available_techs"] >= 0


def test_check_technician_availability_different_categories(tools):
    """Test availability for different categories."""
    maintenance_result = tools.check_technician_availability(
        category=IssueCategory.MAINTENANCE,
        urgency="Medium"
    )
    security_result = tools.check_technician_availability(
        category=IssueCategory.SECURITY,
        urgency="Medium"
    )
    
    assert maintenance_result["available_techs"] >= 0
    assert security_result["available_techs"] >= 0


def test_estimate_repair_cost(tools):
    """Test repair cost estimation."""
    result = tools.estimate_repair_cost(
        category=IssueCategory.MAINTENANCE,
        urgency="High",
        message_text="Broken AC unit"
    )
    
    assert "estimated_cost_low" in result
    assert "estimated_cost_mid" in result
    assert "estimated_cost_high" in result
    assert "confidence" in result
    assert "factors" in result
    assert result["estimated_cost_low"] <= result["estimated_cost_mid"]
    assert result["estimated_cost_mid"] <= result["estimated_cost_high"]


def test_estimate_repair_cost_expensive_keywords(tools):
    """Test cost estimation with expensive keywords."""
    result = tools.estimate_repair_cost(
        category=IssueCategory.MAINTENANCE,
        urgency="Medium",
        message_text="Need to replace the entire HVAC system"
    )
    
    assert result["estimated_cost_mid"] > 0


def test_estimate_repair_cost_cheap_keywords(tools):
    """Test cost estimation with cheap keywords."""
    result = tools.estimate_repair_cost(
        category=IssueCategory.MAINTENANCE,
        urgency="Medium",
        message_text="Minor quick fix needed"
    )
    
    assert result["estimated_cost_mid"] > 0


def test_check_inventory(tools):
    """Test inventory checking."""
    result = tools.check_inventory("Need to replace the air filter")
    
    assert isinstance(result, dict)
    assert "parts_detected" in result


def test_check_inventory_with_parts(tools):
    """Test inventory checking with specific parts mentioned."""
    result = tools.check_inventory("The filter needs replacement")
    
    assert isinstance(result, dict)


def test_check_inventory_no_parts(tools):
    """Test inventory checking with no parts mentioned."""
    result = tools.check_inventory("Something is wrong")
    
    assert isinstance(result, dict)


def test_get_weather_conditions(tools):
    """Test weather condition retrieval."""
    result = tools.get_weather_conditions()
    
    assert "condition" in result
    assert "temperature_f" in result
    assert "affects_outdoor_work" in result
    assert "affects_hvac_priority" in result
    assert "recommendation" in result
    assert 50 <= result["temperature_f"] <= 95


def test_calculate_optimal_schedule(tools):
    """Test optimal schedule calculation."""
    availability_data = {
        "estimated_wait_hours": 4.0,
        "status": "Good"
    }
    
    result = tools.calculate_optimal_schedule(
        category=IssueCategory.MAINTENANCE,
        urgency="High",
        availability_data=availability_data
    )
    
    assert "priority_level" in result
    assert "recommended_schedule" in result
    assert "wait_hours" in result
    assert "schedule_status" in result
    assert "recommendation" in result


def test_calculate_optimal_schedule_different_urgencies(tools):
    """Test schedule calculation for different urgency levels."""
    availability_data = {"estimated_wait_hours": 4.0}
    
    high_result = tools.calculate_optimal_schedule(
        category=IssueCategory.MAINTENANCE,
        urgency="High",
        availability_data=availability_data
    )
    
    low_result = tools.calculate_optimal_schedule(
        category=IssueCategory.MAINTENANCE,
        urgency="Low",
        availability_data=availability_data
    )
    
    assert high_result["priority_level"] == "Emergency"
    assert low_result["priority_level"] == "Routine"


def test_get_time_of_day_factors(tools):
    """Test time of day factor calculation."""
    result = tools.get_time_of_day_factors()
    
    assert "current_hour" in result
    assert "is_business_hours" in result
    assert "is_after_hours" in result
    assert "is_weekend" in result
    assert "cost_multiplier" in result
    assert "availability_factor" in result
    assert 0 <= result["current_hour"] <= 23
    assert result["cost_multiplier"] >= 1.0




@pytest.mark.asyncio
@patch('app.agents.tools.httpx.AsyncClient')
async def test_query_past_solutions_http_error(mock_client_class, tools):
    """Test querying past solutions with HTTP error."""
    import httpx
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.HTTPError("Connection error")
    mock_client_class.return_value = mock_client
    
    result = await tools.query_past_solutions(
        resident_id="R001",
        category=IssueCategory.MAINTENANCE
    )
    
    assert result["found"] == False
    assert "error" in result




@pytest.mark.asyncio
@patch('app.agents.tools.httpx.AsyncClient')
async def test_check_recurring_issues_http_error(mock_client_class, tools):
    """Test checking recurring issues with HTTP error."""
    import httpx
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.HTTPError("Connection error")
    mock_client_class.return_value = mock_client
    
    result = await tools.check_recurring_issues(
        resident_id="R001",
        category=IssueCategory.MAINTENANCE,
        message_text="AC is broken"
    )
    
    assert result["is_recurring"] == False
    assert "error" in result

