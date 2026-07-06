import sqlite3
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

SIGNUP_DB = "signup.db"
PREV_RESULT_DB = "previous_result.db"

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_dbs():
    # Initialize signup.db
    conn = get_db_connection(SIGNUP_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # Initialize previous_result.db
    conn = get_db_connection(PREV_RESULT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            inputs TEXT NOT NULL,
            prediction REAL NOT NULL,
            suggestions TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(name, username, email, phone, password):
    init_dbs()
    hashed_password = generate_password_hash(password)
    conn = get_db_connection(SIGNUP_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, username, email, phone, password) VALUES (?, ?, ?, ?, ?)",
            (name, username, email, phone, hashed_password)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, email, password):
    init_dbs()
    conn = get_db_connection(SIGNUP_DB)
    cursor = conn.cursor()
    # Relax check to allow matching by either username or email (case-insensitively)
    cursor.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
        (username, email)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user["password"], password):
        return dict(user)
    return None

def get_all_users():
    init_dbs()
    conn = get_db_connection(SIGNUP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT name, username, email, phone FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def add_prediction(username, inputs, prediction, suggestions):
    init_dbs()
    inputs_json = json.dumps(inputs)
    conn = get_db_connection(PREV_RESULT_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO predictions (username, inputs, prediction, suggestions) VALUES (?, ?, ?, ?)",
        (username, inputs_json, prediction, suggestions)
    )
    conn.commit()
    conn.close()

def get_predictions_for_user(username):
    init_dbs()
    conn = get_db_connection(PREV_RESULT_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, inputs, prediction, suggestions FROM predictions WHERE username = ? ORDER BY timestamp DESC",
        (username,)
    )
    rows = cursor.fetchall()
    predictions = []
    for row in rows:
        pred_dict = dict(row)
        pred_dict["inputs"] = json.loads(pred_dict["inputs"])
        predictions.append(pred_dict)
    conn.close()
    return predictions

def get_all_predictions():
    init_dbs()
    conn = get_db_connection(PREV_RESULT_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, timestamp, inputs, prediction, suggestions FROM predictions ORDER BY timestamp DESC"
    )
    rows = cursor.fetchall()
    predictions = []
    for row in rows:
        pred_dict = dict(row)
        pred_dict["inputs"] = json.loads(pred_dict["inputs"])
        predictions.append(pred_dict)
    conn.close()
    return predictions

# Initialize the databases immediately when this module is imported
init_dbs()
