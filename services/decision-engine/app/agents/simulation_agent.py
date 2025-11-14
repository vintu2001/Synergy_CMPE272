"""
Simulation Agent
Generates multiple resolution options and simulates their outcomes using SimPy.
"""
from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os
sys.path.insert(0, '/app/libs')
from shared_models import ClassificationResponse, SimulationResponse, SimulatedOption, IssueCategory, Urgency
import simpy
import random
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class SimulationRequest(BaseModel):
    """Request model for simulation endpoint"""
    classification: ClassificationResponse
    risk_score: float = 0.5


class ResolutionSimulator:
    """Simulates resolution options using SimPy discrete-event simulation."""
    
    def __init__(self):
        self.option_templates = self._load_option_templates()
    
    def _load_option_templates(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load resolution option templates for each category and urgency level."""
        return {
            "Maintenance": {
                "High": [
                    {
                        "action": "Dispatch Emergency Technician Immediately",
                        "base_cost": 400,
                        "base_time": 1.5,
                        "base_satisfaction": 0.95,
                        "resource_type": "emergency_tech"
                    },
                    {
                        "action": "Schedule Urgent Repair (within 4 hours)",
                        "base_cost": 250,
                        "base_time": 4.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "urgent_tech"
                    },
                    {
                        "action": "Send Maintenance Staff for Temporary Fix",
                        "base_cost": 100,
                        "base_time": 2.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "maintenance_staff"
                    }
                ],
                "Medium": [
                    {
                        "action": "Schedule Standard Repair (next business day)",
                        "base_cost": 180,
                        "base_time": 24.0,
                        "base_satisfaction": 0.75,
                        "resource_type": "standard_tech"
                    },
                    {
                        "action": "Add to Next Available Slot",
                        "base_cost": 150,
                        "base_time": 48.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "standard_tech"
                    },
                    {
                        "action": "Provide DIY Instructions and Monitor",
                        "base_cost": 10,
                        "base_time": 1.0,
                        "base_satisfaction": 0.45,
                        "resource_type": "support_staff"
                    }
                ],
                "Low": [
                    {
                        "action": "Schedule Routine Maintenance Visit",
                        "base_cost": 120,
                        "base_time": 72.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "standard_tech"
                    },
                    {
                        "action": "Send DIY Video Tutorial",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.50,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Add to Monthly Inspection List",
                        "base_cost": 20,
                        "base_time": 168.0,
                        "base_satisfaction": 0.40,
                        "resource_type": "routine"
                    }
                ]
            },
            "Security": {
                "High": [
                    {
                        "action": "Dispatch Security Team Immediately",
                        "base_cost": 300,
                        "base_time": 0.5,
                        "base_satisfaction": 0.95,
                        "resource_type": "security_team"
                    },
                    {
                        "action": "Alert On-Site Security and Monitor",
                        "base_cost": 100,
                        "base_time": 1.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "on_site_security"
                    },
                    {
                        "action": "Initiate Lockdown Protocol",
                        "base_cost": 500,
                        "base_time": 0.25,
                        "base_satisfaction": 0.90,
                        "resource_type": "emergency_protocol"
                    }
                ],
                "Medium": [
                    {
                        "action": "Schedule Security Assessment",
                        "base_cost": 150,
                        "base_time": 8.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "security_team"
                    },
                    {
                        "action": "Increase Patrol Frequency",
                        "base_cost": 80,
                        "base_time": 4.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "on_site_security"
                    },
                    {
                        "action": "Send Security Reminder Email",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.45,
                        "resource_type": "automated"
                    }
                ],
                "Low": [
                    {
                        "action": "Add to Next Security Walkthrough",
                        "base_cost": 50,
                        "base_time": 48.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "routine"
                    },
                    {
                        "action": "Send Security Best Practices Guide",
                        "base_cost": 5,
                        "base_time": 0.25,
                        "base_satisfaction": 0.50,
                        "resource_type": "automated"
                    }
                ]
            },
            "Billing": {
                "High": [
                    {
                        "action": "Immediate Manager Review and Adjustment",
                        "base_cost": 50,
                        "base_time": 2.0,
                        "base_satisfaction": 0.90,
                        "resource_type": "manager"
                    },
                    {
                        "action": "Expedited Billing Audit",
                        "base_cost": 30,
                        "base_time": 4.0,
                        "base_satisfaction": 0.80,
                        "resource_type": "billing_specialist"
                    },
                    {
                        "action": "Apply Credit and Investigate",
                        "base_cost": 20,
                        "base_time": 1.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "billing_staff"
                    }
                ],
                "Medium": [
                    {
                        "action": "Standard Billing Review",
                        "base_cost": 25,
                        "base_time": 24.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "billing_staff"
                    },
                    {
                        "action": "Automated System Check",
                        "base_cost": 5,
                        "base_time": 1.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Schedule Payment Plan Consultation",
                        "base_cost": 15,
                        "base_time": 48.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "billing_staff"
                    }
                ],
                "Low": [
                    {
                        "action": "Send Billing Explanation Email",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.55,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Add to Next Billing Cycle Review",
                        "base_cost": 10,
                        "base_time": 168.0,
                        "base_satisfaction": 0.50,
                        "resource_type": "routine"
                    }
                ]
            },
            "Deliveries": {
                "High": [
                    {
                        "action": "Immediate Package Location and Delivery",
                        "base_cost": 50,
                        "base_time": 1.0,
                        "base_satisfaction": 0.90,
                        "resource_type": "concierge"
                    },
                    {
                        "action": "Alert Concierge to Prioritize Search",
                        "base_cost": 20,
                        "base_time": 2.0,
                        "base_satisfaction": 0.75,
                        "resource_type": "concierge"
                    }
                ],
                "Medium": [
                    {
                        "action": "Check Package Room and Notify",
                        "base_cost": 15,
                        "base_time": 4.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "concierge"
                    },
                    {
                        "action": "Contact Carrier for Update",
                        "base_cost": 10,
                        "base_time": 8.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "support_staff"
                    },
                    {
                        "action": "Send Delivery Tracking Information",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.55,
                        "resource_type": "automated"
                    }
                ],
                "Low": [
                    {
                        "action": "Add to Next Concierge Rounds",
                        "base_cost": 10,
                        "base_time": 24.0,
                        "base_satisfaction": 0.50,
                        "resource_type": "routine"
                    },
                    {
                        "action": "Send Package Pickup Instructions",
                        "base_cost": 5,
                        "base_time": 0.25,
                        "base_satisfaction": 0.45,
                        "resource_type": "automated"
                    }
                ]
            },
            "Amenities": {
                "High": [
                    {
                        "action": "Immediate Staff Response and Resolution",
                        "base_cost": 80,
                        "base_time": 1.0,
                        "base_satisfaction": 0.85,
                        "resource_type": "amenities_staff"
                    },
                    {
                        "action": "Temporary Closure and Alternative Arrangement",
                        "base_cost": 50,
                        "base_time": 2.0,
                        "base_satisfaction": 0.70,
                        "resource_type": "amenities_staff"
                    }
                ],
                "Medium": [
                    {
                        "action": "Schedule Amenity Maintenance Check",
                        "base_cost": 40,
                        "base_time": 12.0,
                        "base_satisfaction": 0.65,
                        "resource_type": "amenities_staff"
                    },
                    {
                        "action": "Update Amenity Schedule and Notify Residents",
                        "base_cost": 10,
                        "base_time": 1.0,
                        "base_satisfaction": 0.60,
                        "resource_type": "support_staff"
                    }
                ],
                "Low": [
                    {
                        "action": "Send Amenity Hours and Rules Guide",
                        "base_cost": 5,
                        "base_time": 0.25,
                        "base_satisfaction": 0.60,
                        "resource_type": "automated"
                    },
                    {
                        "action": "Add to Community Newsletter",
                        "base_cost": 5,
                        "base_time": 72.0,
                        "base_satisfaction": 0.45,
                        "resource_type": "routine"
                    },
                    {
                        "action": "Post Information on Resident Portal",
                        "base_cost": 5,
                        "base_time": 0.5,
                        "base_satisfaction": 0.55,
                        "resource_type": "automated"
                    }
                ]
            }
        }
    
    def simulate_resolution_process(self, template: Dict[str, Any], risk_score: float) -> Dict[str, float]:
        """
        Simulate a resolution option using SimPy.
        Adjusts parameters based on risk score.
        """
        env = simpy.Environment()
        
        results = {
            'cost': template['base_cost'],
            'time': template['base_time'],
            'satisfaction': template['base_satisfaction']
        }
        
        def resolution_process(env):
            travel_time = random.uniform(0.1, 0.5) if template['resource_type'] != 'automated' else 0
            yield env.timeout(travel_time)
            
            work_time = template['base_time'] * random.uniform(0.8, 1.2)
            yield env.timeout(work_time)
            
            results['time'] = travel_time + work_time
        
        env.process(resolution_process(env))
        env.run()
        
        # Adjust based on risk score
        if risk_score > 0.7:
            results['cost'] *= 1.2
            results['time'] *= 0.9
            results['satisfaction'] = min(results['satisfaction'] * 1.05, 1.0)
        elif risk_score < 0.4:
            results['cost'] *= 0.85
            results['time'] *= 1.1
            results['satisfaction'] *= 0.95
        
        # Add slight randomness
        results['cost'] *= random.uniform(0.95, 1.05)
        results['time'] *= random.uniform(0.9, 1.1)
        results['satisfaction'] = min(max(results['satisfaction'] * random.uniform(0.95, 1.02), 0.0), 1.0)
        
        return results
    
    def generate_options(
        self, 
        category: IssueCategory, 
        urgency: Urgency,
        risk_score: float = 0.5
    ) -> List[SimulatedOption]:
        """Generate resolution options based on category, urgency, and risk score."""
        
        category_key = category.value
        urgency_key = urgency.value
        
        templates = self.option_templates.get(category_key, {}).get(urgency_key, [])
        
        if not templates:
            templates = self.option_templates.get("Maintenance", {}).get("Medium", [])
        
        options = []
        for idx, template in enumerate(templates, 1):
            simulated = self.simulate_resolution_process(template, risk_score)
            
            option = SimulatedOption(
                option_id=f"opt_{category_key.lower()}_{urgency_key.lower()}_{idx}",
                action=template['action'],
                estimated_cost=round(simulated['cost'], 2),
                time_to_resolution=round(simulated['time'], 2),
                resident_satisfaction_impact=round(simulated['satisfaction'], 2)
            )
            options.append(option)
        
        return options


simulator = ResolutionSimulator()


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_resolutions(request: SimulationRequest) -> SimulationResponse:
    """
    Generate multiple resolution options using SimPy simulation.
    
    Args:
        request: SimulationRequest containing classification and risk_score
    
    Returns:
        SimulationResponse with 3+ simulated resolution options
    """
    try:
        options = simulator.generate_options(
            category=request.classification.category,
            urgency=request.classification.urgency,
            risk_score=request.risk_score
        )
        
        logger.info(f"Generated {len(options)} options for {request.classification.category.value}/{request.classification.urgency.value} (risk: {request.risk_score:.2f})")
        
        return SimulationResponse(
            options=options,
            issue_id=f"sim_{request.classification.category.value}_{request.classification.urgency.value}"
        )
    
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        fallback_options = [
            SimulatedOption(
                option_id="fallback_1",
                action="Standard Resolution Process",
                estimated_cost=100.00,
                time_to_resolution=24.0,
                resident_satisfaction_impact=0.70
            ),
            SimulatedOption(
                option_id="fallback_2",
                action="Expedited Resolution",
                estimated_cost=200.00,
                time_to_resolution=4.0,
                resident_satisfaction_impact=0.85
            ),
            SimulatedOption(
                option_id="fallback_3",
                action="Self-Service Option",
                estimated_cost=10.00,
                time_to_resolution=1.0,
                resident_satisfaction_impact=0.50
            )
        ]
        return SimulationResponse(options=fallback_options, issue_id="fallback")

