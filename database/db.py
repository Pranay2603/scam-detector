import sqlite3
from datetime import datetime

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
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# ✅ INSERT (store REAL datetime, not just display format)
def insert_history(text, score, risk):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO history (text, score, risk, created_at) VALUES (?, ?, ?, ?)",
        (text, score, risk, now)
    )

    conn.commit()
    conn.close()


# ✅ FETCH (format time for UI)
def get_all_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, text, score, risk, created_at FROM history ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()

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