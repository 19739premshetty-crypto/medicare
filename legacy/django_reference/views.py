from django.http import HttpResponse

from insights.analytics import (
    calculate_adherence,
    analyze_missed_doses,
    predict_refill
)

from .pdf_generator import generate_doctor_pdf


sample_doses = [
    {"medicine": "Medicine A", "status": "taken"},
    {"medicine": "Medicine B", "status": "taken"},
    {"medicine": "Medicine A", "status": "missed", "reason": "Forgot"},
    {"medicine": "Medicine B", "status": "taken"},
    {"medicine": "Medicine A", "status": "missed", "reason": "Busy"},
]


def doctor_report(request):

    insights = {
        "adherence_percentage": calculate_adherence(sample_doses),
        "missed_doses": analyze_missed_doses(sample_doses),
        "refill": predict_refill(6, 2)
    }

    pdf_file = generate_doctor_pdf(insights)

    response = HttpResponse(
        pdf_file,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="medimitra_doctor_report.pdf"'
    )

    return response