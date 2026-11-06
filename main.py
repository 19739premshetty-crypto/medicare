
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib
import secrets
import hmac
from datetime import datetime

app = FastAPI(title="Medication Adherence Backend")


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def connect_db():
    return sqlite3.connect("medicine.db")


# -----------------------------
# CREATE DATABASE TABLES
# -----------------------------

def create_tables():
    db = connect_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        time TEXT NOT NULL
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS dose_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        status TEXT,
        reason TEXT,
        date TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS consents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        caregiver_id INTEGER,
        granted INTEGER DEFAULT 0
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        details TEXT,
        date TEXT
    )
    """)

    db.commit()
    db.close()


create_tables()


# -----------------------------
# AUDIT LOG FUNCTION
# -----------------------------

def add_audit_log(user_id, action, details=""):
    db = connect_db()

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute("""
    INSERT INTO audit_logs (user_id, action, details, date)
    VALUES (?, ?, ?, ?)
    """, (user_id, action, details, date))

    db.commit()
    db.close()


# -----------------------------
# PASSWORD SECURITY
# -----------------------------

def hash_password(password):
    salt = secrets.token_hex(16)

    hashed = hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=16384,
        r=8,
        p=1
    ).hex()

    return salt + ":" + hashed


def check_password(password, stored):
    salt, old_hash = stored.split(":")

    new_hash = hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=16384,
        r=8,
        p=1
    ).hex()

    return hmac.compare_digest(new_hash, old_hash)


# -----------------------------
# REQUEST MODELS
# -----------------------------

class UserRequest(BaseModel):
    username: str
    password: str
    role: str = "patient"


class ConsentRequest(BaseModel):
    patient_id: int
    caregiver_id: int
    granted: bool


# -----------------------------
# HOME
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "Medication Backend Running!"
    }


# -----------------------------
# REGISTER USER
# -----------------------------

@app.post("/register")
def register(data: UserRequest):

    if not data.username or not data.password:
        raise HTTPException(400, "Enter username and password")

    if len(data.password) < 8:
        raise HTTPException(
            400,
            "Password must be at least 8 characters"
        )

    if data.role not in ["patient", "caregiver", "doctor"]:
        raise HTTPException(400, "Invalid role")

    db = connect_db()

    try:
        db.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, (
            data.username,
            hash_password(data.password),
            data.role
        ))

        db.commit()

        user = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (data.username,)
        ).fetchone()

        add_audit_log(user[0], "REGISTER", "New user registered")

        return {
            "message": "User registered successfully!"
        }

    except sqlite3.IntegrityError:
        raise HTTPException(400, "Username already exists")

    finally:
        db.close()


# -----------------------------
# LOGIN USER
# -----------------------------

@app.post("/login")
def login(data: UserRequest):

    db = connect_db()

    user = db.execute("""
    SELECT * FROM users WHERE username = ?
    """, (data.username,)).fetchone()

    db.close()

    if user is None or not check_password(data.password, user[2]):
        raise HTTPException(401, "Invalid username or password")

    add_audit_log(user[0], "LOGIN", "User logged in")

    return {
        "message": "Login successful!",
        "user_id": user[0],
        "username": user[1],
        "role": user[3]
    }


# -----------------------------
# ADD MEDICINE
# -----------------------------

@app.post("/add-medicine")
def add_medicine(name: str, dosage: str, time: str):

    db = connect_db()

    db.execute("""
    INSERT INTO medicines (name, dosage, time)
    VALUES (?, ?, ?)
    """, (name, dosage, time))

    db.commit()
    db.close()

    add_audit_log(None, "ADD_MEDICINE", name)

    return {
        "message": "Medicine added successfully!"
    }


# -----------------------------
# VIEW MEDICINES
# -----------------------------

@app.get("/medicines")
def get_medicines():

    db = connect_db()

    db.row_factory = sqlite3.Row

    medicines = db.execute(
        "SELECT * FROM medicines"
    ).fetchall()

    result = [dict(row) for row in medicines]

    db.close()

    return {
        "medicines": result
    }


# -----------------------------
# DELETE MEDICINE
# -----------------------------

@app.delete("/delete-medicine/{medicine_id}")
def delete_medicine(medicine_id: int):

    db = connect_db()

    cursor = db.execute(
        "DELETE FROM medicines WHERE id = ?",
        (medicine_id,)
    )

    db.commit()
    db.close()

    if cursor.rowcount == 0:
        raise HTTPException(404, "Medicine not found")

    add_audit_log(None, "DELETE_MEDICINE", str(medicine_id))

    return {
        "message": "Medicine deleted successfully!"
    }


# -----------------------------
# RECORD DOSE
# -----------------------------

@app.post("/record-dose")
def record_dose(
    medicine_id: int,
    status: str,
    reason: str = ""
):

    if status not in ["taken", "missed"]:
        raise HTTPException(
            400,
            "Status must be taken or missed"
        )

    db = connect_db()

    medicine = db.execute(
        "SELECT id FROM medicines WHERE id = ?",
        (medicine_id,)
    ).fetchone()

    if medicine is None:
        db.close()
        raise HTTPException(404, "Medicine not found")

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute("""
    INSERT INTO dose_logs (medicine_id, status, reason, date)
    VALUES (?, ?, ?, ?)
    """, (medicine_id, status, reason, date))

    db.commit()
    db.close()

    add_audit_log(
        None,
        "RECORD_DOSE",
        f"Medicine {medicine_id}: {status}"
    )

    return {
        "message": "Dose recorded successfully!",
        "status": status
    }


# -----------------------------
# VIEW DOSE HISTORY
# -----------------------------

@app.get("/dose-history")
def dose_history():

    db = connect_db()

    db.row_factory = sqlite3.Row

    records = db.execute("""
    SELECT * FROM dose_logs
    ORDER BY id DESC
    """).fetchall()

    result = [dict(row) for row in records]

    db.close()

    return {
        "dose_history": result
    }


# -----------------------------
# MANAGE CAREGIVER CONSENT
# -----------------------------

@app.post("/consent")
def manage_consent(data: ConsentRequest):

    db = connect_db()

    patient = db.execute("""
    SELECT id FROM users
    WHERE id = ? AND role = 'patient'
    """, (data.patient_id,)).fetchone()

    caregiver = db.execute("""
    SELECT id FROM users
    WHERE id = ? AND role = 'caregiver'
    """, (data.caregiver_id,)).fetchone()

    if not patient or not caregiver:
        db.close()
        raise HTTPException(
            400,
            "Invalid patient or caregiver ID"
        )

    existing = db.execute("""
    SELECT id FROM consents
    WHERE patient_id = ? AND caregiver_id = ?
    """, (data.patient_id, data.caregiver_id)).fetchone()

    if existing:
        db.execute("""
        UPDATE consents
        SET granted = ?
        WHERE id = ?
        """, (int(data.granted), existing[0]))

    else:
        db.execute("""
        INSERT INTO consents
        (patient_id, caregiver_id, granted)
        VALUES (?, ?, ?)
        """, (
            data.patient_id,
            data.caregiver_id,
            int(data.granted)
        ))

    db.commit()
    db.close()

    add_audit_log(
        data.patient_id,
        "UPDATE_CONSENT",
        f"Caregiver {data.caregiver_id}: {data.granted}"
    )

    return {
        "message": "Consent updated successfully!",
        "granted": data.granted
    }


# -----------------------------
# VIEW CONSENTS
# -----------------------------

@app.get("/consent")
def view_consent():

    db = connect_db()

    db.row_factory = sqlite3.Row

    records = db.execute(
        "SELECT * FROM consents"
    ).fetchall()

    result = [dict(row) for row in records]

    db.close()

    return {
        "consents": result
    }


# -----------------------------
# VIEW AUDIT LOGS
# -----------------------------

@app.get("/audit-logs")
def view_audit_logs():

    db = connect_db()

    db.row_factory = sqlite3.Row

    records = db.execute("""
    SELECT * FROM audit_logs
    ORDER BY id DESC
    """).fetchall()

    result = [dict(row) for row in records]

    db.close()

    return {
        "audit_logs": result
    }
