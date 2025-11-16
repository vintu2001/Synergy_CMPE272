"""
Learning & Adaptation Engine (Level 4)
Tracks outcomes, learns from feedback, and optimizes decision strategies.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from app.services.database import get_all_requests
from app.models.schemas import Status
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Tracks decision outcomes and learns from historical data.
    Provides insights for improving future decisions.
    """
    
    def __init__(self):
        self.learning_cache = {}  # In-memory cache for learning insights
    
    async def track_outcome(
        self,
        request_id: str,
        chosen_option_id: str,
        chosen_action: str,
        estimated_cost: float,
        estimated_time: float,
        estimated_satisfaction: float,
        actual_cost: Optional[float] = None,
        actual_time: Optional[float] = None,
        actual_satisfaction: Optional[float] = None,
        resident_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track the outcome of a decision for learning.
        
        Args:
            request_id: The request identifier
            chosen_option_id: Which option was selected
            chosen_action: The action that was taken
            estimated_*: Predicted values
            actual_*: Actual outcomes (if available)
            resident_feedback: Text feedback from resident
        
        Returns:
            Dict with accuracy metrics and insights
        """
        outcome = {
            'request_id': request_id,
            'chosen_option_id': chosen_option_id,
            'chosen_action': chosen_action,
            'estimated': {
                'cost': estimated_cost,
                'time': estimated_time,
                'satisfaction': estimated_satisfaction
            },
            'actual': {
                'cost': actual_cost,
                'time': actual_time,
                'satisfaction': actual_satisfaction
            },
            'resident_feedback': resident_feedback,
            'tracked_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Calculate accuracy if actuals are available
        accuracy = {}
        if actual_cost is not None and estimated_cost > 0:
            accuracy['cost_accuracy'] = 1.0 - abs(actual_cost - estimated_cost) / estimated_cost
        if actual_time is not None and estimated_time > 0:
            accuracy['time_accuracy'] = 1.0 - abs(actual_time - estimated_time) / estimated_time
        if actual_satisfaction is not None:
            accuracy['satisfaction_accuracy'] = 1.0 - abs(actual_satisfaction - estimated_satisfaction)
        
        outcome['accuracy'] = accuracy
        
        # Store in learning cache (in production, this would go to a database)
        self.learning_cache[request_id] = outcome
        
        logger.info(f"Tracked outcome for {request_id}: {accuracy}")
        return outcome
    
    async def analyze_historical_performance(
        self,
        category: Optional[str] = None,
        time_window_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze historical performance to identify patterns.
        
        Args:
            category: Filter by category (optional)
            time_window_days: How far back to analyze
        
        Returns:
            Dict with performance insights and recommendations
        """
        try:
            # Get all resolved requests from time window
            all_requests = get_all_requests()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
            
            # Filter resolved requests
            resolved_requests = [
                req for req in all_requests
                if req.status == Status.RESOLVED and
                   req.created_at >= cutoff_date
            ]
            
            if category:
                resolved_requests = [
                    req for req in resolved_requests
                    if req.category.value == category
                ]
            
            if not resolved_requests:
                return {
                    'total_requests': 0,
                    'message': 'No historical data available for analysis'
                }
            
            # Analyze patterns
            analysis = {
                'total_requests': len(resolved_requests),
                'time_window_days': time_window_days,
                'category_filter': category,
                'patterns': self._identify_patterns(resolved_requests),
                'cost_trends': self._analyze_cost_trends(resolved_requests),
                'time_trends': self._analyze_time_trends(resolved_requests),
                'success_factors': self._identify_success_factors(resolved_requests),
                'recommendations': []
            }
            
            # Generate recommendations based on analysis
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            logger.info(f"Analyzed {len(resolved_requests)} historical requests")
            return analysis
        
        except Exception as e:
            logger.error(f"Historical performance analysis failed: {e}")
            return {'error': str(e)}
    
    def _identify_patterns(self, requests: List[Any]) -> Dict[str, Any]:
        """Identify patterns in resolved requests."""
        patterns = {
            'most_common_categories': {},
            'most_common_urgencies': {},
            'avg_resolution_time': 0.0,
            'escalation_rate': 0.0
        }
        
        try:
            # Count categories
            for req in requests:
                cat = req.category.value if hasattr(req.category, 'value') else str(req.category)
                patterns['most_common_categories'][cat] = patterns['most_common_categories'].get(cat, 0) + 1
            
            # Count urgencies
            for req in requests:
                urg = req.urgency.value if hasattr(req.urgency, 'value') else str(req.urgency)
                patterns['most_common_urgencies'][urg] = patterns['most_common_urgencies'].get(urg, 0) + 1
            
            # Calculate escalation rate
            escalated = sum(1 for req in requests if hasattr(req, 'status') and str(req.status).lower() == 'escalated')
            patterns['escalation_rate'] = escalated / len(requests) if requests else 0.0
            
            # Sort by frequency
            patterns['most_common_categories'] = dict(
                sorted(patterns['most_common_categories'].items(), key=lambda x: x[1], reverse=True)
            )
            patterns['most_common_urgencies'] = dict(
                sorted(patterns['most_common_urgencies'].items(), key=lambda x: x[1], reverse=True)
            )
        
        except Exception as e:
            logger.error(f"Pattern identification failed: {e}")
        
        return patterns
    
    def _analyze_cost_trends(self, requests: List[Any]) -> Dict[str, Any]:
        """Analyze cost trends in resolved requests."""
        costs = []
        
        for req in requests:
            if hasattr(req, 'simulated_options') and req.simulated_options:
                for opt in req.simulated_options:
                    if isinstance(opt, dict) and 'estimated_cost' in opt:
                        cost = opt['estimated_cost']
                        if isinstance(cost, Decimal):
                            cost = float(cost)
                        costs.append(cost)
        
        if not costs:
            return {'avg_cost': 0.0, 'min_cost': 0.0, 'max_cost': 0.0}
        
        return {
            'avg_cost': sum(costs) / len(costs),
            'min_cost': min(costs),
            'max_cost': max(costs),
            'total_requests_with_cost': len(costs)
        }
    
    def _analyze_time_trends(self, requests: List[Any]) -> Dict[str, Any]:
        """Analyze time trends in resolved requests."""
        times = []
        
        for req in requests:
            if hasattr(req, 'simulated_options') and req.simulated_options:
                for opt in req.simulated_options:
                    if isinstance(opt, dict) and 'time_to_resolution' in opt:
                        time_val = opt['time_to_resolution']
                        if isinstance(time_val, Decimal):
                            time_val = float(time_val)
                        times.append(time_val)
        
        if not times:
            return {'avg_time_hours': 0.0, 'min_time': 0.0, 'max_time': 0.0}
        
        return {
            'avg_time_hours': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_requests_with_time': len(times)
        }
    
    def _identify_success_factors(self, requests: List[Any]) -> Dict[str, Any]:
        """Identify factors that correlate with successful resolution."""
        success_factors = {
            'high_satisfaction_actions': [],
            'quick_resolution_categories': [],
            'cost_effective_approaches': []
        }
        
        try:
            # Analyze which actions lead to high satisfaction
            # (In production, this would use actual satisfaction data)
            # For now, we use estimated satisfaction from options
            
            action_satisfaction = {}
            for req in requests:
                if hasattr(req, 'chosen_action') and req.chosen_action:
                    action = req.chosen_action
                    # Simulate satisfaction score (in production, use actual feedback)
                    if action not in action_satisfaction:
                        action_satisfaction[action] = []
                    action_satisfaction[action].append(0.85)  # Placeholder
            
            # Get top actions by satisfaction
            for action, scores in action_satisfaction.items():
                avg_score = sum(scores) / len(scores)
                if avg_score > 0.8:
                    success_factors['high_satisfaction_actions'].append({
                        'action': action,
                        'avg_satisfaction': avg_score,
                        'frequency': len(scores)
                    })
        
        except Exception as e:
            logger.error(f"Success factor identification failed: {e}")
        
        return success_factors
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        try:
            patterns = analysis.get('patterns', {})
            cost_trends = analysis.get('cost_trends', {})
            
            # Recommendation based on escalation rate
            if patterns.get('escalation_rate', 0) > 0.15:
                recommendations.append(
                    f"High escalation rate ({patterns['escalation_rate']:.1%}). "
                    "Consider improving initial classification accuracy or expanding tool capabilities."
                )
            
            # Recommendation based on cost trends
            avg_cost = cost_trends.get('avg_cost', 0)
            if avg_cost > 200:
                recommendations.append(
                    f"Average resolution cost is ${avg_cost:.2f}. "
                    "Consider prioritizing preventive maintenance to reduce costs."
                )
            
            # Recommendation based on common categories
            common_cats = patterns.get('most_common_categories', {})
            if common_cats:
                top_category = list(common_cats.keys())[0]
                count = common_cats[top_category]
                recommendations.append(
                    f"Most common category is '{top_category}' ({count} requests). "
                    f"Consider developing specialized workflows for {top_category} issues."
                )
        
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
        
        return recommendations
    
    async def get_learning_insights_for_request(
        self,
        category: str,
        urgency: str,
        message_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Get learning insights to inform current decision.
        
        Args:
            category: Issue category
            urgency: Urgency level
            message_keywords: Keywords from the message
        
        Returns:
            Dict with insights like cost_adjustment, time_adjustment, recommended_approach
        """
        try:
            # Get historical performance for this category
            analysis = await self.analyze_historical_performance(category=category, time_window_days=90)
            
            if analysis.get('total_requests', 0) == 0:
                return {
                    'has_insights': False,
                    'message': 'No historical data for this category'
                }
            
            insights = {
                'has_insights': True,
                'historical_avg_cost': analysis.get('cost_trends', {}).get('avg_cost', 0),
                'historical_avg_time': analysis.get('time_trends', {}).get('avg_time_hours', 0),
                'escalation_risk': analysis.get('patterns', {}).get('escalation_rate', 0),
                'recommendations': analysis.get('recommendations', []),
                'cost_adjustment_factor': 1.0,  # Multiplier for cost estimates
                'time_adjustment_factor': 1.0,  # Multiplier for time estimates
                'suggested_approach': 'standard'
            }
            
            # Adjust based on urgency and historical data
            if urgency == 'High' and insights['escalation_risk'] > 0.2:
                insights['suggested_approach'] = 'expedited'
                insights['cost_adjustment_factor'] = 1.2
                insights['time_adjustment_factor'] = 0.8
            
            return insights
        
        except Exception as e:
            logger.error(f"Failed to get learning insights: {e}")
            return {'has_insights': False, 'error': str(e)}


# Global instance
learning_engine = LearningEngine()

