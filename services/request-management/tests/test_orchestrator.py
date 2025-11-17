"""
Tests for Request Orchestrator
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from app.services.orchestrator import submit_request, select_option
from app.models.schemas import MessageRequest, SelectOptionRequest, IssueCategory, Urgency, Intent


@pytest.fixture
def mock_httpx_client():
    with patch('httpx.AsyncClient') as mock:
        yield mock


@pytest.fixture
def sample_message_request():
    return MessageRequest(
        resident_id="RES123",
        message_text="My AC is not working properly"
    )


@pytest.fixture
def sample_classification_response():
    return {
        "category": "Maintenance",
        "urgency": "High",
        "intent": "solve_problem",
        "confidence": 0.92
    }


@pytest.fixture
def sample_risk_response():
    return {
        "risk_score": 0.75,
        "recurrence_probability": 0.3
    }


@pytest.fixture
def sample_simulation_response():
    return {
        "options": [
            {
                "option_id": "OPT1",
                "action": "Dispatch HVAC technician",
                "estimated_cost": 150.0,
                "estimated_time": 24
            },
            {
                "option_id": "OPT2",
                "action": "Schedule maintenance",
                "estimated_cost": 200.0,
                "estimated_time": 48
            }
        ],
        "issue_id": "ISSUE123"
    }


@pytest.mark.asyncio
async def test_select_option_success():
    selection = SelectOptionRequest(
        request_id="REQ123",
        selected_option_id="OPT1"
    )
    
    mock_request = {
        "request_id": "REQ123",
        "simulated_options": [
            {"option_id": "OPT1", "action": "Dispatch technician", "estimated_cost": 150}
        ]
    }
    
    with patch('app.services.orchestrator.get_request_by_id', return_value=mock_request):
        with patch('app.services.orchestrator.get_table') as mock_table:
            mock_table.return_value.update_item = Mock()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_exec_response = AsyncMock()
                mock_exec_response.json.return_value = {"status": "success"}
                mock_exec_response.raise_for_status = Mock()
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_exec_response
                
                result = await select_option(selection)
                
                assert result["status"] == "success"
                assert result["request_id"] == "REQ123"


@pytest.mark.asyncio
async def test_select_option_invalid_option():
    selection = SelectOptionRequest(
        request_id="REQ123",
        selected_option_id="INVALID"
    )
    
    mock_request = {
        "request_id": "REQ123",
        "simulated_options": [
            {"option_id": "OPT1", "action": "Dispatch technician"}
        ]
    }
    
    with patch('app.services.orchestrator.get_request_by_id', return_value=mock_request):
        with pytest.raises(HTTPException) as exc_info:
            await select_option(selection)
        
        assert exc_info.value.status_code == 400
        assert "Invalid option ID" in str(exc_info.value.detail)



