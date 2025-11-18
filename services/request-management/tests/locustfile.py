from locust import HttpUser, task, between, events
import random
import time


class RequestManagementUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.user_id = f"load_test_user_{random.randint(1000, 9999)}"
        self.request_ids = []
    
    @task(3)
    def view_requests(self):
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def create_request(self):
        messages = [
            "Air conditioning not working in unit",
            "Water leak in bathroom",
            "Noise complaint from neighbor",
            "Broken window needs repair",
            "Emergency heating issue"
        ]
        
        payload = {
            "resident_id": self.user_id,
            "message_text": random.choice(messages)
        }
        
        with self.client.post(
            "/api/v1/submit-request",
            json=payload,
            catch_response=True,
            timeout=60
        ) as response:
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    if "request_id" in data:
                        self.request_ids.append(data["request_id"])
                    response.success()
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def check_health(self):
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    



class StressTestUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task
    def rapid_fire_requests(self):
        self.client.get("/health")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*60)
    print("LOAD TEST STARTING")
    print("="*60)
    print(f"Host: {environment.host}")
    print(f"Users: Will ramp up based on your settings")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*60)
    print("LOAD TEST COMPLETED")
    print("="*60)
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")
    print("="*60 + "\n")
