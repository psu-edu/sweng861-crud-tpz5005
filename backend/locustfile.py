import os
import random
import urllib3
from datetime import datetime, timedelta, timezone
import jwt
from locust import HttpUser, task, between
from dotenv import load_dotenv

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

SECRET_KEY = os.getenv("CUSTOM_JWT_KEY", "dev_default_secret_key_123")
ALGORITHM = "HS256"

def generate_locust_token(username: str = "student") -> str:
    """Generates a valid JWT signed with the shared secret key."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    payload = {
        "sub": username,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# to run
#locust --headless --users 50 --spawn-rate 5 --run-time 20s --host https://localhost:8000

# Simulate a user
class OSRSUser(HttpUser):
    # set a wait time
    wait_time = between(1, 2)

    def on_start(self):
        # Disable SSL verification for self-signed certificates
        self.client.verify = False

        # Track items created by this virtual user session
        self.created_item_ids = []

        # Generate JWT
        token = generate_locust_token(username="student")
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def create_item(self):
        # we need to generate random IDs otherwise the database 
        # will throw errors
        item_id = random.randint(1000000, 9999999)
        response = self.client.post(
            "/api/osrs/database/create",
            json={
                "item_id": item_id,
                "item_name": "Load Test Item",
                "item_value": 1000
            }
        )

        # since i am using random IDs i need to keep track of them all
        if response.status_code in (200, 201):
            self.created_item_ids.append(item_id)

    @task(2)
    def update_item(self):
        if not self.created_item_ids:
            return

        #Randomly choose an id
        item_id = random.choice(self.created_item_ids)

        self.client.put(
            f"/api/osrs/database/update/{item_id}",
            json={
                "item_name": "Updated Load Test Item",
                "item_value": 2000
            }
        )