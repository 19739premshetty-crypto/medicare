# Medication Adherence Platform

A prototype for medication tracking, reminders and adherence analytics.

## Tech Stack
- Python
- FastAPI
- SQLite
- HTML, CSS and JavaScript
- ReportLab

## Setup

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Run

python3 -m uvicorn app.main:app --reload

Dashboard: http://127.0.0.1:8000/dashboard
API Docs: http://127.0.0.1:8000/docs

Note: Uses demo data. Not intended for real patient records.
