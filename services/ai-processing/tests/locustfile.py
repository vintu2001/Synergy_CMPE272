from locust import HttpUser, task, between
import random


class AIProcessingUser(HttpUser):
    wait_time = between(2, 5)
    
    descriptions = [
        "The air conditioning is not working",
        "Water leak in the kitchen",
        "Noise from upstairs neighbor",
        "Package delivery assistance needed",
        "Parking spot issue",
        "Emergency: Gas smell detected",
        "Light bulb replacement needed",
        "Gym equipment broken",
        "Pool maintenance required",
        "Elevator not working properly"
    ]
    
    categories = ["maintenance", "complaint", "emergency", "suggestion"]
    priorities = ["low", "medium", "high", "critical"]
    
    @task(5)
    def classify_request(self):
        payload = {
            "resident_id": f"R{random.randint(100, 999)}",
            "message_text": random.choice(self.descriptions)
        }
        
        with self.client.post(
            "/api/v1/classify",
            json=payload,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Classification failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
