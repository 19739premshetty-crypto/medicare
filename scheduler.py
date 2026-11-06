from datetime import datetime


def is_reminder_due(medicine):
    current_time = datetime.now().strftime("%H:%M")

    if current_time >= medicine["time"]:
        return True

    return False


if __name__ == "__main__":

    medicine = {"name": "Medicine A", "time": "14:00"}

    result = is_reminder_due(medicine)

    print("Reminder due:", result)
