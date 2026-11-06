from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_doctor_pdf(insights):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#5425A8"),
        fontSize=22,
        spaceAfter=15,
    )

    story = []

    story.append(Paragraph("MediCare", title_style))
    story.append(
        Paragraph(
            "Medication Adherence Report",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"Report generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "Report Type: Demonstration Report",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 15))

    # Adherence summary
    story.append(Paragraph("Medication Adherence Summary", styles["Heading2"]))

    missed = insights["missed_doses"]

    summary_data = [
        ["Metric", "Result"],
        ["Adherence Percentage", f'{insights["adherence_percentage"]}%'],
        ["Total Missed Doses", str(missed["total_missed"])],
        ["Most Missed Medicine", str(missed["most_missed_medicine"])],
        ["Common Missed Dose Reason", str(missed["common_reason"])],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[85 * mm, 85 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5425A8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Refill information for every medicine
    story.append(Paragraph("Medicine Refill Overview", styles["Heading2"]))

    refill_data = [["Medicine", "Days Remaining", "Refill Status"]]

    for medicine in insights["refill"]:
        days = medicine["days_remaining"]

        refill_data.append(
            [
                str(medicine["name"]),
                str(days) if days is not None else "Not entered",
                str(medicine["refill_status"]),
            ]
        )

    if len(refill_data) == 1:
        refill_data.append(["No medicines found", "-", "-"])

    refill_table = Table(
        refill_data,
        colWidths=[60 * mm, 45 * mm, 65 * mm],
    )

    refill_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5425A8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(refill_table)
    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "Note: This demonstration report is for informational "
            "purposes only. It is not a medical diagnosis or a "
            "recommendation to change medication or dosage. "
            "Clinical decisions should be made by a qualified "
            "healthcare professional.",
            styles["Italic"],
        )
    )

    document.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
