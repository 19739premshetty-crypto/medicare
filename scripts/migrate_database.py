import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

REMINDER_DB = BASE_DIR / "medication.db"
PLATFORM_DB = BASE_DIR / "medicine.db"

DATA_DIR = BASE_DIR / "data"
TARGET_DB = DATA_DIR / "medication_platform.db"


def migrate_database():
    if TARGET_DB.exists():
        print("Target database already exists.")
        print("Migration cancelled to protect existing data.")
        return

    if not REMINDER_DB.exists() or not PLATFORM_DB.exists():
        print("One or both source databases are missing.")
        return

    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(TARGET_DB)
    cursor = connection.cursor()

    try:
        connection.execute("ATTACH DATABASE ? AS reminders", (str(REMINDER_DB),))

        connection.execute("ATTACH DATABASE ? AS platform", (str(PLATFORM_DB),))

        sources = [
            ("reminders", REMINDER_DB),
            ("platform", PLATFORM_DB),
        ]

        for alias, source_path in sources:
            source_cursor = connection.cursor()

            source_cursor.execute(f"""
                SELECT name, sql
                FROM {alias}.sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                """)

            tables = source_cursor.fetchall()

            for table_name, schema in tables:
                schema = schema.replace("CREATE TABLE ", "CREATE TABLE main.", 1)

                cursor.execute(schema)

                cursor.execute(f"""
                    INSERT INTO main."{table_name}"
                    SELECT * FROM {alias}."{table_name}"
                    """)

                print(f"Migrated: {table_name}")

        connection.commit()

        print("\nDatabase migration completed.")

    except Exception as error:
        connection.rollback()
        print("Migration failed:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_database()
