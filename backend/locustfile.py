from locust import HttpUser, task, between
import random

# to run
# locust --headless \
#     --users 50 \
#     --spawn-rate 5 \
#     --run-time 60s \
#     --host https://localhost:8000

# Simulate a user
class OSRSUser(HttpUser):
    # set a wait time
    wait_time = between(1, 2)

    @task
    def create_item(self):
        # we need to generate random IDs otherwise the database 
        # will throw errors
        item_id = random.randint(1000000, 9999999)
        self.client.post(
            "/api/osrs/database/create",
            json={
                "item_id": item_id,
                "item_name": "Load Test Item",
                "item_value": 1000
            }
        )

    @task
    def update_item(self):
        self.client.put(
            "/api/osrs/database/update/999999",
            json={
                "item_name": "Updated Load Test Item",
                "item_value": 2000
            }
        )