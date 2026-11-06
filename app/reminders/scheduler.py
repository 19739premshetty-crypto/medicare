from datetime import datetime, timedelta


def is_reminder_due(medicine):
    current_time = datetime.now().strftime("%H:%M")

    if current_time >= medicine["time"]:
        return True

    return False


def is_quiet_hours(medicine, current_time=None):

    if current_time is None:
        current_time = datetime.now()

    start = datetime.strptime(medicine["quiet_hours_start"], "%H:%M").time()

    end = datetime.strptime(medicine["quiet_hours_end"], "%H:%M").time()

    current = current_time.time()

    if start < end:
        return start <= current < end

    return current >= start or current < end


def next_allowed_time(medicine, current_time=None):

    if current_time is None:
        current_time = datetime.now()

    end = datetime.strptime(medicine["quiet_hours_end"], "%H:%M").time()

    target = datetime.combine(current_time.date(), end)

    start = datetime.strptime(medicine["quiet_hours_start"], "%H:%M").time()

    if start > end and current_time.time() >= start:
        target += timedelta(days=1)

    return target


if __name__ == "__main__":

    medicine = {"name": "Medicine A", "time": "14:00"}

    result = is_reminder_due(medicine)

    print("Reminder due:", result)
if __name__ == "__main__":

    medicine = {
        "name": "Medicine A",
        "time": "23:00",
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "07:00",
    }

    test_time = datetime.strptime("2026-11-06 23:30", "%Y-%m-%d %H:%M")

    print("Quiet hours:", is_quiet_hours(medicine, test_time))

    print("Next allowed time:", next_allowed_time(medicine, test_time))
