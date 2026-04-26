import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "history.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# ✅ INIT DB (moved from app.py)
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        score INTEGER,
        risk TEXT,
        user_id INTEGER,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


# ✅ INSERT (store REAL datetime, not just display format)
def insert_history(text, score, risk, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO history (text, score, risk, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (text, score, risk, user_id, now)
    )

    conn.commit()
    conn.close()


# ✅ FETCH (format time for UI)
def get_all_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, text, score, risk, created_at FROM history WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    from datetime import datetime

    history = []
    for row in rows:
        formatted_time = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")

        history.append({
            "id": row[0],
            "text": row[1],
            "score": row[2],
            "risk": row[3],
            "time": formatted_time
        })

    return history


# ✅ DELETE SELECTED
def delete_by_ids(ids):
    conn = get_connection()
    cursor = conn.cursor()

    for id in ids:
        cursor.execute("DELETE FROM history WHERE id = ?", (id,))

    conn.commit()
    conn.close()


# ✅ DELETE BY TIME RANGE (FINAL FIX)
def delete_by_time(hours):
    conn = get_connection()
    cursor = conn.cursor()

    if hours == 0:
        cursor.execute("DELETE FROM history")
    else:
        cursor.execute(
            f"DELETE FROM history WHERE datetime(created_at) >= datetime('now', '-{hours} hours')"
        )

    conn.commit()
    conn.close()


def create_user(username, password, email):
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = generate_password_hash(password)  # ✅ inside function

    try:
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, hashed_password, email)   # ✅ use hashed password
        )
        conn.commit()
        return True

    except Exception as e:
        print("ERROR:", e)
        return False

    finally:
        conn.close()

def get_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[2], password):
        return user

    return None

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    conn.close()
    return user