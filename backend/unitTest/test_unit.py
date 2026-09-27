import sqlite3
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status

# Import functions across all backend modules
# from custom_auth import ALGORITHM, SECRET_KEY, create_jwt_token, valid_user
# from database import get_data_field, handle_user_login_data
# from main import require_admin, validate_data, verify_owner_or_admin
from osrsdatabase import create_item, read_item, update_item, delete_item, delete_all_items, get_all_ids


# ==================================================================#
# OSRS Database tests (CRUD)
# ==================================================================#
@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_create_item(mock_get_connection):
#-----------------------------------------------#
    """ Target: create_item()
        Brief: Tests the creation of items in the osrs database """
    # get a connection with a mock SQlite
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn

    # create item fields
    item_id = 1333
    item_name = "Rune Scimitar"
    item_value = 25000
    created_by = "player_one"

    # create the item
    create_item(item_id, item_name, item_value, created_by)

    # verify that sqlite executed with correct fields
    mock_conn.execute.assert_called_once_with(
        "INSERT OR REPLACE INTO items (id, item, price, created_by) VALUES (?, ?, ?, ?)",
        (1333, "Rune Scimitar", 25000, "player_one")
    )

    # verify it was executed
    mock_conn.commit.assert_called_once()


@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_read_item_valid(mock_get_connection):
#-----------------------------------------------#
    """  Target: read_item() -- valid data
        Brief: Tests the read function of osrs database when there is data """

    # make a connection with a mock cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Simulate sqlite3.Row behavior using a dictionary-like object
    db_row = {"id": 1333, "item": "Rune Scimitar", "price": 25000, "created_by": "player_one"}
    mock_cursor.fetchone.return_value = db_row

    # attempt to read the item
    result = read_item(1333)

    # verify that the item was found
    mock_cursor.execute.assert_called_once_with(
        "SELECT id, item, price, created_by FROM items WHERE id = ?", 
        (1333,)
    )

    # Verify format and content
    assert isinstance(result, dict)
    assert result == db_row
    assert result["item"] == "Rune Scimitar"


@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_read_item_not_valid(mock_get_connection):
#-----------------------------------------------#
    """  Target: read_item() -- invalid data
            Brief: Tests the read function of osrs database when there is no data """

    # make a connection with a mock cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Simulate item not found
    mock_cursor.fetchone.return_value = None

    # try to read a non-existant ID
    result = read_item(9999)

    # make sure it does not exist
    assert result is None


@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_update_item(mock_get_connection):
#-----------------------------------------------#
    """ Target: update_item()
        Brief: Tests to make sure non-allowed columns returns early """
    # Setup 
    item_id = 1333
    unsupported_fields = {"invalid_column": "some_value"}

    # Run
    update_item(item_id, unsupported_fields)

    # Check to make sure mock_get_connection was never called
    mock_get_connection.assert_not_called()


@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_delete_item_executes_delete_query(mock_get_connection):
#-----------------------------------------------#
    """ Target: update_item()
            Brief: Tests to make sure item is deleted form database """
    # Set up connection
    mock_conn = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn

    item_id_to_delete = 1333

    # Attempt to delete the item
    delete_item(item_id_to_delete)

    # verify the item was deleted
    mock_conn.execute.assert_called_once_with(
        "DELETE FROM items WHERE id = ?", 
        (1333,)
    )
    # verify it was called
    mock_conn.commit.assert_called_once()


@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_delete_all_items_returns_deleted_row_count(mock_get_connection):
#-----------------------------------------------#
    """ Target: update_item()
        Brief: Tests to make sure all items are deleted """
    # set up database connections
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # 
    mock_get_connection.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # simulate multiple item deletions
    mock_cursor.rowcount = 5

    # attempt to delete the items
    deleted_count = delete_all_items()

    # verify they are deleted
    mock_cursor.execute.assert_called_once_with("DELETE FROM items")
    assert deleted_count == 5
    # verufy it was called
    mock_conn.close.assert_called_once()


# ==================================================================#
# Utility Test
# ==================================================================#
@patch("osrsdatabase.get_connection")
#-----------------------------------------------#
def test_get_all_ids(mock_get_connection):
#-----------------------------------------------#
    """ Target: get_all_ids()
            Brief: Verify we can obtain all the ids in the database """
    # mock connections
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Simulate multiple rows returned
    mock_rows = [{"id": 1333}, {"id": 4151}, {"id": 11832}]
    mock_cursor.fetchall.return_value = mock_rows

    # Attempt to get all IDS
    ids = get_all_ids()

    # Verify it recieved all the items
    mock_cursor.execute.assert_called_once_with("SELECT id FROM items")
    assert ids == [1333, 4151, 11832]