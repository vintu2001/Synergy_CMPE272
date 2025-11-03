"""
Execution Layer - Ticket 14
Simulated API endpoints that mimic real-world systems.

TODO (Ticket 14):
- POST /alert-on-call-manager - Logs escalation message
- POST /dispatch-maintenance - Logs request and returns mock work order ID
- POST /reroute-package - Logs request and returns mock tracking number
- POST /send-billing-notification - Logs request and returns success message
"""
from fastapi import APIRouter
from app.models.schemas import DecisionResponse, IssueCategory
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/alert-on-call-manager")
async def alert_on_call_manager(decision: DecisionResponse):
    # TODO (Ticket 14): Log escalation via monitoring layer
    logger.info(f"ESCALATION ALERT: {decision.reasoning} at {datetime.now()}")
    
    return {
        "status": "escalated",
        "alert_id": f"ALERT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "message": "On-call manager has been notified"
    }


@router.post("/dispatch-maintenance")
async def dispatch_maintenance(decision: DecisionResponse):
    # TODO (Ticket 14): Log to maintenance subsystem
    work_order_id = f"WO_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Maintenance dispatched: {decision.chosen_action} - Work Order: {work_order_id}")
    
    return {
        "status": "dispatched",
        "work_order_id": work_order_id,
        "action": decision.chosen_action
    }


@router.post("/reroute-package")
async def reroute_package(decision: DecisionResponse):
    # TODO (Ticket 14): Log to courier subsystem
    tracking_number = f"TRACK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Package rerouted: {decision.chosen_action} - Tracking: {tracking_number}")
    
    return {
        "status": "rerouted",
        "tracking_number": tracking_number,
        "action": decision.chosen_action
    }


@router.post("/send-billing-notification")
async def send_billing_notification(decision: DecisionResponse):
    # TODO (Ticket 14): Log to billing subsystem
    notification_id = f"BILL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Billing notification sent: {decision.chosen_action} - ID: {notification_id}")
    
    return {
        "status": "sent",
        "notification_id": notification_id,
        "message": "Billing notification sent successfully"
    }

