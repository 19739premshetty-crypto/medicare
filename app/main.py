from contextlib import contextmanager
from datetime import datetime
from typing import Literal
from pathlib import Path
from fastapi.responses import FileResponse
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import date, timedelta
from fastapi.responses import Response
from app.pdf_generator import generate_doctor_pdf

from app.database import get_connection
from app.analytics import (
    calculate_adherence,
    analyze_missed_doses,
    predict_refill,
)

app = FastAPI(
    title="Medication Adherence Platform",
    description="Medication tracking and adherence analytics API",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/dashboard")
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


@contextmanager
def database():
    connection = get_connection()
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


class MedicineRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dosage: str = Field(min_length=1, max_length=100)
    time: str = Field(min_length=1, max_length=20)


class DoseRequest(BaseModel):
    medicine_id: int
    status: Literal["taken", "missed"]
    reason: str = ""


class StockRequest(BaseModel):
    quantity_remaining: int = Field(ge=0)
    daily_doses: float = Field(gt=0)


@app.get("/")
def home():
    frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(frontend_path)


@app.get("/api/medicines")
def get_medicines():
    with database() as connection:
        rows = connection.execute("SELECT * FROM medicines ORDER BY id").fetchall()

    return [dict(row) for row in rows]


@app.post("/api/medicines")
def add_medicine(medicine: MedicineRequest):
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO medicines (name, dosage, time)
            VALUES (?, ?, ?)
            """,
            (medicine.name, medicine.dosage, medicine.time),
        )

        medicine_id = cursor.lastrowid

    return {
        "message": "Medicine added successfully",
        "id": medicine_id,
    }


@app.delete("/api/medicines/{medicine_id}")
def delete_medicine(medicine_id: int):
    with database() as connection:
        cursor = connection.execute(
            "DELETE FROM medicines WHERE id = ?",
            (medicine_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Medicine not found",
            )

    return {"message": "Medicine deleted successfully"}


@app.put("/api/medicines/{medicine_id}/stock")
def update_medicine_stock(medicine_id: int, stock: StockRequest):
    with database() as connection:
        cursor = connection.execute(
            """
            UPDATE medicines
            SET quantity_remaining = ?, daily_doses = ?
            WHERE id = ?
            """,
            (
                stock.quantity_remaining,
                stock.daily_doses,
                medicine_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Medicine not found",
            )

    return {"message": "Medicine stock updated successfully"}


@app.get("/api/refill-status")
def get_refill_status():
    with database() as connection:
        medicines = connection.execute("""
            SELECT id, name, quantity_remaining, daily_doses
            FROM medicines
            ORDER BY id
            """).fetchall()

    results = []

    for medicine in medicines:
        item = dict(medicine)

        if item["quantity_remaining"] is None or item["daily_doses"] is None:
            result = {
                "days_remaining": None,
                "refill_status": "Stock not entered",
            }
        else:
            result = predict_refill(
                item["quantity_remaining"],
                item["daily_doses"],
            )

        results.append(
            {
                "id": item["id"],
                "name": item["name"],
                **result,
            }
        )

    return results


@app.post("/api/doses")
def record_dose(dose: DoseRequest):
    with database() as connection:
        medicine = connection.execute(
            "SELECT id FROM medicines WHERE id = ?",
            (dose.medicine_id,),
        ).fetchone()

        if medicine is None:
            raise HTTPException(
                status_code=404,
                detail="Medicine not found",
            )

        connection.execute(
            """
            INSERT INTO dose_logs
            (medicine_id, status, reason, date)
            VALUES (?, ?, ?, ?)
            """,
            (
                dose.medicine_id,
                dose.status,
                dose.reason,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    return {"message": "Dose recorded successfully"}


@app.get("/api/dose-history")
def get_dose_history():
    with database() as connection:
        rows = connection.execute("""
            SELECT dose_logs.id,
                   dose_logs.medicine_id,
                   medicines.name AS medicine,
                   dose_logs.status,
                   dose_logs.reason,
                   dose_logs.date
            FROM dose_logs
            LEFT JOIN medicines
            ON medicines.id = dose_logs.medicine_id
            ORDER BY dose_logs.id DESC
            """).fetchall()

    return [dict(row) for row in rows]


@app.get("/api/analytics")
def get_analytics():
    with database() as connection:
        rows = connection.execute("""
            SELECT medicines.name AS medicine,
                   dose_logs.status,
                   dose_logs.reason
            FROM dose_logs
            LEFT JOIN medicines
            ON medicines.id = dose_logs.medicine_id
            """).fetchall()

    records = [dict(row) for row in rows]

    return {
        "adherence_percentage": calculate_adherence(records),
        "missed_doses": analyze_missed_doses(records),
    }


@app.get("/api/weekly-adherence")
def get_weekly_adherence():
    today = date.today()
    start_date = today - timedelta(days=6)

    with database() as connection:
        rows = connection.execute(
            """
            SELECT
                date(date) AS day,
                SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) AS taken,
                SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) AS missed
            FROM dose_logs
            WHERE date(date) BETWEEN ? AND ?
            GROUP BY date(date)
        """,
            (start_date.isoformat(), today.isoformat()),
        ).fetchall()

    records = {row["day"]: dict(row) for row in rows}

    days = []

    for offset in range(7):
        current = start_date + timedelta(days=offset)
        record = records.get(current.isoformat(), {})

        taken = record.get("taken", 0) or 0
        missed = record.get("missed", 0) or 0
        total = taken + missed

        percentage = round((taken / total) * 100) if total else 0

        days.append(
            {
                "day": current.strftime("%a"),
                "date": current.isoformat(),
                "taken": taken,
                "missed": missed,
                "adherence": percentage,
            }
        )

    return {"days": days}

@app.get("/api/doctor-report")
def download_doctor_report():
    analytics = get_analytics()
    refill_data = get_refill_status()

    insights = {
        "adherence_percentage": analytics["adherence_percentage"],
        "missed_doses": analytics["missed_doses"],
        "refill": refill_data,
    }

    pdf = generate_doctor_pdf(insights)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="medicare-doctor-report.pdf"'
        },
    )
