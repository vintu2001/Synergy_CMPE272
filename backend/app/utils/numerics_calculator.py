"""
Numerics Calculator for Simulation Options

Calculates cost, ETA hours, and satisfaction scores for resolution options
based on category, urgency, and option characteristics.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Rate table for cost calculation ($ per hour)
HOURLY_RATES = {
    "High": 150.0,      # Emergency rate
    "Medium": 100.0,    # Standard rate
    "Low": 75.0         # Non-urgent rate
}

# SLA-based ETA hours by urgency
SLA_ETA_HOURS = {
    "High": {
        "min": 2.0,
        "max": 4.0,
        "default": 3.0
    },
    "Medium": {
        "min": 4.0,
        "max": 24.0,
        "default": 12.0
    },
    "Low": {
        "min": 24.0,
        "max": 48.0,
        "default": 36.0
    }
}

# Base satisfaction scores by urgency
BASE_SATISFACTION = {
    "High": 0.90,    # High urgency needs fast response
    "Medium": 0.80,  # Medium urgency has flexibility
    "Low": 0.75      # Low urgency is less critical
}


def calculate_cost(
    option_dict: Dict[str, Any],
    category: str,
    urgency: str
) -> float:
    """
    Calculate estimated cost for an option.
    
    Formula: cost = hourly_rate × estimated_hours
    
    If option already has estimated_cost > 0, returns that value.
    If option has estimated_hours or estimated_time, uses that.
    Otherwise, uses SLA default for urgency level.
    
    Args:
        option_dict: Option dictionary (may have estimated_cost, estimated_time, etc.)
        category: Issue category (Maintenance, Billing, etc.)
        urgency: Urgency level (High, Medium, Low)
        
    Returns:
        Estimated cost in dollars
    """
    # Return existing cost if already calculated
    existing_cost = option_dict.get('estimated_cost', 0)
    if existing_cost and existing_cost > 0:
        return float(existing_cost)
    
    # Get hourly rate for urgency
    rate = HOURLY_RATES.get(urgency, HOURLY_RATES["Medium"])
    
    # Get estimated hours from various possible fields
    hours = None
    if 'estimated_hours' in option_dict:
        hours = float(option_dict['estimated_hours'])
    elif 'estimated_time' in option_dict:
        hours = float(option_dict['estimated_time'])
    elif 'time_to_resolution' in option_dict:
        hours = float(option_dict['time_to_resolution'])
    
    # If no hours provided, use SLA default
    if hours is None:
        hours = SLA_ETA_HOURS.get(urgency, SLA_ETA_HOURS["Medium"])["default"]
    
    cost = rate * hours
    
    logger.debug(
        f"Calculated cost: ${cost:.2f} = ${rate}/hr × {hours}h "
        f"(category={category}, urgency={urgency})"
    )
    
    return cost


def calculate_eta_hours(
    option_dict: Dict[str, Any],
    category: str,
    urgency: str
) -> float:
    """
    Calculate ETA in hours for an option using SLA-based estimates.
    
    If option already has estimated_time/time_to_resolution, returns that.
    Otherwise, uses SLA default for urgency level.
    
    Args:
        option_dict: Option dictionary
        category: Issue category
        urgency: Urgency level (High, Medium, Low)
        
    Returns:
        Estimated time to resolution in hours
    """
    # Check if option already has time estimate
    if 'estimated_time' in option_dict and option_dict['estimated_time'] > 0:
        return float(option_dict['estimated_time'])
    
    if 'time_to_resolution' in option_dict and option_dict['time_to_resolution'] > 0:
        return float(option_dict['time_to_resolution'])
    
    if 'estimated_hours' in option_dict and option_dict['estimated_hours'] > 0:
        return float(option_dict['estimated_hours'])
    
    # Use SLA-based default for urgency
    sla_config = SLA_ETA_HOURS.get(urgency, SLA_ETA_HOURS["Medium"])
    eta = sla_config["default"]
    
    logger.debug(
        f"Calculated ETA: {eta}h (SLA default for {urgency} urgency, category={category})"
    )
    
    return eta


def calculate_satisfaction(
    option_dict: Dict[str, Any],
    urgency: str,
    cost: float
) -> float:
    """
    Calculate satisfaction score using simple heuristic.
    
    Formula:
    - Start with base satisfaction for urgency level
    - Fast response (low ETA) boosts satisfaction
    - Lower cost boosts satisfaction
    - High cost reduces satisfaction
    
    Args:
        option_dict: Option dictionary (may have estimated_time)
        urgency: Urgency level (High, Medium, Low)
        cost: Estimated cost in dollars
        
    Returns:
        Satisfaction score between 0.0 and 1.0
    """
    # Start with base satisfaction for urgency
    base = BASE_SATISFACTION.get(urgency, BASE_SATISFACTION["Medium"])
    
    # Get ETA from option
    eta = option_dict.get('estimated_time', option_dict.get('time_to_resolution', None))
    
    # Adjust for fast response (lower ETA = higher satisfaction)
    eta_adjustment = 0.0
    if eta is not None:
        sla_config = SLA_ETA_HOURS.get(urgency, SLA_ETA_HOURS["Medium"])
        # If ETA is below SLA min, boost satisfaction
        if eta < sla_config["min"]:
            eta_adjustment = 0.05
        # If ETA is at or above SLA max, reduce satisfaction
        elif eta >= sla_config["max"]:
            eta_adjustment = -0.05
    
    # Adjust for cost (lower cost = higher satisfaction)
    # Every $100 above $500 reduces satisfaction by 0.01
    cost_adjustment = 0.0
    if cost > 500:
        cost_adjustment = -((cost - 500) / 100) * 0.01
        cost_adjustment = max(cost_adjustment, -0.15)  # Cap reduction at -0.15
    elif cost < 300:
        # Lower cost boosts satisfaction
        cost_adjustment = 0.05
    
    # Calculate final satisfaction
    satisfaction = base + eta_adjustment + cost_adjustment
    
    # Clamp to [0.0, 1.0]
    satisfaction = max(0.0, min(1.0, satisfaction))
    
    logger.debug(
        f"Calculated satisfaction: {satisfaction:.3f} "
        f"(base={base:.3f}, eta_adj={eta_adjustment:+.3f}, cost_adj={cost_adjustment:+.3f}, "
        f"urgency={urgency}, cost=${cost:.2f})"
    )
    
    return satisfaction


def add_numerics_to_option(
    option_dict: Dict[str, Any],
    category: str,
    urgency: str
) -> Dict[str, Any]:
    """
    Convenience function to add all numerics to an option at once.
    
    Calculates and adds:
    - estimated_cost (if not present or zero)
    - estimated_time (if not present)
    - satisfaction_score (always calculated)
    
    Args:
        option_dict: Option dictionary to enhance
        category: Issue category
        urgency: Urgency level
        
    Returns:
        Enhanced option dictionary with numerics
    """
    # Calculate cost (uses existing if present)
    cost = calculate_cost(option_dict, category, urgency)
    option_dict['estimated_cost'] = cost
    
    # Calculate ETA (uses existing if present)
    eta = calculate_eta_hours(option_dict, category, urgency)
    option_dict['estimated_time'] = eta
    
    # Calculate satisfaction (always fresh calculation)
    satisfaction = calculate_satisfaction(option_dict, urgency, cost)
    option_dict['satisfaction_score'] = satisfaction
    
    return option_dict
