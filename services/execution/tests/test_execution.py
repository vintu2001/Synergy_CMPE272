"""
Tests for Execution Service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.execution_layer import (
    alert_on_call_manager,
    dispatch_maintenance,
    reroute_package,
    send_billing_notification
)
from app.models.schemas import DecisionResponse


@pytest.fixture
def sample_decision():
    return DecisionResponse(
        chosen_option_id="OPT1",
        chosen_action="Dispatch HVAC technician",
        estimated_cost=150.0,
        estimated_time=24,
        reasoning="AC issue requires professional repair",
        alternatives_considered=["Schedule routine maintenance", "Escalate to manager"]
    )


@pytest.fixture
def escalation_decision():
    return DecisionResponse(
        chosen_option_id="OPT_ESCALATE",
        chosen_action="Escalate to on-call manager",
        estimated_cost=0.0,
        estimated_time=2,
        escalation_reason="High risk situation",
        reasoning="Requires immediate management attention",
        alternatives_considered=[]
    )




@pytest.mark.asyncio
async def test_work_order_id_format():
    decision = DecisionResponse(
        chosen_option_id="OPT1",
        chosen_action="Fix leak",
        estimated_cost=100.0,
        estimated_time=12,
        reasoning="Urgent repair",
        alternatives_considered=[]
    )
    
    result = await dispatch_maintenance(decision)
    
    assert result["work_order_id"].startswith("WO_")
    assert len(result["work_order_id"]) > 10


@pytest.mark.asyncio
async def test_alert_id_format():
    decision = DecisionResponse(
        chosen_option_id="OPT_ESC",
        chosen_action="Escalate",
        estimated_cost=0.0,
        estimated_time=1,
        escalation_reason="High priority",
        reasoning="Manager needed",
        alternatives_considered=[]
    )
    
    result = await alert_on_call_manager(decision)
    
    assert result["alert_id"].startswith("ALERT_")
    assert len(result["alert_id"]) > 10



