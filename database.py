import sqlite3


def create_database():
    connection = sqlite3.connect("medication.db")

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
    connection = sqlite3.connect("medication.db")

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reminder_events
        (medicine, event, timestamp)
        VALUES (?, ?, ?)
    """,
        (event["medicine"], event["event"], event["timestamp"]),
    )

    connection.commit()
    connection.close()


def get_events():
    connection = sqlite3.connect("medication.db")

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM reminder_events")

    events = cursor.fetchall()

    connection.close()

    return events
