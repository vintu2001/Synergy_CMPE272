"""
Execution Layer
Simulated API endpoints that mimic real-world systems for ticket resolution.
"""
from fastapi import APIRouter
from app.models.schemas import DecisionResponse, IssueCategory
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/alert-on-call-manager")
async def alert_on_call_manager(decision: DecisionResponse):
    logger.info(f"ESCALATION ALERT: {decision.reasoning} at {datetime.now()}")
    
    return {
        "status": "escalated",
        "alert_id": f"ALERT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "message": "On-call manager has been notified"
    }


@router.post("/dispatch-maintenance")
async def dispatch_maintenance(decision: DecisionResponse):
    work_order_id = f"WO_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Maintenance dispatched: {decision.chosen_action} - Work Order: {work_order_id}")
    
    return {
        "status": "dispatched",
        "work_order_id": work_order_id,
        "action": decision.chosen_action
    }


@router.post("/reroute-package")
async def reroute_package(decision: DecisionResponse):
    tracking_number = f"TRACK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Package rerouted: {decision.chosen_action} - Tracking: {tracking_number}")
    
    return {
        "status": "rerouted",
        "tracking_number": tracking_number,
        "action": decision.chosen_action
    }


@router.post("/send-billing-notification")
async def send_billing_notification(decision: DecisionResponse):
    notification_id = f"BILL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Billing notification sent: {decision.chosen_action} - ID: {notification_id}")
    
    return {
        "status": "sent",
        "notification_id": notification_id,
        "message": "Billing notification sent successfully"
    }

async def execute_decision(decision: DecisionResponse, category: IssueCategory) -> dict:
    """Execute a decision based on the issue category."""
    
    # Route the decision to the appropriate execution endpoint
    if decision.escalation_reason:
        return await alert_on_call_manager(decision)
        
    if category == IssueCategory.MAINTENANCE:
        return await dispatch_maintenance(decision)
    elif category == IssueCategory.DELIVERIES:
        return await reroute_package(decision)
    elif category == IssueCategory.BILLING:
        return await send_billing_notification(decision)
    else:
        # Default to maintenance for other categories
        return await dispatch_maintenance(decision)

