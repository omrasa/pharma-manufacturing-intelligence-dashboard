from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():

    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


@app.get("/")
def home():
    return {
        "message": "Pharma Manufacturing Intelligence API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/batches")
def get_batches():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM batches ORDER BY id;")
    batches = cursor.fetchall()

    cursor.close()
    connection.close()

    return batches


@app.get("/risk")
def get_risk():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM batches ORDER BY id;")
    batches = cursor.fetchall()

    risk_results = []

    for batch in batches:

        if (
            batch["temperature"] > 40
            and batch["yield_percent"] < 90
        ):
            risk = "HIGH RISK"

        elif (
            batch["pressure"] > 2
            or batch["yield_percent"] < 90
        ):
            risk = "MEDIUM RISK"

        else:
            risk = "LOW RISK"

        risk_results.append({
            "batch_number": batch["batch_number"],
            "risk_level": risk
        })

    cursor.close()
    connection.close()

    return risk_results
@app.get("/auto-deviations")
def get_auto_deviations():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM batches ORDER BY id;")
    batches = cursor.fetchall()

    deviations = []

    for batch in batches:

        if batch["temperature"] > 40:
            deviations.append({
                "batch_number": batch["batch_number"],
                "issue_type": "High Temperature",
                "severity": "Critical",
                "description": "Temperature exceeded acceptable process range"
            })

        if batch["yield_percent"] < 90:
            deviations.append({
                "batch_number": batch["batch_number"],
                "issue_type": "Low Yield",
                "severity": "High",
                "description": "Yield dropped below target threshold"
            })

        if batch["pressure"] > 2:
            deviations.append({
                "batch_number": batch["batch_number"],
                "issue_type": "High Pressure",
                "severity": "Medium",
                "description": "Pressure exceeded normal operating range"
            })

    cursor.close()
    connection.close()

    return deviations
@app.get("/risk-summary")
def risk_summary():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM batches ORDER BY id;")
    batches = cursor.fetchall()

    high_risk = 0
    medium_risk = 0
    low_risk = 0

    for batch in batches:

        if batch["temperature"] > 42 and batch["yield_percent"] < 85:
            high_risk += 1

        elif batch["pressure"] > 2.8 or batch["yield_percent"] < 90:
            medium_risk += 1

        else:
            low_risk += 1

    cursor.close()
    connection.close()

    return {
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk
    }