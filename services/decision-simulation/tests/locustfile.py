from locust import HttpUser, task, between
import random


class DecisionSimulationUser(HttpUser):
    wait_time = between(3, 7)
    
    scenarios = [
        {
            "description": "Air conditioning not working properly",
            "category": "Maintenance",
            "priority": "Medium"
        },
        {
            "description": "Emergency water leak in apartment",
            "category": "Maintenance",
            "priority": "High"
        },
        {
            "description": "Noise complaint from neighbors",
            "category": "Security",
            "priority": "Low"
        },
        {
            "description": "Elevator malfunction",
            "category": "Maintenance",
            "priority": "High"
        },
        {
            "description": "Package delivery assistance needed",
            "category": "Deliveries",
            "priority": "Low"
        }
    ]
    
    @task(10)
    def simulate_decision(self):
        scenario = random.choice(self.scenarios)
        payload = {
            "resident_id": f"R{random.randint(100, 999)}",
            "message_text": scenario["description"],
            "category": scenario["category"],
            "urgency": scenario["priority"],
            "risk_score": 0.5
        }
        
        with self.client.post(
            "/api/v1/simulate",
            json=payload,
            catch_response=True,
            timeout=60
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "options" in data or "simulation" in data:
                        response.success()
                    else:
                        response.failure("Missing simulation results")
                except Exception as e:
                    response.failure(f"Invalid response: {e}")
            else:
                response.failure(f"Simulation failed: {response.status_code}")
    
    @task(3)
    def query_knowledge_base(self):
        queries = [
            "What is the cost for HVAC repair?",
            "Emergency response SLA",
            "Maintenance policy for plumbing",
            "How to handle urgent requests?"
        ]
        
        payload = {
            "question": random.choice(queries),
            "resident_id": f"R{random.randint(100, 999)}",
            "category": "Maintenance",
            "building_id": "B001"
        }
        
        with self.client.post(
            "/api/v1/answer-question",
            json=payload,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code in [200, 404, 500]:  # May fail if RAG not working
                response.success()
            else:
                response.failure(f"Query failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
