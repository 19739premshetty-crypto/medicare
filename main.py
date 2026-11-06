import json
import time
from datetime import datetime
from database import create_database, get_events
from database import get_events

from reminder_engine import (
    send_reminder,
    check_no_response,
    record_patient_response,
    event_log,
)

medications = [
    {
        "name": "Medicine A",
        "time": datetime.now().strftime("%H:%M"),
        "status": "scheduled",
        "response_prompted": False,
    },
    {
        "name": "Medicine B",
        "time": datetime.now().strftime("%H:%M"),
        "status": "scheduled",
        "response_prompted": False,
    },
    {
        "name": "Medicine C",
        "time": datetime.now().strftime("%H:%M"),
        "status": "scheduled",
        "response_prompted": False,
    },
]

print("Medication Reminder System Started...")
create_database()

try:
    while True:
        for medicine in medications:

            send_reminder(medicine)

            if medicine["status"] == "delivered" and not medicine["response_prompted"]:
                print("\nPatient Response:")
                print("1. Confirmed")
                print("2. Skipped")
                print("3. No response")

                choice = input("Enter choice: ")
                medicine["response_prompted"] = True

                if choice == "1":
                    record_patient_response(medicine, "confirmed")

                elif choice == "2":
                    record_patient_response(medicine, "skipped")

                elif choice == "3":
                    print("Waiting for patient response...")

                else:
                    print("Invalid choice. Waiting for response.")

            check_no_response(medicine, timeout=30)

        time.sleep(2)

except KeyboardInterrupt:
    print("\nReminder system stopped.")

    print("\n========== EVENT HISTORY ==========")

    for event in event_log:
        print(event)

    print("===================================")
    with open("events.json", "w") as file:
        json.dump(event_log, file, indent=4)

    print("\nEvents exported successfully to events.json")
    print("\n========== DATABASE EVENT HISTORY ==========")

for row in get_events():
    print(row)

print("============================================")
