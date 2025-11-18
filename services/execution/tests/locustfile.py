from locust import HttpUser, task, between
import random


class ExecutionServiceUser(HttpUser):
    wait_time = between(1, 3)
    
    actions = ["approve", "reject", "escalate", "defer"]
    priorities = ["low", "medium", "high", "critical"]
    teams = ["maintenance_team", "emergency_team", "specialist_team", "general_team"]
    
    @task(10)
    def execute_decision(self):
        categories = ["Maintenance", "Billing", "Security", "Deliveries", "Amenities"]
        actions = ["Approve", "Reject", "Escalate", "Schedule"]
        
        payload = {
            "chosen_action": random.choice(actions),
            "chosen_option_id": f"option_{random.randint(1, 10)}",
            "reasoning": "Load test execution",
            "alternatives_considered": ["Option A", "Option B"],
            "category": random.choice(categories)
        }
        
        with self.client.post(
            "/api/v1/execute",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Execution failed: {response.status_code}")
    
    @task(3)
    def check_execution_status(self):
        execution_id = f"exec_{random.randint(10000, 99999)}"
        with self.client.get(
            f"/api/v1/executions/{execution_id}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is OK
                response.success()
            else:
                response.failure(f"Status check failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
