import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

db_name = "osrs_db"

# gets the connection object to the database
#-----------------------------------------------#
def get_connection():
#-----------------------------------------------#
    connection = sqlite3. connect(db_name)
    connection.row_factory = sqlite3.Row
    return connection

# gets the registered ids
#-----------------------------------------------#
def get_all_ids():
#-----------------------------------------------#
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM items")
        rows = cursor.fetchall()
        return [row["id"] for row in rows]

# Initialize the database
#-----------------------------------------------#
def init_osrs_db():
#-----------------------------------------------#
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                item TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        """)
        connection.commit()


# Create
#-----------------------------------------------#
def create_item(item_id: int, item_name: str, item_value: int):
#-----------------------------------------------#
    with get_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO items (id, item, price) VALUES (?, ?, ?)",
            (item_id, item_name, item_value)
        )
        connection.commit()

# Read 
#-----------------------------------------------#
def read_item(item_id: int):
#-----------------------------------------------#
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, item, price FROM items WHERE id = ?", 
            (item_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

# Update
#-----------------------------------------------#
def update_item(item_id: int, fields: dict):
#-----------------------------------------------#
    if not fields:
        return 

    set_clauses = []
    values = []
    for key, val in fields.items():
        if key in ("item", "price"):
            set_clauses.append(f"{key} = ?")
            values.append(val)

    if not set_clauses:
        return

    values.append(item_id)
    query = f"UPDATE items SET {', '.join(set_clauses)} WHERE id = ?"

    with get_connection() as connection:
        connection.execute(query, values)
        connection.commit()

# Delete
#-----------------------------------------------#
def delete_item(item_id: int):
#-----------------------------------------------#
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM items WHERE id = ?", 
            (item_id,)
        )
        connection.commit()