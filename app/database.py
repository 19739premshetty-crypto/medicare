import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "medication_platform.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminder_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine TEXT NOT NULL,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    print("Database initialized successfully.")


def save_event(event):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reminder_events (medicine, event, timestamp)
        VALUES (?, ?, ?)
        """,
        (event["medicine"], event["event"], event["timestamp"]),
    )

    connection.commit()
    connection.close()


def get_events():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM reminder_events")
    events = cursor.fetchall()

    connection.close()
    return events
