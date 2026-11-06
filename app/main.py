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

from app.database import get_connection
from app.analytics import (
    calculate_adherence,
    analyze_missed_doses,
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
