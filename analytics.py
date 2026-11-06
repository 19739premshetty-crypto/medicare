
def calculate_adherence(dose_records):
    """
    Calculate medication adherence percentage.

    Only taken and missed doses are included.
    Pending doses are excluded.
    """

    total_due = 0
    total_taken = 0

    for dose in dose_records:
        status = dose["status"].lower()

        if status == "taken":
            total_taken += 1
            total_due += 1

        elif status == "missed":
            total_due += 1

    if total_due == 0:
        return 0

    adherence = (total_taken / total_due) * 100

    return round(adherence, 2)


# Sample patient dose records
sample_doses = [
    {"medicine": "Medicine A", "status": "taken"},
    {"medicine": "Medicine B", "status": "taken"},
    {"medicine": "Medicine A", "status": "missed"},
    {"medicine": "Medicine B", "status": "taken"},
    {"medicine": "Medicine A", "status": "missed"},
]

result = calculate_adherence(sample_doses)

print("Medication Adherence:", result, "%")

def analyze_missed_doses(dose_records):
    missed_count = 0
    medicine_counts = {}
    reason_counts = {}

    for dose in dose_records:
        if dose["status"].lower() == "missed":
            missed_count += 1

            medicine = dose["medicine"]
            reason = dose.get("reason", "Not specified")

            medicine_counts[medicine] = medicine_counts.get(medicine, 0) + 1
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    most_missed_medicine = (
        max(medicine_counts, key=medicine_counts.get)
        if medicine_counts else "None"
    )

    common_reason = (
        max(reason_counts, key=reason_counts.get)
        if reason_counts else "None"
    )

    return {
        "total_missed": missed_count,
        "most_missed_medicine": most_missed_medicine,
        "common_reason": common_reason,
        "medicine_breakdown": medicine_counts,
        "reason_breakdown": reason_counts
    }


def predict_refill(quantity_remaining, daily_doses):
    if daily_doses <= 0:
        return {
            "days_remaining": None,
            "refill_status": "Invalid daily dose count"
        }

    days_remaining = quantity_remaining / daily_doses

    if days_remaining <= 3:
        status = "Refill urgently"
    elif days_remaining <= 7:
        status = "Refill soon"
    else:
        status = "Sufficient stock"

    return {
        "days_remaining": round(days_remaining, 1),
        "refill_status": status
    }

