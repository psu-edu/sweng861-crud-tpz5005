import pytest
import jwt

from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from custom_auth import ALGORITHM, SECRET_KEY, create_jwt_token, valid_user
from database import handle_user_login_data
from main import app, require_admin, verify_owner_or_admin
from custom_auth import create_jwt_token

client = TestClient(app)

# Disable rate limiting during tests
app.state.limiter.enabled = False

# Helper function to generate authorization headers
#-----------------------------------------------#
def get_auth_header(username: str):
#-----------------------------------------------#
    token = create_jwt_token(username)
    return {"Authorization": f"Bearer {token}"}


# ==================================================================#
# Unauthenticated Access 401
# ==================================================================#
#-----------------------------------------------#
def test_get_item_invalid_token_returns_401():
#-----------------------------------------------#
    """Test the validity of a token"""
    headers = {"Authorization": "Bearer invalid_token_psu"}
    response = client.get("/api/osrs/database/read/1333", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid JWT token"


# ==================================================================#
# Authenticated access to own data 200
# ==================================================================#
@patch("main.read_item")
#-----------------------------------------------#
def test_get_item_owner_returns_200(mock_read_item):
#-----------------------------------------------#
    """Verify that the creator of an item can retrieve it successfully (200 OK)."""
    # Arrange: Item owned by student
    mock_read_item.return_value = {
        "id": 1333,
        "item": "Rune Scimitar",
        "price": 25000,
        "created_by": "student"
    }
    headers = get_auth_header("student")

    # Act
    response = client.get("/api/osrs/database/read/1333", headers=headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1333
    assert data["item"] == "Rune Scimitar"
    assert data["created_by"] == "student"


# ==================================================================#
# 403 FORBIDDEN (NON-OWNER ACCESS) TESTS
# ==================================================================#
@patch("main.read_item")
#-----------------------------------------------#
def test_get_item_owner_returns_403(mock_read_item):
#-----------------------------------------------#
    """Verify that a non-owner, non-admin user receives 403 Forbidden."""
    # Arrange: Item owned by professor
    mock_read_item.return_value = {
        "id": 1333,
        "item": "Rune Scimitar",
        "price": 25000,
        "created_by": "professor"
    }
    # Authenticate as student
    headers = get_auth_header("student")

    # Act
    response = client.get("/api/osrs/database/read/1333", headers=headers)

    # Assert
    assert response.status_code == 403
    assert response.json()["detail"] == "You are not authorized to view this item."


# ==================================================================#
# 404 NOT FOUND TESTS
# ==================================================================#
@patch("main.read_item")
#-----------------------------------------------#
def test_get_item_not_found_returns_404(mock_read_item):
#-----------------------------------------------#
    """Verify that requesting a non-existent item returns 404 Not Found."""
    mock_read_item.return_value = None
    headers = get_auth_header("player_one")

    response = client.get("/api/osrs/database/read/9999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "This item does not exist or has been deleted."


# ==================================================================#
# Authentication Tests
# ==================================================================#
#-----------------------------------------------#
def test_valid_user():
#-----------------------------------------------#
    """ Target: valid_user
    Brief: Tests the password fields on the login form """
    # Setup different user data
    valid_username = "student"
    valid_password = "student123"
    wrong_password = "wrongpassword"
    unknown_user = "nobody"

    # Test different scanarios
    success = valid_user(valid_username, valid_password)
    fail_wrong_pass = valid_user(valid_username, wrong_password)
    fail_no_user = valid_user(unknown_user, valid_password)

    # Check against expected values
    assert success is True
    assert fail_wrong_pass is False
    assert fail_no_user is False


@patch("database.create_user")
@patch("database.update_user_login")
@patch("database.sqlite3.connect")
#-----------------------------------------------#
def test_handle_user_login_data(mock_connect, 
                                mock_update_user, 
                                mock_create_user):
#-----------------------------------------------#
    """ Target: handle_user_login_data()
        Brief: Tests OAuth login routing in database"""
    # Create fake database cursor
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor

    # create fake users
    new_user_profile = {"id": 12345, "email": "newUser@psu.edu"}
    existing_user_profile = {"id": 67890, "email": "existingUser@psu.edu"}

    # Simulate no provider_id being found
    mock_cursor.fetchone.return_value = None
    handle_user_login_data(new_user_profile)

    # verify that create_user was in fact called
    mock_create_user.assert_called_once_with("12345", "newUser@psu.edu")

    # Simulate an existing user
    mock_cursor.fetchone.return_value = (1, "67890", "existingUser@psu.edu", "user", "time", "time")
    handle_user_login_data(existing_user_profile)

    # Verify that update_user_login was called
    mock_update_user.assert_called_once_with("67890", "existingUser@psu.edu")


#-----------------------------------------------#
def test_create_jwt_token():
#-----------------------------------------------#
    """ Target: create_jwt_token()
        Brief: Tests JWT token generation"""
    # Test a professor
    username = "professor"

    # attempt to get a token
    token = create_jwt_token(username)

    # Decode the token to inspect the payload
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    # the sub claim should match 'professor'
    assert decoded_payload.get("sub") == "professor"
    # also check to make sure it has an expiration date
    assert "exp" in decoded_payload


#-----------------------------------------------#
def test_verify_owner_or_admin():
#-----------------------------------------------#
    """ Target: verify_owner_or_admin()
        Brief: Tests the ownership of items or if user is admin"""
    # Create some scenarios
    owner_user = {"id": 101, "role": "user"}
    admin_user = {"id": 999, "role": "admin"}
    unauthorized_user = {"id": 202, "role": "user"}
    resource_owner_id = 101

    # Test a happy paths
    owner_access = verify_owner_or_admin(owner_user, resource_owner_id)
    # user id does not match but user is an admin 
    admin_access = verify_owner_or_admin(admin_user, resource_owner_id)

    # test to make sure they are granted access to the data
    assert owner_access == owner_user
    assert admin_access == admin_user

    # If the user is not the owner or an admin, make sure
    # it throws a 403 error
    with pytest.raises(HTTPException) as exc_info:
        verify_owner_or_admin(unauthorized_user, resource_owner_id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
#-----------------------------------------------#
async def test_require_admin():
#-----------------------------------------------#
    """ Target: require_admin()
        Brief: tests that endpoints that require admin throw a 403 error"""
    # create a student
    student_user = {"username": "student", "role": "student"}

    # try to access as a student
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=student_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Admin privlages required"