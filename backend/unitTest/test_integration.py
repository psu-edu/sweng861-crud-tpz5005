import pytest
from fastapi.testclient import TestClient

# Import your FastAPI app instance from main.py
from main import app

# Create an API TestClient instance
client = TestClient(app)

# Disable rate limiting during tests
app.state.limiter.enabled = False

# To Run
# python -m pytest unitTest/test_integration.py -v

# To run all backend
# python -m pytest unitTest/ -v

# ==================================================================#
# Test authentication, CRUD, adn permission (happy path)
# ==================================================================#
#-----------------------------------------------#
def test_login_create_fetch():
#-----------------------------------------------#
    """ Brief: Tests the create_item WITH a JWT token
        1. Authenticate and recieve JWT toekn
        2. Create a OSRS item with the token
        3. get the item """
    # Attempt to log in and get a token
    login_payload = {"username": "student", "password": "student123"}
    login_response = client.post("/token", data=login_payload)
    
    # If using custom JSON login route, fallback to json format:
    if login_response.status_code != 200:
        login_response = client.post("/auth/custom", json=login_payload)

    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token_data = login_response.json()
    access_token = token_data.get("access_token") or token_data.get("token")
    assert access_token is not None

    # should have token
    headers = {"Authorization": f"Bearer {access_token}"}

    # create an item
    new_item = {
        "item_id": 1234,
        "item_name": "Twisted Bow",
        "item_value": 999999
    }

    # attempt to create the item
    create_response = client.post("/api/osrs/database/create", json=new_item, headers=headers)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.text}"

    # attempt to get the item
    fetch_response = client.get("/api/osrs/database/read/1234", headers=headers)
    assert fetch_response.status_code == 200

    # read the item and make sure it exists
    fetched_data = fetch_response.json()
    assert fetched_data["id"] == 1234
    assert fetched_data["item"] == "Twisted Bow"
    assert fetched_data["price"] == 999999


# ==================================================================#
# Create a bad item (Invalid Input & Missing Fields)
# ==================================================================#
#-----------------------------------------------#
def test_create_item_invalid_data():
#-----------------------------------------------#
    """
    Brief: Attempts to create an item with a malformed json
            Expects to receive a 4-- error
    """
    # Attempt to create an item without a price, bad ID, 
    # and no description
    invalid_item_payload = {
        "id": "not_an_integer_id",
        "item": ""
    }

    # attemnt to create the item
    response = client.post("/items/", json=invalid_item_payload)
    
    # make sure it returns a 4-- error
    assert response.status_code in (400, 404, 422), f"Expected 4--, got {response.status_code}"


#-----------------------------------------------#
def test_fetch_missing_item():
#-----------------------------------------------#
    """ Brief: Attempts to get an item that does not exist """
    not_real_id = 777777
    response = client.get(f"/items/{not_real_id}")

    # make sure it returns a 404 not found
    assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}"


# ==================================================================#
# Item ownsership
# ==================================================================#
#-----------------------------------------------#
def test_ownership_authorization():
#-----------------------------------------------#
    """ Brief: Creates an item as user A and attempts to get it as user B.
               Expects to recieve a 403 error. """
    # Authenticate as user A
    login_A = client.post("/token", data={"username": "student", "password": "student123"})
    if login_A.status_code != 200:
        login_A = client.post("/login", json={"username": "student", "password": "student123"})
    token_A = login_A.json().get("access_token") or login_A.json().get("token")
    headers_A = {"Authorization": f"Bearer {token_A}"}

    item_id = 8881
    # creat the item with user A
    client.post("/items/", 
                json={"id": item_id, 
                      "item": "Abyssal Whip", 
                      "price": 1500000, 
                      "created_by": "student"}, 
                headers=headers_A)

    # Create the header of someone who does not have authorization (user B)
    user_B_header = {"Authorization": "Bearer invalid_or_other_user_token"}

    # attempt to read the item
    update_response = client.put(f"/items/{item_id}", json={"price": 1}, headers=user_B_header)
    
    assert update_response.status_code in (401, 403, 404), f"Expected permission failure, got {update_response.status_code}"