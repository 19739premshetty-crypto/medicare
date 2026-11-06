
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def generate_doctor_pdf(insights):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#5425A8"),
        fontSize=22,
        spaceAfter=15
    )

    story = []

    story.append(Paragraph("MediMitra AI", title_style))
    story.append(Paragraph(
        "Doctor Medication Adherence Report",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 15))

    story.append(Paragraph(
        "Report Type: Demonstration Report",
        styles["Normal"]
    ))

    story.append(Spacer(1, 15))

    story.append(Paragraph(
        "Medication Adherence Summary",
        styles["Heading2"]
    ))

    missed = insights["missed_doses"]
    refill = insights["refill"]

    data = [
        ["Metric", "Result"],
        [
            "Adherence Percentage",
            f'{insights["adherence_percentage"]}%'
        ],
        ["Total Missed Doses", str(missed["total_missed"])],
        [
            "Most Missed Medicine",
            missed["most_missed_medicine"]
        ],
        ["Common Missed Dose Reason", missed["common_reason"]],
        [
            "Estimated Days Remaining",
            str(refill["days_remaining"])
        ],
        ["Refill Status", refill["refill_status"]]
    ]

    table = Table(data, colWidths=[85 * mm, 85 * mm])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5425A8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(table)

    story.append(Spacer(1, 25))

    story.append(Paragraph(
        "Note: This report is for informational purposes only. "
        "It is not a medical diagnosis or a recommendation to change "
        "medication or dosage. Clinical decisions should be made "
        "by a qualified healthcare professional.",
        styles["Italic"]
    ))

    document.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
