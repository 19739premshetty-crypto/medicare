from itertools import count
from datetime import datetime, timedelta
import time
from app.reminders.reminder_engine import send_reminder, log_event

counter = count()
import heapq
from datetime import datetime

reminder_queue = []


def add_reminder(medicine, scheduled_time):
    heapq.heappush(reminder_queue, (scheduled_time, next(counter), medicine))

    print(f"Added {medicine['name']} to the queue.")


def get_next_reminder():
    if reminder_queue:
        scheduled_time, _, medicine = heapq.heappop(reminder_queue)

        return scheduled_time, medicine

    return None


def process_queue(callback, max_retries=2, retry_delay=3):

    while reminder_queue:

        result = get_due_reminder()

        if result:
            scheduled_time, medicine = result

            print(f"\nProcessing: {medicine['name']}")

            previous_status = medicine.get("status")
            previous_delivery_time = medicine.get("delivered_at")

            try:
                callback(medicine)

                medicine["retry_count"] = 0

            except Exception as error:

                # Restore the medicine's previous state
                medicine["status"] = previous_status

                if previous_delivery_time is None:
                    medicine.pop("delivered_at", None)
                else:
                    medicine["delivered_at"] = previous_delivery_time

                attempts = medicine.get("retry_count", 0) + 1
                medicine["retry_count"] = attempts

                if attempts <= max_retries:

                    retry_time = datetime.now() + timedelta(seconds=retry_delay)

                    print(f"Delivery failed: {error}")
                    print(f"Retrying ({attempts}/{max_retries})...")

                    add_reminder(medicine, retry_time)

                else:

                    print("Maximum retries reached.")
                    print(f"Final error: {error}")

                    try:
                        log_event(medicine, "delivery_failed")
                    except Exception as log_error:
                        print("Could not save failure event:", log_error)

        else:
            time.sleep(1)


def get_due_reminder():
    if not reminder_queue:
        return None

    scheduled_time = reminder_queue[0][0]

    if scheduled_time <= datetime.now():
        return get_next_reminder()

    return None


def display_queue():
    if not reminder_queue:
        print("Reminder queue is empty.")
        return

    print("\n========== UPCOMING REMINDERS ==========")

    for scheduled_time, _, medicine in sorted(reminder_queue):
        print(
            f"{medicine['name']} - " f"{scheduled_time.strftime('%d-%m-%Y %H:%M:%S')}"
        )

    print("========================================")


if __name__ == "__main__":

    medicine_a = {
        "name": "Medicine A",
        "time": datetime.now().strftime("%H:%M"),
        "status": "scheduled",
    }

    medicine_b = {
        "name": "Medicine B",
        "time": datetime.now().strftime("%H:%M"),
        "status": "scheduled",
    }

    now = datetime.now()

    add_reminder(medicine_a, now + timedelta(seconds=3))
    add_reminder(medicine_b, now + timedelta(seconds=6))

    test_attempts = {"count": 0}

    def reminder_callback(medicine):
        send_reminder(medicine)

    process_queue(reminder_callback)

    print("\nAll reminders processed.")
