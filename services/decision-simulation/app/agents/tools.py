"""
Agent Tools for Real-Time Data Access (Level 2)
Provides agents with tools to gather contextual information.
"""
import random
import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from app.models.schemas import IssueCategory
import logging

logger = logging.getLogger(__name__)

REQUEST_MANAGEMENT_URL = os.getenv("REQUEST_MANAGEMENT_SERVICE_URL", "http://request-management:8001")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "test-admin-key")


class AgentTools:
    """Collection of tools that agents can use to gather real-time information."""
    
    def __init__(self):
        self.tools_registry = {
            'check_technician_availability': self.check_technician_availability,
            'estimate_repair_cost': self.estimate_repair_cost,
            'query_past_solutions': self.query_past_solutions,
            'check_inventory': self.check_inventory,
            'get_weather_conditions': self.get_weather_conditions,
            'calculate_optimal_schedule': self.calculate_optimal_schedule,
            'check_recurring_issues': self.check_recurring_issues,
            'get_time_of_day_factors': self.get_time_of_day_factors
        }
    
    async def execute_tools(
        self,
        resident_id: str,
        category: IssueCategory,
        urgency: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Execute all relevant tools and return aggregated data.
        This simulates an agent deciding which tools to use.
        """
        tools_data = {}
        
        try:
            # Always check availability and pricing
            tools_data['availability'] = self.check_technician_availability(category, urgency)
            tools_data['pricing'] = self.estimate_repair_cost(category, urgency, message_text)
            
            # Check past solutions for this resident
            tools_data['past_solutions'] = await self.query_past_solutions(resident_id, category)
            
            # Check for recurring issues
            tools_data['recurring'] = await self.check_recurring_issues(resident_id, category, message_text)
            
            # For maintenance, check inventory and weather
            if category == IssueCategory.MAINTENANCE:
                tools_data['inventory'] = self.check_inventory(message_text)
                tools_data['weather'] = self.get_weather_conditions()
            
            # Get time-of-day factors for scheduling
            tools_data['time_factors'] = self.get_time_of_day_factors()
            
            # Calculate optimal schedule
            tools_data['optimal_schedule'] = self.calculate_optimal_schedule(
                category, urgency, tools_data['availability']
            )
            
            logger.info(f"Executed {len(tools_data)} tools for resident {resident_id}")
            
        except Exception as e:
            logger.error(f"Error executing tools: {e}")
        
        return tools_data
    
    def check_technician_availability(
        self,
        category: IssueCategory,
        urgency: str
    ) -> Dict[str, Any]:
        """
        Check real-time technician availability using simulation algorithm.
        Uses time-of-day, urgency, and category factors to estimate availability.
        """
        # Calculate availability based on time of day
        hour = datetime.now().hour
        
        # More techs available during business hours (8am-6pm)
        if 8 <= hour < 18:
            base_available = random.randint(2, 5)
        elif 18 <= hour < 22:
            base_available = random.randint(1, 3)
        else:
            base_available = random.randint(0, 1)  # Limited overnight
        
        # High urgency increases availability (emergency staff)
        if urgency == "High":
            base_available += 1
        
        # Category-specific availability
        category_multipliers = {
            IssueCategory.MAINTENANCE: 1.0,
            IssueCategory.SECURITY: 1.2,
            IssueCategory.BILLING: 0.5,
            IssueCategory.DELIVERIES: 0.8,
            IssueCategory.AMENITIES: 0.7
        }
        
        available_count = int(base_available * category_multipliers.get(category, 1.0))
        
        # Estimate wait time
        if available_count >= 3:
            wait_time = random.uniform(0.5, 1.5)
            status = "Excellent"
        elif available_count == 2:
            wait_time = random.uniform(1.5, 3.0)
            status = "Good"
        elif available_count == 1:
            wait_time = random.uniform(3.0, 6.0)
            status = "Limited"
        else:
            wait_time = random.uniform(6.0, 12.0)
            status = "Very Limited"
        
        return {
            'available_techs': available_count,
            'estimated_wait_hours': round(wait_time, 1),
            'status': status,
            'next_available_slot': (datetime.now(timezone.utc) + timedelta(hours=wait_time)).isoformat()
        }
    
    def estimate_repair_cost(
        self,
        category: IssueCategory,
        urgency: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Estimate repair costs based on issue type, urgency, and message content.
        Uses category-based pricing, urgency multipliers, and keyword analysis.
        """
        # Base costs by category
        base_costs = {
            IssueCategory.MAINTENANCE: 150,
            IssueCategory.SECURITY: 200,
            IssueCategory.BILLING: 0,
            IssueCategory.DELIVERIES: 25,
            IssueCategory.AMENITIES: 100
        }
        
        base_cost = base_costs.get(category, 100)
        
        # Urgency multiplier
        urgency_multipliers = {
            "High": 1.5,
            "Medium": 1.0,
            "Low": 0.8
        }
        
        cost = base_cost * urgency_multipliers.get(urgency, 1.0)
        
        # Adjust based on keywords in message
        expensive_keywords = ['replace', 'emergency', 'broken', 'urgent', 'flooded']
        moderate_keywords = ['repair', 'fix', 'maintenance', 'check']
        cheap_keywords = ['minor', 'small', 'simple', 'quick']
        
        message_lower = message_text.lower()
        
        if any(kw in message_lower for kw in expensive_keywords):
            cost *= 1.3
        elif any(kw in message_lower for kw in cheap_keywords):
            cost *= 0.7
        
        # Add time-of-day premium
        hour = datetime.now().hour
        if hour < 6 or hour > 22:
            cost *= 1.4  # After-hours premium
        
        return {
            'estimated_cost_low': round(cost * 0.8, 2),
            'estimated_cost_mid': round(cost, 2),
            'estimated_cost_high': round(cost * 1.3, 2),
            'confidence': 0.75,
            'factors': {
                'base_category_cost': base_cost,
                'urgency_multiplier': urgency_multipliers.get(urgency, 1.0),
                'after_hours': hour < 6 or hour > 22
            }
        }
    
    async def query_past_solutions(
        self,
        resident_id: str,
        category: IssueCategory
    ) -> Dict[str, Any]:
        """
        Query past solutions for this resident and category.
        Calls Request Management service via HTTP to get resident's request history.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{REQUEST_MANAGEMENT_URL}/api/v1/get-requests/{resident_id}"
                )
                response.raise_for_status()
                past_requests = response.json()
            
            if not past_requests:
                return {
                    'found': False,
                    'count': 0,
                    'message': 'No past similar issues'
                }
            
            # Filter by category
            category_requests = [
                req for req in past_requests
                if req.get('category') == category.value
            ]
            
            if not category_requests:
                return {
                    'found': False,
                    'count': 0,
                    'message': f'No past {category.value} issues'
                }
            
            # Analyze past requests
            total_count = len(category_requests)
            resolved_count = sum(1 for req in category_requests if req.get('status') == 'Resolved')
            
            # Get most recent solution
            recent_request = category_requests[-1] if category_requests else None
            
            return {
                'found': True,
                'count': total_count,
                'resolved_count': resolved_count,
                'success_rate': resolved_count / total_count if total_count > 0 else 0,
                'most_recent': {
                    'date': recent_request.get('created_at') if recent_request else None,
                    'status': recent_request.get('status') if recent_request else None,
                    'action': recent_request.get('chosen_action') if recent_request else 'Unknown'
                },
                'recommendation': 'Consider permanent solution' if total_count >= 3 else 'Standard approach'
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying past solutions: {e}")
            return {'found': False, 'error': f'Service unavailable: {str(e)}'}
        except Exception as e:
            logger.error(f"Error querying past solutions: {e}")
            return {'found': False, 'error': str(e)}
    
    def check_inventory(self, message_text: str) -> Dict[str, Any]:
        """
        Check parts inventory availability using keyword-based detection.
        Analyzes message text to identify required parts and estimates availability.
        """
        # Common parts and their availability estimates
        parts_keywords = {
            'filter': {'available': random.choice([True, True, False]), 'stock': random.randint(0, 10)},
            'faucet': {'available': random.choice([True, True, False]), 'stock': random.randint(0, 8)},
            'light': {'available': random.choice([True, True, True]), 'stock': random.randint(5, 20)},
            'bulb': {'available': True, 'stock': random.randint(10, 50)},
            'thermostat': {'available': random.choice([True, False]), 'stock': random.randint(0, 5)},
            'lock': {'available': random.choice([True, True, False]), 'stock': random.randint(2, 8)},
            'pipe': {'available': True, 'stock': random.randint(5, 15)}
        }
        
        message_lower = message_text.lower()
        detected_parts = []
        
        for part, status in parts_keywords.items():
            if part in message_lower:
                detected_parts.append({
                    'part': part,
                    'available': status['available'],
                    'stock_count': status['stock']
                })
        
        if not detected_parts:
            return {
                'parts_detected': False,
                'message': 'No specific parts identified'
            }
        
        all_available = all(p['available'] for p in detected_parts)
        
        return {
            'parts_detected': True,
            'parts': detected_parts,
            'all_available': all_available,
            'estimated_delay': 0 if all_available else random.uniform(24, 72),
            'recommendation': 'Parts in stock' if all_available else 'May need to order parts'
        }
    
    def get_weather_conditions(self) -> Dict[str, Any]:
        """
        Get current weather conditions using simulation algorithm.
        Generates weather data relevant for outdoor repairs and HVAC priority assessment.
        """
        # Generate weather conditions
        conditions = ['Clear', 'Cloudy', 'Rainy', 'Stormy', 'Hot', 'Cold']
        current_condition = random.choice(conditions)
        
        temp = random.randint(50, 95)  # Fahrenheit
        
        affects_outdoor_work = current_condition in ['Rainy', 'Stormy']
        affects_hvac_priority = temp < 60 or temp > 85
        
        return {
            'condition': current_condition,
            'temperature_f': temp,
            'affects_outdoor_work': affects_outdoor_work,
            'affects_hvac_priority': affects_hvac_priority,
            'recommendation': 'Delay outdoor work' if affects_outdoor_work else 'Normal conditions'
        }
    
    def calculate_optimal_schedule(
        self,
        category: IssueCategory,
        urgency: str,
        availability_data: Dict
    ) -> Dict[str, Any]:
        """
        Calculate optimal scheduling based on availability and urgency.
        """
        wait_hours = availability_data.get('estimated_wait_hours', 4.0)
        
        # Urgency-based scheduling
        if urgency == "High":
            priority = "Emergency"
            max_acceptable_wait = 2.0
        elif urgency == "Medium":
            priority = "Standard"
            max_acceptable_wait = 8.0
        else:
            priority = "Routine"
            max_acceptable_wait = 24.0
        
        # Compare wait time vs acceptable
        schedule_status = "Immediate" if wait_hours <= max_acceptable_wait / 2 else \
                          "Acceptable" if wait_hours <= max_acceptable_wait else \
                          "Delayed"
        
        optimal_time = datetime.now(timezone.utc) + timedelta(hours=wait_hours)
        
        return {
            'priority_level': priority,
            'recommended_schedule': optimal_time.isoformat(),
            'wait_hours': wait_hours,
            'schedule_status': schedule_status,
            'recommendation': f"Schedule within {wait_hours:.1f} hours" if schedule_status != "Delayed" else "Consider emergency override"
        }
    
    async def check_recurring_issues(
        self,
        resident_id: str,
        category: IssueCategory,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Check if this is a recurring issue for the resident.
        Calls Request Management service via HTTP to get resident's request history.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{REQUEST_MANAGEMENT_URL}/api/v1/get-requests/{resident_id}"
                )
                response.raise_for_status()
                past_requests = response.json()
            
            # Filter by category and last 6 months
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
            recent_same_category = []
            
            for req in past_requests:
                if req.get('category') == category.value:
                    created_at_str = req.get('created_at')
                    if created_at_str:
                        try:
                            if isinstance(created_at_str, str):
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            else:
                                created_at = created_at_str
                            
                            if created_at >= six_months_ago:
                                recent_same_category.append(req)
                        except (ValueError, TypeError):
                            continue
            
            # Improved keyword matching for similar issues
            message_lower = message_text.lower()
            
            # Extract keywords - include important short words like "ac", "hvac", "heat", "cold", "leak", etc.
            important_short_words = {'ac', 'hvac', 'heat', 'cold', 'leak', 'hot', 'door', 'lock', 'key', 'wifi', 'gas', 'pipe'}
            words = message_lower.split()
            keywords = [
                word for word in words 
                if len(word) > 4 or word in important_short_words
            ]
            
            # Also check for recurring keywords in the message itself ("again", "still", "keep")
            recurring_keywords = {'again', 'still', 'keep', 'keeps', 'repeatedly', 'continue', 'continues', 'ongoing'}
            message_indicates_recurring = any(kw in message_lower for kw in recurring_keywords)
            
            similar_count = 0
            for req in recent_same_category:
                req_text = req.get('message_text', '').lower()
                matches = sum(1 for kw in keywords if kw in req_text)
                # If we have at least 2 matching keywords OR the messages are very similar, count it
                if matches >= 2 or (matches >= 1 and len(keywords) <= 3):
                    similar_count += 1
            
            # Mark as recurring if:
            # 1. We found 2+ similar past requests in same category, OR
            # 2. The message itself contains recurring keywords ("still", "again", etc.) AND there's at least 1 past request
            is_recurring = similar_count >= 2 or (message_indicates_recurring and similar_count >= 1)
            
            logger.info(
                f"Recurring check for {resident_id}: "
                f"keywords={keywords}, similar_count={similar_count}, "
                f"message_indicates_recurring={message_indicates_recurring}, "
                f"category_count={len(recent_same_category)}, is_recurring={is_recurring}"
            )
            
            return {
                'is_recurring': is_recurring,
                'occurrence_count': similar_count + 1,
                'category_count': len(recent_same_category),
                'time_window': '6 months',
                'keywords_matched': keywords,
                'message_has_recurring_keywords': message_indicates_recurring,
                'recommendation': 'Permanent solution needed' if is_recurring else 'Standard resolution'
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error checking recurring issues: {e}")
            return {'is_recurring': False, 'error': f'Service unavailable: {str(e)}'}
        except Exception as e:
            logger.error(f"Error checking recurring issues: {e}")
            return {'is_recurring': False, 'error': str(e)}
    
    def get_time_of_day_factors(self) -> Dict[str, Any]:
        """
        Get time-of-day factors affecting service.
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        is_business_hours = 8 <= hour < 18
        is_after_hours = hour < 6 or hour > 22
        is_weekend = now.weekday() >= 5
        
        cost_multiplier = 1.0
        if is_after_hours:
            cost_multiplier = 1.4
        elif not is_business_hours:
            cost_multiplier = 1.2
        
        if is_weekend:
            cost_multiplier *= 1.15
        
        return {
            'current_hour': hour,
            'is_business_hours': is_business_hours,
            'is_after_hours': is_after_hours,
            'is_weekend': is_weekend,
            'cost_multiplier': cost_multiplier,
            'availability_factor': 1.0 if is_business_hours else 0.6
        }


# Global instance
agent_tools = AgentTools()

