import pytest
from unittest.mock import patch, AsyncMock
from app.services.execution_layer import (
    execute_decision,
    alert_on_call_manager,
    dispatch_maintenance,
    reroute_package,
    send_billing_notification
)
from app.models.schemas import DecisionResponse, IssueCategory


@pytest.fixture
def sample_decision():
    """Create a sample decision for testing."""
    return DecisionResponse(
        chosen_option_id="OPT1",
        chosen_action="Dispatch HVAC technician",
        reasoning="AC issue requires professional repair",
        alternatives_considered=["Schedule routine maintenance", "Escalate to manager"]
    )


@pytest.fixture
def escalation_decision():
    """Create an escalation decision for testing."""
    return DecisionResponse(
        chosen_option_id="OPT_ESCALATE",
        chosen_action="Escalate to on-call manager",
        escalation_reason="High risk situation",
        reasoning="Requires immediate management attention",
        alternatives_considered=[]
    )


@pytest.mark.asyncio
async def test_alert_on_call_manager(escalation_decision):
    """Test alerting on-call manager."""
    result = await alert_on_call_manager(escalation_decision)
    
    assert result["status"] == "escalated"
    assert "alert_id" in result
    assert result["alert_id"].startswith("ALERT_")
    assert "message" in result
    assert "On-call manager" in result["message"]


@pytest.mark.asyncio
async def test_alert_on_call_manager_logs(escalation_decision):
    """Test that alert_on_call_manager logs to CloudWatch."""
    with patch('app.services.execution_layer.log_to_cloudwatch') as mock_log:
        await alert_on_call_manager(escalation_decision)
        assert mock_log.called
        call_args = mock_log.call_args
        assert call_args[0][0] == 'escalation_executed'
        assert 'alert_id' in call_args[0][1]


@pytest.mark.asyncio
async def test_dispatch_maintenance(sample_decision):
    """Test dispatching maintenance."""
    result = await dispatch_maintenance(sample_decision)
    
    assert result["status"] == "dispatched"
    assert "work_order_id" in result
    assert result["work_order_id"].startswith("WO_")
    assert result["action"] == sample_decision.chosen_action


@pytest.mark.asyncio
async def test_dispatch_maintenance_logs(sample_decision):
    """Test that dispatch_maintenance logs to CloudWatch."""
    with patch('app.services.execution_layer.log_to_cloudwatch') as mock_log:
        await dispatch_maintenance(sample_decision)
        assert mock_log.called
        call_args = mock_log.call_args
        assert call_args[0][0] == 'maintenance_dispatched'
        assert 'work_order_id' in call_args[0][1]


@pytest.mark.asyncio
async def test_reroute_package(sample_decision):
    """Test rerouting package."""
    result = await reroute_package(sample_decision)
    
    assert result["status"] == "rerouted"
    assert "tracking_number" in result
    assert result["tracking_number"].startswith("TRACK_")
    assert result["action"] == sample_decision.chosen_action


@pytest.mark.asyncio
async def test_reroute_package_logs(sample_decision):
    """Test that reroute_package logs to CloudWatch."""
    with patch('app.services.execution_layer.log_to_cloudwatch') as mock_log:
        await reroute_package(sample_decision)
        assert mock_log.called
        call_args = mock_log.call_args
        assert call_args[0][0] == 'package_rerouted'
        assert 'tracking_number' in call_args[0][1]


@pytest.mark.asyncio
async def test_send_billing_notification(sample_decision):
    """Test sending billing notification."""
    result = await send_billing_notification(sample_decision)
    
    assert result["status"] == "sent"
    assert "notification_id" in result
    assert result["notification_id"].startswith("BILL_")
    assert "message" in result


@pytest.mark.asyncio
async def test_send_billing_notification_logs(sample_decision):
    """Test that send_billing_notification logs to CloudWatch."""
    with patch('app.services.execution_layer.log_to_cloudwatch') as mock_log:
        await send_billing_notification(sample_decision)
        assert mock_log.called
        call_args = mock_log.call_args
        assert call_args[0][0] == 'billing_notification_sent'
        assert 'notification_id' in call_args[0][1]


@pytest.mark.asyncio
async def test_execute_decision_escalation(escalation_decision):
    """Test execute_decision routes escalation correctly."""
    with patch('app.services.execution_layer.alert_on_call_manager') as mock_alert:
        mock_alert.return_value = {"status": "escalated", "alert_id": "ALERT_123"}
        
        result = await execute_decision(escalation_decision, IssueCategory.MAINTENANCE)
        
        assert result["status"] == "escalated"
        mock_alert.assert_called_once_with(escalation_decision)


@pytest.mark.asyncio
async def test_execute_decision_maintenance(sample_decision):
    """Test execute_decision routes maintenance correctly."""
    with patch('app.services.execution_layer.dispatch_maintenance') as mock_dispatch:
        mock_dispatch.return_value = {"status": "dispatched", "work_order_id": "WO_123"}
        
        result = await execute_decision(sample_decision, IssueCategory.MAINTENANCE)
        
        assert result["status"] == "dispatched"
        mock_dispatch.assert_called_once_with(sample_decision)


@pytest.mark.asyncio
async def test_execute_decision_deliveries(sample_decision):
    """Test execute_decision routes deliveries correctly."""
    with patch('app.services.execution_layer.reroute_package') as mock_reroute:
        mock_reroute.return_value = {"status": "rerouted", "tracking_number": "TRACK_123"}
        
        result = await execute_decision(sample_decision, IssueCategory.DELIVERIES)
        
        assert result["status"] == "rerouted"
        mock_reroute.assert_called_once_with(sample_decision)


@pytest.mark.asyncio
async def test_execute_decision_billing(sample_decision):
    """Test execute_decision routes billing correctly."""
    with patch('app.services.execution_layer.send_billing_notification') as mock_billing:
        mock_billing.return_value = {"status": "sent", "notification_id": "BILL_123"}
        
        result = await execute_decision(sample_decision, IssueCategory.BILLING)
        
        assert result["status"] == "sent"
        mock_billing.assert_called_once_with(sample_decision)


@pytest.mark.asyncio
async def test_execute_decision_security_defaults_to_maintenance(sample_decision):
    """Test execute_decision defaults to maintenance for security category."""
    with patch('app.services.execution_layer.dispatch_maintenance') as mock_dispatch:
        mock_dispatch.return_value = {"status": "dispatched", "work_order_id": "WO_123"}
        
        result = await execute_decision(sample_decision, IssueCategory.SECURITY)
        
        assert result["status"] == "dispatched"
        mock_dispatch.assert_called_once_with(sample_decision)


@pytest.mark.asyncio
async def test_execute_decision_amenities_defaults_to_maintenance(sample_decision):
    """Test execute_decision defaults to maintenance for amenities category."""
    with patch('app.services.execution_layer.dispatch_maintenance') as mock_dispatch:
        mock_dispatch.return_value = {"status": "dispatched", "work_order_id": "WO_123"}
        
        result = await execute_decision(sample_decision, IssueCategory.AMENITIES)
        
        assert result["status"] == "dispatched"
        mock_dispatch.assert_called_once_with(sample_decision)


@pytest.mark.asyncio
async def test_work_order_id_format(sample_decision):
    """Test work order ID format."""
    result = await dispatch_maintenance(sample_decision)
    
    assert result["work_order_id"].startswith("WO_")
    assert len(result["work_order_id"]) > 10
    # Should contain timestamp
    assert len(result["work_order_id"].split("_")) >= 2


@pytest.mark.asyncio
async def test_alert_id_format(escalation_decision):
    """Test alert ID format."""
    result = await alert_on_call_manager(escalation_decision)
    
    assert result["alert_id"].startswith("ALERT_")
    assert len(result["alert_id"]) > 10
    # Should contain timestamp
    assert len(result["alert_id"].split("_")) >= 2


@pytest.mark.asyncio
async def test_tracking_number_format(sample_decision):
    """Test tracking number format."""
    result = await reroute_package(sample_decision)
    
    assert result["tracking_number"].startswith("TRACK_")
    assert len(result["tracking_number"]) > 10


@pytest.mark.asyncio
async def test_notification_id_format(sample_decision):
    """Test notification ID format."""
    result = await send_billing_notification(sample_decision)
    
    assert result["notification_id"].startswith("BILL_")
    assert len(result["notification_id"]) > 10

