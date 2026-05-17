import os
import sqlite3
import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None



st.set_page_config(
    page_title="Pharma Manufacturing Intelligence",
    page_icon="🏭",
    layout="wide",
)


# ============================================================
# Database Audit Trail
# ============================================================

DATABASE_FILE = "audit_trail.db"


def initialize_audit_database():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            role TEXT,
            event TEXT,
            batch TEXT,
            details TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def log_database_event(username, role, event, batch, details):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO audit_events (
            timestamp,
            username,
            role,
            event,
            batch,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username,
            role,
            event,
            batch,
            details,
        ),
    )

    connection.commit()
    connection.close()


def load_database_audit_events():
    connection = sqlite3.connect(DATABASE_FILE)

    audit_df = pd.read_sql_query(
        "SELECT * FROM audit_events ORDER BY id DESC",
        connection,
    )

    connection.close()

    return audit_df



load_dotenv()
initialize_audit_database()

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

if "rag_chat_history" not in st.session_state:
    st.session_state.rag_chat_history = []

# ============================================================
# Simple Enterprise Authentication
# ============================================================

USERS = {
    "admin": {
        "password": "admin123",
        "role": "Admin",
        "name": "Admin User",
    },
    "qa": {
        "password": "qa123",
        "role": "QA Manager",
        "name": "QA Reviewer",
    },
    "engineer": {
        "password": "eng123",
        "role": "Process Engineer",
        "name": "Process Engineer",
    },
    "operator": {
        "password": "op123",
        "role": "Manufacturing Operator",
        "name": "Manufacturing Operator",
    },
}

ROLE_ACCESS = {
    "Admin": "Full platform access",
    "QA Manager": "QA/CAPA, reports, deviation review, audit trail",
    "Process Engineer": "Trends, equipment monitoring, live monitoring, batch comparison",
    "Manufacturing Operator": "Overview, risk alerts, live monitoring",
}


def login_user(username, password):
    user = USERS.get(username)

    if user and user["password"] == password:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_role = user["role"]
        st.session_state.user_name = user["name"]

        try:
            log_database_event(
                username=username,
                role=user["role"],
                event="User login",
                batch="Platform",
                details="Successful login",
            )
        except Exception:
            pass

        return True

    return False


def logout_user():
    try:
        log_database_event(
            username=st.session_state.get("username", "unknown"),
            role=st.session_state.get("user_role", "unknown"),
            event="User logout",
            batch="Platform",
            details="User logged out",
        )
    except Exception:
        pass

    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_name = None


def can_access_tab(tab_name):
    role = st.session_state.get("user_role", "")

    if role == "Admin":
        return True

    qa_tabs = [
        "Overview",
        "Risk & Alerts",
        "Deviation Management",
        "QA / CAPA",
        "Reports",
        "RAG QA Assistant",
        "Audit Trail",
        "AI Deviation Report",
    ]

    engineer_tabs = [
        "Overview",
        "Risk & Alerts",
        "Batch Comparison",
        "AI Trend Prediction",
        "Live Manufacturing Monitor",
        "Equipment Monitoring",
    ]

    operator_tabs = [
        "Overview",
        "Risk & Alerts",
        "Live Manufacturing Monitor",
    ]

    if role == "QA Manager":
        return tab_name in qa_tabs

    if role == "Process Engineer":
        return tab_name in engineer_tabs

    if role == "Manufacturing Operator":
        return tab_name in operator_tabs

    return False


def render_access_denied(tab_name):
    st.warning(
        f"Access denied for {tab_name}. Your current role is "
        f"{st.session_state.get('user_role', 'Unknown')}."
    )

    st.info(
        "Switch to an Admin account if you want to test full platform access."
    )


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None


def render_login_screen():
    st.title("🏭 Pharma Manufacturing Intelligence Platform")
    st.subheader("Enterprise Login")

    st.info(
        "Demo login system for role-based pharma manufacturing workflows."
    )

    login_col1, login_col2 = st.columns([1, 1])

    with login_col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(username, password):
                st.success("Login successful. Loading dashboard...")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with login_col2:
        st.markdown("### Demo Accounts")

        demo_accounts = pd.DataFrame(
            [
                {"Username": "admin", "Password": "admin123", "Role": "Admin"},
                {"Username": "qa", "Password": "qa123", "Role": "QA Manager"},
                {"Username": "engineer", "Password": "eng123", "Role": "Process Engineer"},
                {"Username": "operator", "Password": "op123", "Role": "Manufacturing Operator"},
            ]
        )

        st.dataframe(
            demo_accounts,
            hide_index=True,
        )

    st.markdown("---")

    st.caption(
        "Demo authentication only. For production, use hashed passwords, OAuth, SSO, or enterprise identity management."
    )


if not st.session_state.authenticated:
    render_login_screen()
    st.stop()


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100% !important;
    }
    .main { background-color: #f7f9fc; }
    h1, h2, h3 { color: #1f2937; }
    [data-testid="stSidebar"] { background-color: #eef2f7; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
    .stAlert { border-radius: 12px; }
    div[data-testid="stDataFrame"] { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

API_URL = "http://127.0.0.1:8000/batches"
RISK_URL = "http://127.0.0.1:8000/risk-summary"
DEVIATION_URL = "http://127.0.0.1:8000/auto-deviations"


def load_api_data(url, fallback):
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return fallback


def calculate_critical_alerts(dataframe):
    if dataframe.empty:
        return 0
    return len(dataframe[(dataframe["temperature"] > 40) & (dataframe["yield_percent"] < 90)])


def get_risky_batches(dataframe):
    if dataframe.empty:
        return dataframe
    return dataframe[
        (dataframe["temperature"] > 40)
        | (dataframe["pressure"] > 2)
        | (dataframe["yield_percent"] < 90)
    ]


def calculate_risk_score(row):
    risk_score = 0
    if row["temperature"] > 40:
        risk_score += 40
    if row["yield_percent"] < 90:
        risk_score += 35
    if row["pressure"] > 2:
        risk_score += 25
    return min(risk_score, 100)


def calculate_health_score(row):
    health_score = 100
    if row["temperature"] > 40:
        health_score -= 25
    if row["pressure"] > 2:
        health_score -= 20
    if row["yield_percent"] < 90:
        health_score -= 30
    return max(health_score, 0)


def generate_release_recommendation(batch):
    risk_score = 0
    reasons = []
    if batch["yield_percent"] < 80:
        risk_score += 30
        reasons.append("Low batch yield detected")
    if batch["pressure"] > 2.5:
        risk_score += 25
        reasons.append("High reactor pressure")
    if batch["temperature"] > 35:
        risk_score += 20
        reasons.append("Elevated reactor temperature")
    if batch["status"] == "Pending Review":
        risk_score += 25
        reasons.append("Batch still under QA review")
    if risk_score >= 70:
        decision = "HOLD"
    elif risk_score >= 40:
        decision = "INVESTIGATE"
    else:
        decision = "RELEASE"
    return {"decision": decision, "risk_score": min(risk_score, 100), "reasons": reasons}


def classify_deviation_severity(ai_risk_score):
    if ai_risk_score >= 70:
        return "Critical"
    if ai_risk_score >= 40:
        return "Major"
    return "Minor"


def generate_capa_actions(ai_risk_score):
    if ai_risk_score >= 70:
        return [
            "Open formal deviation investigation",
            "Escalate to QA manager immediately",
            "Quarantine manufacturing batch",
            "Review reactor temperature calibration",
            "Perform root-cause investigation",
            "Initiate corrective and preventive action process",
        ]
    if ai_risk_score >= 40:
        return [
            "Perform QA review before release",
            "Monitor reactor pressure trend",
            "Review batch manufacturing records",
            "Increase sampling frequency",
            "Document process deviation",
        ]
    return ["Continue routine batch monitoring", "No major CAPA action required"]


def compare_two_batches(batch_a, batch_b):
    release_a = generate_release_recommendation(batch_a)
    release_b = generate_release_recommendation(batch_b)
    temperature_difference = abs(batch_a["temperature"] - batch_b["temperature"])
    pressure_difference = abs(batch_a["pressure"] - batch_b["pressure"])
    yield_difference = abs(batch_a["yield_percent"] - batch_b["yield_percent"])
    root_cause_notes = []
    if temperature_difference > 5:
        root_cause_notes.append("Large temperature variation detected between batches.")
    if pressure_difference > 0.5:
        root_cause_notes.append("Pressure instability observed across batches.")
    if yield_difference > 10:
        root_cause_notes.append("Major yield deviation detected.")
    if not root_cause_notes:
        root_cause_notes.append("No major manufacturing deviation detected between the selected batches.")
    return {
        "temperature_difference": temperature_difference,
        "pressure_difference": pressure_difference,
        "yield_difference": yield_difference,
        "batch_a_release": release_a["decision"],
        "batch_b_release": release_b["decision"],
        "root_cause_notes": root_cause_notes,
    }



def generate_ai_deviation_report(batch):
    ai_risk_score = calculate_risk_score(batch)
    release_result = generate_release_recommendation(batch)
    severity_level = classify_deviation_severity(ai_risk_score)
    capa_actions = generate_capa_actions(ai_risk_score)

    detected_issues = []

    if batch["temperature"] > 40:
        detected_issues.append(
            "High temperature deviation detected, suggesting possible cooling instability or temperature control drift."
        )

    if batch["yield_percent"] < 90:
        detected_issues.append(
            "Low yield deviation detected, suggesting possible raw material variability, incomplete reaction, or product loss."
        )

    if batch["pressure"] > 2:
        detected_issues.append(
            "High pressure deviation detected, suggesting possible flow restriction, valve issue, or reactor blockage."
        )

    if not detected_issues:
        detected_issues.append(
            "No major process deviation detected based on the current thresholds."
        )

    issue_text = "\n".join([f"- {issue}" for issue in detected_issues])
    capa_text = "\n".join([f"- {action}" for action in capa_actions])

    reason_text = "\n".join(
        [f"- {reason}" for reason in release_result["reasons"]]
    )

    if not reason_text:
        reason_text = "- No major release-risk reason detected"

    report = f"""
AI-Generated Deviation Report

Batch Number:
{batch["batch_number"]}

Product Name:
{batch["product_name"]}

Process Parameters:
- Temperature: {batch["temperature"]} °C
- Pressure: {batch["pressure"]}
- Yield: {batch["yield_percent"]}%
- Status: {batch["status"]}

Deviation Severity:
{severity_level}

AI Risk Score:
{ai_risk_score}/100

AI Release Recommendation:
{release_result["decision"]}

Detected Issues:
{issue_text}

Release Recommendation Reasons:
{reason_text}

Recommended CAPA Actions:
{capa_text}

Executive QA Summary:
Batch {batch["batch_number"]} was assessed using manufacturing process parameters and AI-assisted risk logic.
The current deviation severity is classified as {severity_level}, with an AI risk score of {ai_risk_score}/100.
The recommended QA disposition is {release_result["decision"]}. QA should review the listed CAPA actions and document the final batch disposition according to GMP procedures.
"""

    return report



def predict_future_risk(row):
    predicted_risk = calculate_risk_score(row)

    if row["temperature"] > 42:
        predicted_risk += 10

    if row["yield_percent"] < 85:
        predicted_risk += 10

    if row["pressure"] > 2.8:
        predicted_risk += 10

    return min(predicted_risk, 100)


def classify_future_risk(score):
    if score >= 70:
        return "Critical"

    if score >= 40:
        return "Medium"

    return "Low"


def generate_trend_summary(row, future_risk):
    summary = []

    if row["temperature"] > 40:
        summary.append(
            "Elevated temperature trend may increase future batch instability."
        )

    if row["yield_percent"] < 90:
        summary.append(
            "Yield reduction trend indicates possible process efficiency loss."
        )

    if row["pressure"] > 2:
        summary.append(
            "Pressure trend indicates potential reactor flow instability."
        )

    if future_risk >= 70:
        summary.append(
            "AI predicts high probability of future manufacturing deviation."
        )

    if not summary:
        summary.append(
            "Manufacturing trend currently stable."
        )

    return summary


def calculate_equipment_health(row):
    health_score = 100

    if row["temperature"] > 40:
        health_score -= 25

    if row["pressure"] > 2:
        health_score -= 25

    if row["yield_percent"] < 90:
        health_score -= 15

    if row["status"] == "Pending Review":
        health_score -= 10

    return max(health_score, 0)


def classify_equipment_health(health_score):
    if health_score >= 80:
        return "Healthy"

    if health_score >= 60:
        return "Monitor"

    if health_score >= 40:
        return "Maintenance Required"

    return "Critical Maintenance"


def predict_equipment_failure_probability(row):
    health_score = calculate_equipment_health(row)
    failure_probability = 100 - health_score

    if row["temperature"] > 42:
        failure_probability += 10

    if row["pressure"] > 2.8:
        failure_probability += 10

    return min(failure_probability, 100)


def generate_maintenance_recommendations(row):
    recommendations = []

    if row["temperature"] > 40:
        recommendations.append(
            "Inspect reactor cooling loop and verify temperature sensor calibration."
        )

    if row["pressure"] > 2:
        recommendations.append(
            "Inspect pressure control valve, flow path, and downstream restrictions."
        )

    if row["yield_percent"] < 90:
        recommendations.append(
            "Review process efficiency, transfer losses, and purification equipment performance."
        )

    if not recommendations:
        recommendations.append(
            "Continue routine preventive maintenance and standard equipment monitoring."
        )

    return recommendations



def simulate_live_sensor_values(row):
    simulated_temperature = round(row["temperature"] + random.uniform(-0.8, 0.8), 2)
    simulated_pressure = round(row["pressure"] + random.uniform(-0.15, 0.15), 2)
    simulated_yield = round(row["yield_percent"] + random.uniform(-1.2, 1.2), 2)

    return {
        "batch_number": row["batch_number"],
        "temperature": simulated_temperature,
        "pressure": max(simulated_pressure, 0),
        "yield_percent": max(min(simulated_yield, 100), 0),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


def classify_live_alert(sensor_values):
    alerts = []

    if sensor_values["temperature"] > 40:
        alerts.append({
            "level": "Critical",
            "message": f"High live reactor temperature detected: {sensor_values['temperature']} °C",
        })

    if sensor_values["pressure"] > 2:
        alerts.append({
            "level": "Warning",
            "message": f"Elevated live reactor pressure detected: {sensor_values['pressure']}",
        })

    if sensor_values["yield_percent"] < 90:
        alerts.append({
            "level": "Warning",
            "message": f"Live yield drift detected: {sensor_values['yield_percent']}%",
        })

    if not alerts:
        alerts.append({
            "level": "Normal",
            "message": "Live reactor conditions are within expected operating range.",
        })

    return alerts


def calculate_live_risk(sensor_values):
    live_risk = 0

    if sensor_values["temperature"] > 40:
        live_risk += 40

    if sensor_values["pressure"] > 2:
        live_risk += 25

    if sensor_values["yield_percent"] < 90:
        live_risk += 35

    return min(live_risk, 100)



def calculate_platform_maturity_score():
    score = 0

    completed_capabilities = {
        "PostgreSQL data layer": True,
        "FastAPI backend": True,
        "Streamlit frontend": True,
        "Interactive Plotly charts": True,
        "AI risk scoring": True,
        "QA/CAPA workflow": True,
        "RAG knowledge assistant": True,
        "PDF reporting": True,
        "Audit trail": True,
        "Role-based login": True,
        "Live monitoring": True,
        "Equipment monitoring": True,
    }

    for is_complete in completed_capabilities.values():
        if is_complete:
            score += 8

    return min(score, 100), completed_capabilities


def generate_recruiter_demo_script():
    return """
Demo Flow for Recruiters / Hiring Managers

1. Login as admin / admin123.
2. Open the Overview tab to show manufacturing KPIs and Plotly charts.
3. Open Risk & Alerts to show AI-assisted batch risk detection.
4. Open QA / CAPA to show root-cause analysis, CAPA recommendations, and PDF report generation.
5. Open RAG QA Assistant to show knowledge-base grounded QA responses.
6. Open Batch Comparison to compare two manufacturing batches.
7. Open AI Deviation Report to generate a deviation investigation summary.
8. Open AI Trend Prediction to show predictive risk forecasting.
9. Open Live Manufacturing Monitor to show simulated real-time manufacturing intelligence.
10. Open Equipment Monitoring to show predictive maintenance recommendations.
11. Open Audit Trail to show traceability of AI and QA actions.

Key message:
This is not only a dashboard. It is a pharma manufacturing intelligence platform combining data engineering, AI, QA workflows, RAG, audit traceability, and enterprise product thinking.
"""


def generate_cv_pitch():
    return """
Portfolio Pitch

I built an AI-assisted Pharma Manufacturing Intelligence Platform using Streamlit, FastAPI, PostgreSQL, Plotly, OpenAI, LangChain, ChromaDB, ReportLab, and Docker.

The platform supports batch monitoring, deviation detection, QA/CAPA workflows, RAG-based knowledge assistance, AI deviation reporting, predictive maintenance, live manufacturing monitoring, audit trail logging, and role-based access.

This project demonstrates my ability to bridge pharma process understanding, data analytics, AI workflows, backend/frontend integration, and business-oriented product thinking.
"""


def generate_root_cause_investigation(batch):
    risk_score = calculate_risk_score(batch)
    release_result = generate_release_recommendation(batch)

    probable_root_causes = []
    contributing_parameters = []
    corrective_actions = []
    preventive_actions = []

    if batch["temperature"] > 40:
        probable_root_causes.append("Reactor cooling instability or temperature control drift")
        contributing_parameters.append(f"Temperature above control threshold: {batch['temperature']} °C")
        corrective_actions.append("Verify reactor temperature probe calibration and inspect cooling-loop performance.")
        preventive_actions.append("Add routine temperature controller verification to preventive maintenance schedule.")

    if batch["pressure"] > 2:
        probable_root_causes.append("Pressure control deviation, flow restriction, or valve performance issue")
        contributing_parameters.append(f"Pressure above expected operating range: {batch['pressure']}")
        corrective_actions.append("Inspect pressure valve, reactor venting pathway, and downstream restriction points.")
        preventive_actions.append("Trend pressure-control performance across future batches and define alert limits.")

    if batch["yield_percent"] < 90:
        probable_root_causes.append("Reduced process efficiency, raw material variability, incomplete conversion, or product loss")
        contributing_parameters.append(f"Yield below expected target: {batch['yield_percent']}%")
        corrective_actions.append("Review batch manufacturing record, raw material COA, reaction completion data, and purification losses.")
        preventive_actions.append("Introduce additional in-process yield checkpoints and supplier/material trend review.")

    if batch["status"] == "Pending Review":
        contributing_parameters.append("Batch is still pending QA review")
        corrective_actions.append("Complete QA batch record review before final disposition.")

    if not probable_root_causes:
        probable_root_causes.append("No major process-related root cause identified from current batch parameters")
        contributing_parameters.append("Temperature, pressure, and yield are within expected operating limits")
        corrective_actions.append("Continue routine QA review and standard GMP documentation.")
        preventive_actions.append("Continue standard monitoring and periodic process trend review.")

    confidence_score = min(55 + risk_score, 95)

    if risk_score >= 70:
        investigation_priority = "High"
    elif risk_score >= 40:
        investigation_priority = "Medium"
    else:
        investigation_priority = "Low"

    return {
        "batch_number": batch["batch_number"],
        "product_name": batch["product_name"],
        "risk_score": risk_score,
        "release_decision": release_result["decision"],
        "investigation_priority": investigation_priority,
        "confidence_score": confidence_score,
        "probable_root_causes": probable_root_causes,
        "contributing_parameters": contributing_parameters,
        "corrective_actions": corrective_actions,
        "preventive_actions": preventive_actions,
    }


def format_root_cause_report(investigation):
    root_causes = "\n".join([f"- {item}" for item in investigation["probable_root_causes"]])
    contributing_parameters = "\n".join([f"- {item}" for item in investigation["contributing_parameters"]])
    corrective_actions = "\n".join([f"- {item}" for item in investigation["corrective_actions"]])
    preventive_actions = "\n".join([f"- {item}" for item in investigation["preventive_actions"]])

    return f"""
AI Root Cause Investigation Report

Batch Number:
{investigation["batch_number"]}

Product:
{investigation["product_name"]}

Investigation Priority:
{investigation["investigation_priority"]}

AI Confidence:
{investigation["confidence_score"]}%

AI Risk Score:
{investigation["risk_score"]}/100

Release Recommendation:
{investigation["release_decision"]}

Probable Root Cause(s):
{root_causes}

Contributing Process Parameter(s):
{contributing_parameters}

Recommended Corrective Action(s):
{corrective_actions}

Recommended Preventive Action(s):
{preventive_actions}

QA Investigation Summary:
AI-assisted analysis indicates that batch {investigation["batch_number"]} should be reviewed with focus on the listed probable root causes and contributing process parameters. QA should verify the batch manufacturing record, process trends, equipment status, and material records before final batch disposition.
"""





# ============================================================
# Batch Genealogy Helper Functions
# ============================================================

def generate_batch_genealogy(batch):
    batch_number = batch["batch_number"]

    genealogy = {
        "batch_number": batch_number,
        "raw_material_lot": f"RM-2026-{batch_number[-3:]}",
        "supplier": "Nordic BioChem Supplier",
        "operator": "Sarah Jensen",
        "reactor_id": f"RX-{200 + int(batch_number[-1])}",
        "cleaning_cycle": f"CLN-{800 + int(batch_number[-1])}",
        "previous_batch": f"B-{int(batch_number[2:]) - 1}",
        "packaging_lot": f"PK-{500 + int(batch_number[-1])}",
        "traceability_score": 98,
        "contamination_risk": "Low",
        "documentation_status": "Complete",
    }

    return genealogy



# ============================================================
# AI Process Optimization Helper Functions
# ============================================================

def generate_process_optimization(batch):
    current_yield = batch["yield_percent"]
    current_temperature = batch["temperature"]
    current_pressure = batch["pressure"]

    target_temperature = 37.0
    target_pressure = 1.8
    target_yield = 94.0

    optimization_actions = []

    if current_temperature > 40:
        optimization_actions.append(
            "Reduce reactor temperature setpoint and verify cooling-loop performance."
        )
    elif current_temperature < 35:
        optimization_actions.append(
            "Review whether reactor temperature is below optimal process window."
        )
    else:
        optimization_actions.append(
            "Temperature is close to the recommended process window."
        )

    if current_pressure > 2:
        optimization_actions.append(
            "Optimize pressure control and inspect for flow restriction or valve instability."
        )
    else:
        optimization_actions.append(
            "Pressure profile is within acceptable operating range."
        )

    if current_yield < 90:
        optimization_actions.append(
            "Investigate reaction completion, raw material variability, and purification losses."
        )
    else:
        optimization_actions.append(
            "Yield performance is acceptable; continue routine process monitoring."
        )

    yield_improvement_potential = max(target_yield - current_yield, 0)
    temperature_gap = abs(current_temperature - target_temperature)
    pressure_gap = abs(current_pressure - target_pressure)

    optimization_score = 100
    optimization_score -= min(temperature_gap * 5, 30)
    optimization_score -= min(pressure_gap * 10, 25)

    if current_yield < 90:
        optimization_score -= 25

    optimization_score = max(int(optimization_score), 0)

    if optimization_score >= 80:
        optimization_category = "Optimized"
    elif optimization_score >= 60:
        optimization_category = "Improvement Opportunity"
    else:
        optimization_category = "Optimization Required"

    energy_saving_opportunity = "Low"

    if current_temperature > 40 or current_pressure > 2.5:
        energy_saving_opportunity = "High"
    elif current_temperature > 38 or current_pressure > 2:
        energy_saving_opportunity = "Medium"

    confidence_score = min(65 + calculate_risk_score(batch), 95)

    return {
        "batch_number": batch["batch_number"],
        "product_name": batch["product_name"],
        "current_temperature": current_temperature,
        "current_pressure": current_pressure,
        "current_yield": current_yield,
        "target_temperature": target_temperature,
        "target_pressure": target_pressure,
        "target_yield": target_yield,
        "yield_improvement_potential": round(yield_improvement_potential, 2),
        "optimization_score": optimization_score,
        "optimization_category": optimization_category,
        "energy_saving_opportunity": energy_saving_opportunity,
        "confidence_score": confidence_score,
        "optimization_actions": optimization_actions,
    }


def format_process_optimization_report(optimization):
    actions_text = "\n".join(
        [f"- {action}" for action in optimization["optimization_actions"]]
    )

    report = f"""
AI Process Optimization Report

Batch Number:
{optimization["batch_number"]}

Product:
{optimization["product_name"]}

Current Process Parameters:
- Temperature: {optimization["current_temperature"]} °C
- Pressure: {optimization["current_pressure"]}
- Yield: {optimization["current_yield"]}%

Recommended Target Parameters:
- Target Temperature: {optimization["target_temperature"]} °C
- Target Pressure: {optimization["target_pressure"]}
- Target Yield: {optimization["target_yield"]}%

Optimization Score:
{optimization["optimization_score"]}/100

Optimization Category:
{optimization["optimization_category"]}

Yield Improvement Potential:
{optimization["yield_improvement_potential"]}%

Energy Saving Opportunity:
{optimization["energy_saving_opportunity"]}

AI Confidence:
{optimization["confidence_score"]}%

Recommended Process Optimization Actions:
{actions_text}

Executive Optimization Summary:
AI-assisted process optimization suggests that batch {optimization["batch_number"]} should be reviewed for parameter tuning opportunities. The platform recommends focusing on temperature control, pressure stability, and yield improvement actions to improve manufacturing consistency and process efficiency.
"""

    return report




# ============================================================
# AI Batch Failure Prediction Helper Functions
# ============================================================

def generate_batch_failure_prediction(batch):
    temperature = batch["temperature"]
    pressure = batch["pressure"]
    yield_percent = batch["yield_percent"]
    status = batch["status"]

    failure_probability = 5
    drift_factors = []
    preventive_actions = []

    if temperature > 40:
        failure_probability += 30
        drift_factors.append(
            f"Temperature above critical process threshold: {temperature} °C"
        )
        preventive_actions.append(
            "Stabilize reactor cooling and verify temperature probe calibration."
        )
    elif temperature > 38:
        failure_probability += 15
        drift_factors.append(
            f"Temperature approaching upper process window: {temperature} °C"
        )
        preventive_actions.append(
            "Increase monitoring frequency for reactor temperature trend."
        )

    if pressure > 2.5:
        failure_probability += 25
        drift_factors.append(
            f"Pressure above high-risk control limit: {pressure}"
        )
        preventive_actions.append(
            "Inspect pressure valve, venting path, and potential flow restrictions."
        )
    elif pressure > 2:
        failure_probability += 15
        drift_factors.append(
            f"Pressure above normal operating range: {pressure}"
        )
        preventive_actions.append(
            "Monitor pressure stability and verify valve-control response."
        )

    if yield_percent < 85:
        failure_probability += 30
        drift_factors.append(
            f"Yield significantly below target: {yield_percent}%"
        )
        preventive_actions.append(
            "Review raw material quality, reaction conversion, and purification losses."
        )
    elif yield_percent < 90:
        failure_probability += 20
        drift_factors.append(
            f"Yield below expected process target: {yield_percent}%"
        )
        preventive_actions.append(
            "Perform early QA review of batch manufacturing record and in-process controls."
        )

    if status == "Pending Review":
        failure_probability += 10
        drift_factors.append(
            "Batch status is pending QA review"
        )
        preventive_actions.append(
            "Complete QA review before batch release decision."
        )

    failure_probability = min(failure_probability, 95)

    predicted_yield_loss = max(round(94 - yield_percent, 2), 0)

    if failure_probability >= 70:
        failure_risk_level = "High"
        release_risk = "Likely Hold / Investigation"
    elif failure_probability >= 40:
        failure_risk_level = "Medium"
        release_risk = "QA Review Recommended"
    else:
        failure_risk_level = "Low"
        release_risk = "Likely Release"

    if not drift_factors:
        drift_factors.append(
            "No significant process drift detected from current batch parameters."
        )

    if not preventive_actions:
        preventive_actions.append(
            "Continue routine process monitoring and standard QA documentation."
        )

    ai_confidence = min(60 + calculate_risk_score(batch), 95)

    return {
        "batch_number": batch["batch_number"],
        "product_name": batch["product_name"],
        "failure_probability": failure_probability,
        "failure_risk_level": failure_risk_level,
        "release_risk": release_risk,
        "predicted_yield_loss": predicted_yield_loss,
        "ai_confidence": ai_confidence,
        "drift_factors": drift_factors,
        "preventive_actions": preventive_actions,
    }


def format_batch_failure_prediction_report(prediction):
    drift_text = "\n".join(
        [f"- {factor}" for factor in prediction["drift_factors"]]
    )

    action_text = "\n".join(
        [f"- {action}" for action in prediction["preventive_actions"]]
    )

    report = f"""
AI Batch Failure Prediction Report

Batch Number:
{prediction["batch_number"]}

Product:
{prediction["product_name"]}

Predicted Failure Probability:
{prediction["failure_probability"]}%

Failure Risk Level:
{prediction["failure_risk_level"]}

Predicted Release Risk:
{prediction["release_risk"]}

Predicted Yield Loss:
{prediction["predicted_yield_loss"]}%

AI Confidence:
{prediction["ai_confidence"]}%

Detected Process Drift Factor(s):
{drift_text}

Recommended Preventive Action(s):
{action_text}

Executive Prediction Summary:
AI-assisted prediction indicates that batch {prediction["batch_number"]} has a {prediction["failure_probability"]}% predicted failure probability. The recommended preventive actions should be reviewed by QA and process engineering before final batch disposition.
"""

    return report




# ============================================================
# AI Manufacturing Copilot Helper Functions
# ============================================================

def generate_copilot_response(user_prompt, batch_data=None):

    prompt = user_prompt.lower()

    if "pressure" in prompt:
        return """
AI Manufacturing Copilot Analysis

Possible causes of elevated reactor pressure:
- Flow restriction
- Valve instability
- Reactor overfeed
- Temperature-driven vapor expansion

Recommended actions:
- Verify valve response
- Inspect vent line
- Review feed rate trend
- Confirm pressure sensor calibration
"""

    elif "yield" in prompt:
        return """
AI Manufacturing Copilot Analysis

Possible causes of low yield:
- Raw material variability
- Incomplete reaction conversion
- Mixing inefficiency
- Purification losses

Recommended CAPA:
- Review batch raw material CoA
- Increase process monitoring
- Verify mixing speed consistency
- Perform reactor cleaning verification
"""

    elif "deviation" in prompt:
        return """
AI Manufacturing Copilot Analysis

Potential deviation contributors:
- Process drift
- Equipment instability
- Human intervention variability
- Environmental fluctuations

Suggested investigation:
- Review audit trail
- Compare historical batches
- Evaluate equipment health
- Verify SOP adherence
"""

    elif "release" in prompt:
        return """
AI Manufacturing Copilot Analysis

Recommended QA release review:
- Evaluate critical process parameters
- Confirm batch documentation completeness
- Verify no unresolved deviations
- Review AI risk scoring
"""

    elif "gmp" in prompt:
        return """
AI Manufacturing Copilot Analysis

Relevant GMP considerations:
- Data integrity
- Traceability
- Audit trail completeness
- CAPA documentation
- Electronic record verification
"""

    return f"""
AI Manufacturing Copilot

Question received:
{user_prompt}

General recommendation:
- Continue QA review
- Verify process stability
- Compare against historical batches
- Review audit trail and CAPA workflow

AI Copilot Confidence: 82%
"""



# ============================================================
# AI Digital Twin Simulation Helper Functions
# ============================================================

def run_digital_twin_simulation(batch, temperature_adjustment, pressure_adjustment):
    simulated_temperature = batch["temperature"] + temperature_adjustment
    simulated_pressure = batch["pressure"] + pressure_adjustment

    base_yield = batch["yield_percent"]

    temperature_penalty = abs(simulated_temperature - 37.0) * 0.8
    pressure_penalty = abs(simulated_pressure - 1.8) * 3.0

    simulated_yield = base_yield - temperature_penalty - pressure_penalty

    if 36 <= simulated_temperature <= 38 and 1.6 <= simulated_pressure <= 2.0:
        simulated_yield += 4

    simulated_yield = max(min(round(simulated_yield, 2), 99), 0)

    simulated_risk = 0

    if simulated_temperature > 40:
        simulated_risk += 40

    if simulated_pressure > 2:
        simulated_risk += 25

    if simulated_yield < 90:
        simulated_risk += 35

    simulated_risk = min(simulated_risk, 100)

    if simulated_risk >= 70:
        scenario_status = "High-Risk Scenario"
    elif simulated_risk >= 40:
        scenario_status = "Moderate-Risk Scenario"
    else:
        scenario_status = "Stable Scenario"

    yield_change = round(simulated_yield - base_yield, 2)

    return {
        "batch_number": batch["batch_number"],
        "base_temperature": batch["temperature"],
        "base_pressure": batch["pressure"],
        "base_yield": base_yield,
        "simulated_temperature": round(simulated_temperature, 2),
        "simulated_pressure": round(simulated_pressure, 2),
        "simulated_yield": simulated_yield,
        "simulated_risk": simulated_risk,
        "yield_change": yield_change,
        "scenario_status": scenario_status,
    }


def format_digital_twin_report(simulation):
    return f"""
AI Digital Twin Simulation Report

Batch Number:
{simulation["batch_number"]}

Baseline Parameters:
- Temperature: {simulation["base_temperature"]} °C
- Pressure: {simulation["base_pressure"]}
- Yield: {simulation["base_yield"]}%

Simulated Parameters:
- Temperature: {simulation["simulated_temperature"]} °C
- Pressure: {simulation["simulated_pressure"]}
- Predicted Yield: {simulation["simulated_yield"]}%

Predicted Yield Change:
{simulation["yield_change"]}%

Simulated Risk Score:
{simulation["simulated_risk"]}/100

Scenario Status:
{simulation["scenario_status"]}

Executive Digital Twin Summary:
The digital twin simulation estimates how process parameter changes may influence batch yield and risk. This allows QA and process engineering teams to test hypothetical manufacturing scenarios before applying changes in production.
"""



def generate_qa_pdf_report(batch_number, report_content):
    safe_batch_number = str(batch_number).replace("/", "_").replace(" ", "_")
    pdf_file_name = f"{safe_batch_number}_qa_report.pdf"
    doc = SimpleDocTemplate(pdf_file_name, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Pharma Manufacturing QA/CAPA Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Batch Number: {batch_number}", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(report_content.replace("\n", "<br/>"), styles["BodyText"]),
    ]
    doc.build(elements)
    return pdf_file_name


def ask_rag_assistant(question):
    embedding_model = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    relevant_docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""
You are a pharma QA/CAPA assistant.

Use the context below to answer the user's question.
If the answer is not in the context, clearly say that the knowledge base does not contain enough information.

Context:
{context}

Question:
{question}

Answer in a clear, professional QA/CAPA style.
Include:
- likely root cause
- recommended CAPA actions
- QA/release recommendation when relevant
"""
    response = llm.invoke(prompt)
    return response.content, relevant_docs


def add_audit_event(event, batch, details):
    st.session_state.audit_log.append(
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": event, "batch": batch, "details": details}
    )


batch_data = load_api_data(API_URL, [])
risk_summary = load_api_data(RISK_URL, {"high_risk": 0, "medium_risk": 0, "low_risk": 0})
deviation_data = load_api_data(DEVIATION_URL, [])
data_source = "FastAPI backend" if batch_data else "Backend unavailable"

df = pd.DataFrame(batch_data)
if not df.empty and "batch_number" in df.columns:
    df = df.drop_duplicates(subset=["batch_number"], keep="first")

deviation_df = pd.DataFrame(deviation_data)

if df.empty:
    st.error("No batch data available. Please check that FastAPI is running.")
    st.stop()

required_columns = ["batch_number", "product_name", "temperature", "pressure", "yield_percent", "status"]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(f"Missing required columns from API response: {missing_columns}")
    st.stop()

st.sidebar.markdown("# 🏭 Pharma AI")
st.sidebar.markdown("### Manufacturing Control Center")
st.sidebar.markdown("---")

st.sidebar.markdown("### Logged-in User")
st.sidebar.write(f"**Name:** {st.session_state.user_name}")
st.sidebar.write(f"**Role:** {st.session_state.user_role}")
st.sidebar.caption(ROLE_ACCESS.get(st.session_state.user_role, ""))

if st.sidebar.button("Logout"):
    logout_user()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("Batch Filter")
st.sidebar.caption(f"Data source: {data_source}")
st.sidebar.success("System Status: Online")
st.sidebar.info("Mode: Local API + PostgreSQL")

search_batch = st.sidebar.text_input("Search Batch Number", placeholder="Example: B-1025")
batch_options = ["All Batches"] + list(df["batch_number"])
selected_batch = st.sidebar.selectbox("Select Batch", batch_options)

if search_batch:
    filtered_df = df[df["batch_number"].str.contains(search_batch, case=False, na=False)]
elif selected_batch == "All Batches":
    filtered_df = df
else:
    filtered_df = df[df["batch_number"] == selected_batch]

if filtered_df.empty:
    st.warning("No batches match the current filter.")
    st.stop()

critical_alerts = calculate_critical_alerts(filtered_df)
risky_batches = get_risky_batches(filtered_df)

st.title("Pharma Manufacturing Intelligence Dashboard")
st.write(
    "AI-assisted pharma manufacturing dashboard for batch monitoring, "
    "deviation detection, QA/CAPA support, and RAG-based knowledge assistance."
)


st.success(
    f"Logged in as {st.session_state.user_name} | Role: {st.session_state.user_role}"
)

with st.expander("Role-Based Access Overview"):
    role_df = pd.DataFrame(
        [
            {"Role": "Admin", "Access": "Full platform access"},
            {"Role": "QA Manager", "Access": "QA/CAPA, reports, deviation review, audit trail"},
            {"Role": "Process Engineer", "Access": "Trends, equipment monitoring, live monitoring, batch comparison"},
            {"Role": "Manufacturing Operator", "Access": "Overview, risk alerts, live monitoring"},
        ]
    )
    st.dataframe(role_df, hide_index=True)


platform_score, platform_capabilities = calculate_platform_maturity_score()

hero_col1, hero_col2, hero_col3, hero_col4 = st.columns(4)

hero_col1.metric("Platform Maturity", f"{platform_score}/100")
hero_col2.metric("AI Modules", "7")
hero_col3.metric("Enterprise Workflows", "5")
hero_col4.metric("Demo Readiness", "High")


tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19 = st.tabs(
    [
        "Overview",
        "Risk & Alerts",
        "Deviation Management",
        "QA / CAPA",
        "Reports",
        "RAG QA Assistant",
        "Audit Trail",
        "Batch Comparison",
        "AI Deviation Report",
        "AI Trend Prediction",
        "Live Manufacturing Monitor",
        "Equipment Monitoring",
        "Executive Demo Center",
        "AI Root Cause Investigation",
        "Batch Genealogy",
        "AI Process Optimization",
        "AI Batch Failure Prediction",
        "AI Manufacturing Copilot",
        "AI Digital Twin Simulation",
    ]
)

with tab1:
    approved_count = len(filtered_df[filtered_df["status"] == "Approved"])
    pending_count = len(filtered_df[filtered_df["status"] == "Pending Review"])
    approval_rate = (approved_count / len(filtered_df)) * 100
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if critical_alerts > 0:
        st.error(f"🚨 {critical_alerts} critical manufacturing batches require immediate QA review")
    else:
        st.success("✅ No critical manufacturing alerts detected")

    st.subheader("Executive Manufacturing Summary")
    executive_col1, executive_col2, executive_col3 = st.columns(3)
    executive_col1.info(f"""
### Production Readiness
• Total batches monitored: {len(filtered_df)}
• Approved batches: {approved_count}
• Pending QA review: {pending_count}
""")
    executive_col2.warning(f"""
### Manufacturing Risk
• High-risk batches: {risk_summary['high_risk']}
• Medium-risk batches: {risk_summary['medium_risk']}
• Critical alerts: {critical_alerts}
""")
    executive_col3.success("""
### System Health
• Reactor systems operational
• API status connected
• GMP workflow active
• Dashboard synced successfully
""")

    st.subheader("Manufacturing Control Status")
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    status_col1.success("🟢 Reactor System Online")
    status_col2.warning(f"🟡 QA Review Queue: {pending_count}")
    status_col3.error(f"🔴 Critical Alerts: {critical_alerts}")
    status_col4.info(f"🕒 Last Refresh: {current_time}")

    st.subheader("Key Manufacturing KPIs")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Batches", len(filtered_df))
    col2.metric("Average Yield", f"{filtered_df['yield_percent'].mean():.1f}%")
    col3.metric("Max Temperature", f"{filtered_df['temperature'].max():.1f} °C")
    col4.metric("Approval Rate", f"{approval_rate:.1f}%")

    st.markdown("### Risk Classification")
    risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
    risk_col1.metric("High Risk", risk_summary["high_risk"])
    risk_col2.metric("Medium Risk", risk_summary["medium_risk"])
    risk_col3.metric("Low Risk", risk_summary["low_risk"])
    risk_col4.metric("Critical Alerts", critical_alerts)

    st.markdown("### Executive KPI Charts")
    chart_col1, chart_col2 = st.columns(2)
    approval_chart_df = pd.DataFrame({"Status": ["Approved", "Pending Review"], "Count": [approved_count, pending_count]})
    risk_chart_df = pd.DataFrame({"Risk Level": ["High Risk", "Medium Risk", "Low Risk"], "Count": [risk_summary["high_risk"], risk_summary["medium_risk"], risk_summary["low_risk"]]})

    with chart_col1:
        fig_approval = px.pie(approval_chart_df, values="Count", names="Status", hole=0.45, title="Batch Approval Status")
        st.plotly_chart(fig_approval, use_container_width=True)
    with chart_col2:
        fig_risk = px.bar(risk_chart_df, x="Risk Level", y="Count", title="Risk Distribution", text="Count")
        st.plotly_chart(fig_risk, use_container_width=True)

    st.subheader("Batch Data")
    display_df = filtered_df.drop(columns=["id"], errors="ignore")
    st.dataframe(display_df, hide_index=True)

    st.subheader("Batch Comparison")
    comparison_columns = ["temperature", "pressure", "yield_percent"]
    fig_comparison = px.line(filtered_df, x="batch_number", y=comparison_columns, markers=True, title="Temperature, Pressure, and Yield Comparison")
    st.plotly_chart(fig_comparison, use_container_width=True)

    st.subheader("Yield Comparison")
    fig_yield = px.bar(filtered_df, x="batch_number", y="yield_percent", title="Yield Comparison by Batch", text="yield_percent")
    st.plotly_chart(fig_yield, use_container_width=True)

    st.subheader("Temperature Trend")
    fig_temperature = px.line(filtered_df, x="batch_number", y="temperature", markers=True, title="Temperature Trend by Batch")
    st.plotly_chart(fig_temperature, use_container_width=True)

    st.subheader("Top Risky Batches")
    if risky_batches.empty:
        st.success("No risky batches found in the selected filter.")
    else:
        st.dataframe(risky_batches.drop(columns=["id"], errors="ignore"), hide_index=True)

    st.subheader("Batch Health Score")
    for _, row in filtered_df.iterrows():
        health_score = calculate_health_score(row)
        if health_score >= 80:
            st.success(f"{row['batch_number']} Health Score: {health_score}/100")
        elif health_score >= 60:
            st.warning(f"{row['batch_number']} Health Score: {health_score}/100")
        else:
            st.error(f"{row['batch_number']} Health Score: {health_score}/100")

with tab2:
    st.subheader("Risk & Alerts Overview")
    st.info("This section summarizes process risk, batch status, and QA review requirements.")
    st.subheader("Live Manufacturing Alert Feed")
    current_time = datetime.now().strftime("%H:%M:%S")
    alert_count = 0
    st.caption("Monitoring temperature, pressure, and yield deviations in real time.")
    for _, row in filtered_df.iterrows():
        if row["temperature"] > 40:
            st.error(f"[{current_time}] | HIGH TEMPERATURE | Batch {row['batch_number']} | Temperature: {row['temperature']} °C")
            alert_count += 1
        if row["yield_percent"] < 90:
            st.warning(f"[{current_time}] | LOW YIELD | Batch {row['batch_number']} | Yield: {row['yield_percent']}%")
            alert_count += 1
        if row["pressure"] > 2:
            st.warning(f"[{current_time}] | HIGH PRESSURE | Batch {row['batch_number']} | Pressure: {row['pressure']}")
            alert_count += 1
    if alert_count == 0:
        st.success("No live manufacturing alerts for the selected batch filter.")

    st.subheader("Top Risky Batches")
    if risky_batches.empty:
        st.success("No risky batches found in the selected filter.")
    else:
        st.dataframe(risky_batches.drop(columns=["id"], errors="ignore"), hide_index=True)

    st.subheader("Risk Trend")
    risk_data = []
    for _, row in filtered_df.iterrows():
        risk_data.append({"batch_number": row["batch_number"], "risk_score": calculate_risk_score(row)})
    risk_df = pd.DataFrame(risk_data)
    fig_risk_trend = px.line(risk_df, x="batch_number", y="risk_score", markers=True, title="AI Risk Score Trend")
    st.plotly_chart(fig_risk_trend, use_container_width=True)

    st.subheader("Batch Release Decision")
    for _, row in filtered_df.iterrows():
        if row["temperature"] > 40 and row["yield_percent"] < 90:
            st.error(f"❌ BATCH REJECTED: {row['batch_number']}")
        elif row["yield_percent"] < 90 or row["pressure"] > 2:
            st.warning(f"⚠️ BATCH REQUIRES QA REVIEW: {row['batch_number']}")
        else:
            st.success(f"✅ BATCH APPROVED: {row['batch_number']}")

with tab3:
    st.subheader("Deviation KPIs")
    dev_col1, dev_col2, dev_col3 = st.columns(3)
    dev_col1.metric("Total Deviations", len(deviation_df))
    if not deviation_df.empty:
        dev_col2.metric("Critical Deviations", len(deviation_df[deviation_df["severity"] == "Critical"]))
        dev_col3.metric("High Severity Deviations", len(deviation_df[deviation_df["severity"] == "High"]))
    else:
        dev_col2.metric("Critical Deviations", 0)
        dev_col3.metric("High Severity Deviations", 0)

    st.subheader("Deviation Management")
    st.dataframe(deviation_df, hide_index=True)
    if not deviation_df.empty:
        severity_counts = deviation_df["severity"].value_counts().reset_index()
        severity_counts.columns = ["Severity", "Count"]
        fig_severity = px.pie(severity_counts, names="Severity", values="Count", hole=0.4, title="Deviation Severity Distribution")
        st.plotly_chart(fig_severity, use_container_width=True)
        st.subheader("Severity Distribution")
        st.dataframe(severity_counts, hide_index=True)
        st.subheader("Severity Review")
        for _, row in deviation_df.iterrows():
            if row["severity"] == "Critical":
                st.error(f"CRITICAL: {row['issue_type']} in {row['batch_number']}")
            elif row["severity"] == "High":
                st.warning(f"HIGH: {row['issue_type']} in {row['batch_number']}")
            elif row["severity"] == "Medium":
                st.info(f"MEDIUM: {row['issue_type']} in {row['batch_number']}")
            else:
                st.success(f"LOW: {row['issue_type']} in {row['batch_number']}")
        st.subheader("CAPA Tracking")
        for _, row in deviation_df.iterrows():
            st.warning(f"CAPA required for {row['batch_number']} — {row['issue_type']}")
    else:
        st.success("No deviations detected.")

with tab4:
    st.subheader("AI Root Cause Recommendation Engine")
    st.info("This module analyzes manufacturing deviations and suggests possible root causes, CAPA actions, and QA release recommendations.")
    for _, row in filtered_df.iterrows():
        st.markdown(f"## Batch {row['batch_number']}")
        ai_risk_score = calculate_risk_score(row)
        failure_probability = min(ai_risk_score + 10, 100)
        release_result = generate_release_recommendation(row)
        severity_level = classify_deviation_severity(ai_risk_score)
        capa_actions = generate_capa_actions(ai_risk_score)

        if row["temperature"] > 40:
            st.error(f"HIGH TEMPERATURE detected | {row['temperature']} °C")
            st.markdown("### Possible Root Cause")
            st.write("- Reactor cooling instability\n- Incorrect process temperature setpoint\n- Heat exchanger efficiency loss")
            st.markdown("### Recommended CAPA")
            st.write("- Inspect cooling system immediately\n- Verify reactor sensor calibration\n- Perform preventive maintenance review")
        if row["yield_percent"] < 90:
            st.warning(f"LOW YIELD detected | {row['yield_percent']}%")
            st.markdown("### Possible Root Cause")
            st.write("- Raw material variability\n- Incomplete reaction conversion\n- Product loss during purification")
            st.markdown("### Recommended CAPA")
            st.write("- Review raw material supplier COA\n- Investigate purification efficiency\n- Increase sampling frequency")
        if row["pressure"] > 2:
            st.warning(f"HIGH PRESSURE detected | {row['pressure']}")
            st.markdown("### Possible Root Cause")
            st.write("- Pressure valve malfunction\n- Reactor blockage\n- Gas flow instability")
            st.markdown("### Recommended CAPA")
            st.write("- Inspect pressure valve system\n- Verify gas flow control\n- Perform equipment integrity check")

        st.markdown("### Predictive Batch Failure Probability")
        st.progress(failure_probability / 100)
        st.write(f"Predicted failure probability: {failure_probability}%")
        st.markdown("### AI Batch Release Recommendation")
        if release_result["decision"] == "HOLD":
            st.error(f"Recommended Action: {release_result['decision']}")
        elif release_result["decision"] == "INVESTIGATE":
            st.warning(f"Recommended Action: {release_result['decision']}")
        else:
            st.success(f"Recommended Action: {release_result['decision']}")
        st.write("Recommendation Reasons:")
        if release_result["reasons"]:
            for reason in release_result["reasons"]:
                st.write(f"- {reason}")
        else:
            st.write("- No major release risk reason detected")
        st.progress(release_result["risk_score"] / 100)
        st.write(f"AI Release Risk Score: {release_result['risk_score']}/100")
        st.markdown("### AI Risk Assessment")
        if ai_risk_score >= 70:
            st.error(f"AI Risk Score: {ai_risk_score}/100 | CRITICAL RISK")
            st.error("AI Recommendation: HOLD batch for QA investigation")
        elif ai_risk_score >= 40:
            st.warning(f"AI Risk Score: {ai_risk_score}/100 | MEDIUM RISK")
            st.warning("AI Recommendation: QA review required before release")
        else:
            st.success(f"AI Risk Score: {ai_risk_score}/100 | LOW RISK")
            st.success("AI Recommendation: Batch suitable for release")
        st.markdown("### Deviation Severity Classification")
        if severity_level == "Critical":
            st.error(f"Deviation Severity: {severity_level}")
            st.error("Immediate QA escalation required. Manufacturing batch may impact product quality or patient safety.")
        elif severity_level == "Major":
            st.warning(f"Deviation Severity: {severity_level}")
            st.warning("QA investigation recommended before batch disposition.")
        else:
            st.success(f"Deviation Severity: {severity_level}")
            st.success("Deviation impact assessed as low risk.")
        st.markdown("### AI CAPA Recommendations")
        for action in capa_actions:
            st.info(f"CAPA Action: {action}")
        st.markdown("### AI Executive Summary")
        executive_summary = f"""
Batch {row['batch_number']} shows a manufacturing yield of {row['yield_percent']}%
with reactor temperature at {row['temperature']}°C and pressure at {row['pressure']}.

AI risk evaluation classified this batch as {release_result['risk_score']}/100 risk score.

Deviation severity classification: {severity_level}.

Recommended QA action: {release_result['decision']}.

Release decision: {release_result['decision']}.
"""
        st.info(executive_summary)
        if ai_risk_score == 0:
            st.success("No major manufacturing deviations detected.")
            st.markdown("### Release Recommendation")
            st.write("- Batch suitable for QA approval\n- Continue standard GMP documentation")
        st.markdown("---")

    st.subheader("QA Review & Approval")
    if st.session_state.user_role not in ["Admin", "QA Manager"]:
        st.warning("Only Admin and QA Manager roles can submit QA decisions.")
    qa_reviewer = st.text_input("QA Reviewer Name")
    qa_decision = st.selectbox("QA Decision", ["Pending", "Approved", "Rejected", "Requires Investigation"])
    qa_comment = st.text_area("QA Review Comment")
    if st.button("Submit QA Decision", disabled=st.session_state.user_role not in ["Admin", "QA Manager"]):
        st.success("QA decision successfully recorded")
        add_audit_event(event="QA decision submitted", batch=selected_batch, details=qa_decision)
    st.write(f"Reviewer: {qa_reviewer}")
    st.write(f"Decision: {qa_decision}")
    st.write(f"Comment: {qa_comment}")
    st.markdown("---")
    st.subheader("Export QA Report")
    pdf_batch_row = filtered_df.iloc[0]
    pdf_release_result = generate_release_recommendation(pdf_batch_row)
    pdf_reasons = "\n".join([f"- {reason}" for reason in pdf_release_result["reasons"]])
    report_text = f"""
Batch Number:
{selected_batch}

Temperature:
{pdf_batch_row['temperature']} °C

Pressure:
{pdf_batch_row['pressure']}

Yield:
{pdf_batch_row['yield_percent']}%

Batch Status:
{pdf_batch_row['status']}

AI Release Recommendation:
{pdf_release_result['decision']}

AI Release Risk Score:
{pdf_release_result['risk_score']}/100

Recommendation Reasons:
{pdf_reasons if pdf_reasons else '- No major release risk reason detected'}

QA Reviewer:
{qa_reviewer}

QA Decision:
{qa_decision}

QA Comment:
{qa_comment}
"""
    if st.button("Generate PDF QA Report", disabled=st.session_state.user_role not in ["Admin", "QA Manager"]):
        report_batch_name = selected_batch if selected_batch != "All Batches" else "general_report"
        pdf_path = generate_qa_pdf_report(report_batch_name, report_text)
        st.session_state["latest_pdf_path"] = pdf_path
        add_audit_event(event="PDF QA report generated", batch=report_batch_name, details=qa_decision)
        st.success("PDF report generated successfully")
    if "latest_pdf_path" in st.session_state:
        with open(st.session_state["latest_pdf_path"], "rb") as pdf_file:
            st.download_button(label="Download QA PDF Report", data=pdf_file, file_name=st.session_state["latest_pdf_path"], mime="application/pdf")

with tab5:
    st.subheader("Download Batch Report")
    report_text = f"""
Batch Report

Selected Batch:
{selected_batch}

Average Yield:
{filtered_df['yield_percent'].mean():.1f}%

Total Batches Displayed:
{len(filtered_df)}

High Risk Batches:
{risk_summary['high_risk']}

Medium Risk Batches:
{risk_summary['medium_risk']}

Low Risk Batches:
{risk_summary['low_risk']}

Critical Alerts:
{critical_alerts}

Total Deviations:
{len(deviation_df)}

Generated:
{datetime.now()}

Data source:
{data_source}

Generated from Pharma Manufacturing Intelligence Dashboard
"""
    st.download_button(label="Download Report", data=report_text, file_name=f"{selected_batch}_report.txt", mime="text/plain")
    st.subheader("Audit Trail")
    current_time = datetime.now()
    st.write(f"Data source: {data_source}")
    st.write(f"Last dashboard review: {current_time}")
    st.write("Audit status: Traceability enabled")

with tab6:
    st.subheader("RAG QA Assistant")
    st.info("Ask GMP, CAPA, deviation, or manufacturing questions using the internal pharma knowledge base.")
    user_question = st.text_area("Enter your QA/CAPA question", placeholder="Example: What should QA do for low yield?", height=120)
    st.markdown("### Batch-Specific RAG Question")
    if selected_batch != "All Batches":
        selected_row = filtered_df.iloc[0]
        batch_question = (
            f"For batch {selected_row['batch_number']}, "
            f"temperature is {selected_row['temperature']} °C, "
            f"pressure is {selected_row['pressure']}, "
            f"yield is {selected_row['yield_percent']}%, "
            f"and status is {selected_row['status']}. "
            f"Explain the likely root cause and recommended CAPA actions."
        )
        if st.button("Ask About Selected Batch", disabled=st.session_state.user_role not in ["Admin", "QA Manager", "Process Engineer"]):
            st.write("Question sent to RAG:")
            st.code(batch_question)
            with st.spinner("Analyzing selected batch with RAG..."):
                batch_answer, batch_docs = ask_rag_assistant(batch_question)
            st.success("Batch-specific RAG answer generated")
            st.markdown("### Batch-Specific Assistant Response")
            st.write(batch_answer)
            st.markdown("### Retrieved Knowledge Sources")
            for i, doc in enumerate(batch_docs, start=1):
                with st.expander(f"Source chunk {i}"):
                    st.write(doc.page_content)
            st.session_state.rag_chat_history.append({"question": batch_question, "answer": batch_answer})
            add_audit_event(event="Batch-specific RAG question asked", batch=selected_batch, details=batch_question)
    else:
        st.info("Select one specific batch from the sidebar to ask a batch-specific RAG question.")
    st.markdown("---")
    if st.button("Ask RAG Assistant", disabled=st.session_state.user_role not in ["Admin", "QA Manager", "Process Engineer"]):
        if user_question.strip() == "":
            st.warning("Please enter a question.")
        else:
            with st.spinner("Searching knowledge base..."):
                rag_answer, retrieved_docs = ask_rag_assistant(user_question)
            st.success("Answer generated successfully")
            st.markdown("### Assistant Response")
            st.write(rag_answer)
            st.markdown("### Retrieved Knowledge Sources")
            for i, doc in enumerate(retrieved_docs, start=1):
                with st.expander(f"Source chunk {i}"):
                    st.write(doc.page_content)
            st.session_state.rag_chat_history.append({"question": user_question, "answer": rag_answer})
            add_audit_event(event="RAG question asked", batch=selected_batch, details=user_question)
    st.markdown("---")
    st.subheader("RAG Chat History")
    if st.session_state.rag_chat_history:
        for i, item in enumerate(st.session_state.rag_chat_history, start=1):
            with st.expander(f"Interaction {i}"):
                st.markdown("**Question**")
                st.write(item["question"])
                st.markdown("**Answer**")
                st.write(item["answer"])
    else:
        st.info("No RAG interactions yet.")

with tab7:
    st.subheader("Enterprise Audit Trail")
    if st.session_state.user_role not in ["Admin", "QA Manager"]:
        st.warning("Audit trail is primarily intended for Admin and QA Manager roles.")
    st.info("This audit trail records key AI, QA, and reporting actions for GMP-style traceability.")
    if len(st.session_state.audit_log) == 0:
        st.warning("No audit events recorded yet.")
    else:
        audit_df = pd.DataFrame(st.session_state.audit_log)
        st.dataframe(audit_df, hide_index=True)
        st.download_button(label="Download Audit Trail CSV", data=audit_df.to_csv(index=False), file_name="audit_trail.csv", mime="text/csv")

with tab8:
    st.subheader("AI Batch Comparison & Root Cause Analysis")
    st.info("Compare two manufacturing batches to identify process deviations, root causes, and QA risk differences.")
    compare_options = df["batch_number"].tolist()
    compare_batch_a = st.selectbox("Select First Batch", compare_options, key="compare_a")
    compare_batch_b = st.selectbox("Select Second Batch", compare_options, index=1 if len(compare_options) > 1 else 0, key="compare_b")
    if st.button("Run Batch Comparison"):
        batch_a_row = df[df["batch_number"] == compare_batch_a].iloc[0]
        batch_b_row = df[df["batch_number"] == compare_batch_b].iloc[0]
        comparison_result = compare_two_batches(batch_a_row, batch_b_row)
        st.markdown("### Comparison Results")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperature Difference", f"{comparison_result['temperature_difference']:.2f} °C")
        with col2:
            st.metric("Pressure Difference", f"{comparison_result['pressure_difference']:.2f}")
        with col3:
            st.metric("Yield Difference", f"{comparison_result['yield_difference']:.2f}%")
        st.markdown("---")
        st.markdown("### AI Release Decision Comparison")
        decision_col1, decision_col2 = st.columns(2)
        with decision_col1:
            if comparison_result["batch_a_release"] == "RELEASE":
                st.success(f"{compare_batch_a}: {comparison_result['batch_a_release']}")
            elif comparison_result["batch_a_release"] == "INVESTIGATE":
                st.warning(f"{compare_batch_a}: {comparison_result['batch_a_release']}")
            else:
                st.error(f"{compare_batch_a}: {comparison_result['batch_a_release']}")
        with decision_col2:
            if comparison_result["batch_b_release"] == "RELEASE":
                st.success(f"{compare_batch_b}: {comparison_result['batch_b_release']}")
            elif comparison_result["batch_b_release"] == "INVESTIGATE":
                st.warning(f"{compare_batch_b}: {comparison_result['batch_b_release']}")
            else:
                st.error(f"{compare_batch_b}: {comparison_result['batch_b_release']}")
        st.markdown("---")
        st.markdown("### AI Root Cause Analysis")
        for note in comparison_result["root_cause_notes"]:
            st.warning(note)


# ============================================================
# Tab 9: AI Deviation Report
# ============================================================

with tab9:
    st.subheader("AI-Generated Deviation Report")

    st.info(
        "Generate a professional deviation investigation summary using batch data, "
        "AI risk logic, severity classification, release recommendation, and CAPA actions."
    )

    report_batch_options = df["batch_number"].tolist()

    selected_report_batch = st.selectbox(
        "Select Batch for AI Deviation Report",
        report_batch_options,
        key="deviation_report_batch",
    )

    selected_report_row = df[
        df["batch_number"] == selected_report_batch
    ].iloc[0]

    generated_report = generate_ai_deviation_report(selected_report_row)

    st.markdown("### AI Deviation Report Preview")

    st.text_area(
        "Generated Report",
        generated_report,
        height=520,
    )

    st.download_button(
        label="Download AI Deviation Report TXT",
        data=generated_report,
        file_name=f"{selected_report_batch}_ai_deviation_report.txt",
        mime="text/plain",
    )

    if st.button("Record Deviation Report in Audit Trail", disabled=st.session_state.user_role not in ["Admin", "QA Manager"]):
        add_audit_event(
            event="AI deviation report generated",
            batch=selected_report_batch,
            details="Deviation report generated in AI Deviation Report tab",
        )
        st.success("AI deviation report recorded in audit trail.")




# ============================================================
# Tab 10: AI Trend Prediction
# ============================================================

with tab10:
    st.subheader("AI Manufacturing Trend Prediction Dashboard")

    st.info(
        "AI-based predictive monitoring for future manufacturing deviation risk."
    )

    trend_batch_options = df["batch_number"].tolist()

    selected_trend_batch = st.selectbox(
        "Select Batch for AI Trend Prediction",
        trend_batch_options,
        key="trend_prediction_batch",
    )

    trend_row = df[
        df["batch_number"] == selected_trend_batch
    ].iloc[0]

    current_risk = calculate_risk_score(trend_row)
    future_risk = predict_future_risk(trend_row)
    future_risk_classification = classify_future_risk(future_risk)

    st.markdown("### AI Risk Forecast")

    col1, col2, col3 = st.columns(3)

    col1.metric("Current Risk Score", f"{current_risk}/100")
    col2.metric("Predicted Future Risk", f"{future_risk}/100")
    col3.metric("Risk Classification", future_risk_classification)

    st.markdown("### AI Future Risk Progress")
    st.progress(future_risk / 100)

    if future_risk >= 70:
        st.error("AI predicts a HIGH probability of future manufacturing deviation.")
    elif future_risk >= 40:
        st.warning("AI predicts MODERATE future manufacturing process risk.")
    else:
        st.success("AI predicts LOW future manufacturing process risk.")

    st.markdown("### Manufacturing Trend Analysis")

    trend_summary = generate_trend_summary(trend_row, future_risk)

    for item in trend_summary:
        st.warning(item)

    st.markdown("### Manufacturing Parameter Visualization")

    trend_chart_df = pd.DataFrame(
        {
            "Parameter": [
                "Temperature",
                "Pressure x10",
                "Yield",
                "Current Risk",
                "Future Risk",
            ],
            "Value": [
                trend_row["temperature"],
                trend_row["pressure"] * 10,
                trend_row["yield_percent"],
                current_risk,
                future_risk,
            ],
        }
    )

    fig_trend = px.bar(
        trend_chart_df,
        x="Parameter",
        y="Value",
        text="Value",
        title="AI Manufacturing Trend Prediction",
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("### AI Executive Forecast Summary")

    executive_forecast = f"""
Batch {trend_row['batch_number']} currently operates with reactor temperature at
{trend_row['temperature']} °C, pressure at {trend_row['pressure']}, and manufacturing
yield at {trend_row['yield_percent']}%.

AI predictive analysis estimates future manufacturing risk at {future_risk}/100,
classified as {future_risk_classification} risk.

Recommended action:
Continue proactive QA monitoring and preventive process review.
"""

    st.info(executive_forecast)

    if st.button("Record AI Trend Analysis", disabled=st.session_state.user_role not in ["Admin", "Process Engineer"]):
        add_audit_event(
            event="AI trend prediction generated",
            batch=selected_trend_batch,
            details=future_risk_classification,
        )

        st.success("AI trend prediction recorded in audit trail.")



# ============================================================
# Tab 11: Live Manufacturing Monitor
# ============================================================

with tab11:
    st.subheader("Live Manufacturing Monitoring Dashboard")

    st.info(
        "Simulated real-time manufacturing control room view for reactor temperature, "
        "pressure, yield drift, live AI risk, and streaming alerts."
    )

    monitor_col1, monitor_col2 = st.columns([2, 1])

    with monitor_col1:
        live_batch_options = df["batch_number"].tolist()

        selected_live_batch = st.selectbox(
            "Select Batch for Live Monitoring",
            live_batch_options,
            key="live_monitoring_batch",
        )

    with monitor_col2:
        auto_refresh_enabled = st.checkbox(
            "Enable live auto-refresh",
            value=False,
        )

    if auto_refresh_enabled:
        if st_autorefresh is not None:
            st_autorefresh(interval=5000, key="live_monitor_refresh")
        else:
            st.warning(
                "Auto-refresh package is not installed. Run: pip install streamlit-autorefresh"
            )

    live_row = df[df["batch_number"] == selected_live_batch].iloc[0]

    live_values = simulate_live_sensor_values(live_row)
    live_risk = calculate_live_risk(live_values)
    live_alerts = classify_live_alert(live_values)

    st.markdown("### Live Reactor KPI Panel")

    live_col1, live_col2, live_col3, live_col4 = st.columns(4)

    live_col1.metric("Live Temperature", f"{live_values['temperature']} °C")
    live_col2.metric("Live Pressure", f"{live_values['pressure']}")
    live_col3.metric("Live Yield Estimate", f"{live_values['yield_percent']}%")
    live_col4.metric("Live AI Risk", f"{live_risk}/100")

    st.markdown("### Live AI Risk Progress")
    st.progress(live_risk / 100)

    if live_risk >= 70:
        st.error("Live AI status: Critical operating risk detected.")
    elif live_risk >= 40:
        st.warning("Live AI status: Moderate operating risk detected.")
    else:
        st.success("Live AI status: Manufacturing process appears stable.")

    st.markdown("### Streaming Manufacturing Alerts")

    for alert in live_alerts:
        if alert["level"] == "Critical":
            st.error(alert["message"])
        elif alert["level"] == "Warning":
            st.warning(alert["message"])
        else:
            st.success(alert["message"])

    st.markdown("### Live Parameter Snapshot")

    live_chart_df = pd.DataFrame(
        {
            "Parameter": ["Temperature", "Pressure x20", "Yield", "Live Risk"],
            "Value": [
                live_values["temperature"],
                live_values["pressure"] * 20,
                live_values["yield_percent"],
                live_risk,
            ],
        }
    )

    fig_live_snapshot = px.bar(
        live_chart_df,
        x="Parameter",
        y="Value",
        text="Value",
        title=f"Live Manufacturing Snapshot — {selected_live_batch}",
    )

    st.plotly_chart(fig_live_snapshot, use_container_width=True)

    st.markdown("### Simulated Live Trend")

    live_trend_df = pd.DataFrame(
        {
            "Time Point": [f"T-{i}" for i in range(9, -1, -1)],
            "Temperature": [
                round(live_row["temperature"] + random.uniform(-1.2, 1.2), 2)
                for _ in range(10)
            ],
            "Pressure x20": [
                round((live_row["pressure"] + random.uniform(-0.2, 0.2)) * 20, 2)
                for _ in range(10)
            ],
            "Yield": [
                round(live_row["yield_percent"] + random.uniform(-1.8, 1.8), 2)
                for _ in range(10)
            ],
        }
    )

    fig_live_trend = px.line(
        live_trend_df,
        x="Time Point",
        y=["Temperature", "Pressure x20", "Yield"],
        markers=True,
        title=f"Simulated Live Process Trend — {selected_live_batch}",
    )

    st.plotly_chart(fig_live_trend, use_container_width=True)

    st.markdown("### AI Live Monitoring Summary")

    live_summary = f"""
Live monitoring snapshot for batch {selected_live_batch} at {live_values['timestamp']}.

Current simulated reactor temperature: {live_values['temperature']} °C
Current simulated pressure: {live_values['pressure']}
Current simulated yield estimate: {live_values['yield_percent']}%

Live AI risk score: {live_risk}/100.

Recommended action:
Continue monitoring. Escalate to QA or process engineering if live risk remains elevated across repeated refresh cycles.
"""

    st.info(live_summary)

    if st.button("Record Live Monitoring Event", disabled=st.session_state.user_role not in ["Admin", "Process Engineer", "Manufacturing Operator"]):
        add_audit_event(
            event="Live manufacturing monitoring event recorded",
            batch=selected_live_batch,
            details=f"Live AI risk: {live_risk}/100",
        )

        st.success("Live monitoring event recorded in audit trail.")



# ============================================================
# Tab 12: Equipment Monitoring
# ============================================================

with tab12:
    st.subheader("Predictive Maintenance & Equipment Monitoring")

    st.info(
        "Monitor reactor equipment health, predict maintenance risk, and generate "
        "AI-assisted maintenance recommendations."
    )

    equipment_batch_options = df["batch_number"].tolist()

    selected_equipment_batch = st.selectbox(
        "Select Batch for Equipment Health Analysis",
        equipment_batch_options,
        key="equipment_monitoring_batch",
    )

    equipment_row = df[
        df["batch_number"] == selected_equipment_batch
    ].iloc[0]

    equipment_health = calculate_equipment_health(equipment_row)
    equipment_status = classify_equipment_health(equipment_health)
    failure_probability = predict_equipment_failure_probability(equipment_row)
    maintenance_actions = generate_maintenance_recommendations(equipment_row)

    st.markdown("### Equipment Health Summary")

    eq_col1, eq_col2, eq_col3 = st.columns(3)

    eq_col1.metric("Equipment Health Score", f"{equipment_health}/100")
    eq_col2.metric("Failure Probability", f"{failure_probability}%")
    eq_col3.metric("Maintenance Status", equipment_status)

    st.markdown("### Equipment Health Progress")

    st.progress(equipment_health / 100)

    if equipment_status == "Healthy":
        st.success("Equipment status is healthy. Continue routine monitoring.")
    elif equipment_status == "Monitor":
        st.warning("Equipment should be monitored for early signs of instability.")
    elif equipment_status == "Maintenance Required":
        st.warning("Maintenance review is recommended before extended production use.")
    else:
        st.error("Critical maintenance risk detected. Escalate to engineering review.")

    st.markdown("### Reactor Equipment Indicators")

    equipment_indicator_df = pd.DataFrame(
        {
            "Indicator": [
                "Temperature Load",
                "Pressure Load",
                "Yield Impact",
                "Failure Probability",
                "Equipment Health",
            ],
            "Value": [
                equipment_row["temperature"],
                equipment_row["pressure"] * 20,
                100 - equipment_row["yield_percent"],
                failure_probability,
                equipment_health,
            ],
        }
    )

    fig_equipment = px.bar(
        equipment_indicator_df,
        x="Indicator",
        y="Value",
        text="Value",
        title="Equipment Risk Indicators",
    )

    st.plotly_chart(fig_equipment, use_container_width=True)

    st.markdown("### AI Maintenance Recommendations")

    for action in maintenance_actions:
        st.info(f"Maintenance Action: {action}")

    st.markdown("### Predictive Maintenance Summary")

    maintenance_summary = f"""
Batch {equipment_row['batch_number']} was analyzed for equipment health using
temperature, pressure, yield, and QA status indicators.

Equipment health score: {equipment_health}/100
Failure probability: {failure_probability}%
Maintenance status: {equipment_status}

Recommended action:
Follow the AI maintenance recommendations and document any equipment intervention
in the maintenance log.
"""

    st.info(maintenance_summary)

    if st.button("Record Equipment Monitoring Event", disabled=st.session_state.user_role not in ["Admin", "Process Engineer"]):
        add_audit_event(
            event="Equipment monitoring analysis generated",
            batch=selected_equipment_batch,
            details=equipment_status,
        )

        st.success("Equipment monitoring event recorded in audit trail.")




# ============================================================
# Tab 13: Executive Demo Center
# ============================================================

with tab13:
    st.subheader("Executive Demo Center")

    st.info(
        "Recruiter-ready executive overview of the Pharma Manufacturing Intelligence Platform."
    )

    platform_score, platform_capabilities = calculate_platform_maturity_score()

    st.markdown("### Platform Readiness Score")

    readiness_col1, readiness_col2, readiness_col3 = st.columns(3)

    readiness_col1.metric("Overall Platform Maturity", f"{platform_score}/100")
    readiness_col2.metric("Completed Capabilities", len(platform_capabilities))
    readiness_col3.metric("Recommended Demo Time", "5–7 min")

    st.progress(platform_score / 100)

    st.markdown("### Capability Map")

    capability_df = pd.DataFrame(
        [
            {
                "Capability": capability,
                "Status": "Complete" if status else "Pending",
            }
            for capability, status in platform_capabilities.items()
        ]
    )

    st.dataframe(
        capability_df,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### Executive Value Proposition")

    value_col1, value_col2 = st.columns(2)

    with value_col1:
        st.success(
            """
            ### Business Value

            • Faster batch risk review

            • QA/CAPA decision support

            • Better deviation visibility

            • Audit traceability

            • Predictive manufacturing insight
            """
        )

    with value_col2:
        st.info(
            """
            ### Technical Value

            • FastAPI backend

            • PostgreSQL data layer

            • Streamlit frontend

            • OpenAI + RAG

            • Docker deployment
            """
        )

    st.markdown("### Recruiter Demo Script")

    demo_script = generate_recruiter_demo_script()

    st.text_area(
        "Suggested 5–7 Minute Demo Flow",
        demo_script,
        height=360,
    )

    st.markdown("### CV / Interview Pitch")

    cv_pitch = generate_cv_pitch()

    st.text_area(
        "Project Pitch",
        cv_pitch,
        height=260,
    )

    st.download_button(
        label="Download Demo Script",
        data=demo_script,
        file_name="pharma_platform_demo_script.txt",
        mime="text/plain",
    )

    st.download_button(
        label="Download CV Project Pitch",
        data=cv_pitch,
        file_name="pharma_platform_cv_pitch.txt",
        mime="text/plain",
    )

    if st.button("Record Executive Demo Review"):
        add_audit_event(
            event="Executive demo center reviewed",
            batch="Platform",
            details=f"Platform maturity score: {platform_score}/100",
        )

        st.success("Executive demo review recorded in audit trail.")



st.markdown("---")

st.markdown("---")

# ============================================================
# Tab 14: AI Root Cause Investigation
# ============================================================

with tab14:
    st.subheader("AI Root Cause Investigation Engine")

    st.info(
        "Generate a structured pharma-style root cause investigation based on "
        "batch parameters, risk score, release recommendation, and CAPA logic."
    )

    investigation_batch_options = df["batch_number"].tolist()

    selected_investigation_batch = st.selectbox(
        "Select Batch for Root Cause Investigation",
        investigation_batch_options,
        key="root_cause_investigation_batch",
    )

    investigation_row = df[
        df["batch_number"] == selected_investigation_batch
    ].iloc[0]

    investigation = generate_root_cause_investigation(investigation_row)
    investigation_report = format_root_cause_report(investigation)

    st.markdown("### Investigation Summary")

    rc_col1, rc_col2, rc_col3, rc_col4 = st.columns(4)

    rc_col1.metric("Investigation Priority", investigation["investigation_priority"])
    rc_col2.metric("AI Confidence", f"{investigation['confidence_score']}%")
    rc_col3.metric("Risk Score", f"{investigation['risk_score']}/100")
    rc_col4.metric("Release Decision", investigation["release_decision"])

    st.markdown("### Probable Root Cause(s)")

    for cause in investigation["probable_root_causes"]:
        if investigation["investigation_priority"] == "High":
            st.error(cause)
        elif investigation["investigation_priority"] == "Medium":
            st.warning(cause)
        else:
            st.success(cause)

    st.markdown("### Contributing Process Parameter(s)")

    for parameter in investigation["contributing_parameters"]:
        st.info(parameter)

    st.markdown("### Corrective Action Recommendation(s)")

    for action in investigation["corrective_actions"]:
        st.warning(action)

    st.markdown("### Preventive Action Recommendation(s)")

    for action in investigation["preventive_actions"]:
        st.success(action)

    st.markdown("### Investigation Report")

    st.text_area(
        "AI-Generated Root Cause Investigation Report",
        investigation_report,
        height=520,
    )

    st.download_button(
        label="Download Root Cause Investigation Report",
        data=investigation_report,
        file_name=f"{selected_investigation_batch}_root_cause_investigation.txt",
        mime="text/plain",
    )

    if st.button(
        "Record Root Cause Investigation",
        disabled=st.session_state.user_role not in ["Admin", "QA Manager", "Process Engineer"],
    ):
        add_audit_event(
            event="AI root cause investigation generated",
            batch=selected_investigation_batch,
            details=f"Priority: {investigation['investigation_priority']} | Confidence: {investigation['confidence_score']}%",
        )

        st.success("Root cause investigation recorded in audit trail.")




st.markdown("### Enterprise Platform Statistics")

stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

try:
    database_events_df = load_database_audit_events()
    database_event_count = len(database_events_df)
except Exception:
    database_event_count = 0

stats_col1.metric("Persistent Audit Events", database_event_count)
stats_col2.metric("AI Modules", 7)
stats_col3.metric("Enterprise Workflows", 5)
stats_col4.metric("Platform Readiness", "Production Demo")



# ============================================================
# Tab 15: Batch Genealogy
# ============================================================

with tab15:

    st.subheader("Digital Batch Genealogy & Traceability")

    st.info(
        "Track raw material lineage, operator involvement, equipment usage, cleaning cycles, packaging linkage, and GMP traceability."
    )

    genealogy_batch = st.selectbox(
        "Select Batch for Genealogy",
        df["batch_number"].tolist(),
        key="genealogy_batch"
    )

    genealogy_row = df[df["batch_number"] == genealogy_batch].iloc[0]

    genealogy = generate_batch_genealogy(genealogy_row)

    st.markdown("### Batch Traceability Overview")

    g1, g2, g3, g4 = st.columns(4)

    g1.metric("Traceability Score", f"{genealogy['traceability_score']}/100")
    g2.metric("Contamination Risk", genealogy["contamination_risk"])
    g3.metric("Documentation", genealogy["documentation_status"])
    g4.metric("Supplier", "Verified")

    st.markdown("### Batch Genealogy Map")

    genealogy_text = f"""
Batch: {genealogy['batch_number']}

├── Raw Material Lot: {genealogy['raw_material_lot']}
├── Supplier: {genealogy['supplier']}
├── Operator: {genealogy['operator']}
├── Reactor ID: {genealogy['reactor_id']}
├── Cleaning Cycle: {genealogy['cleaning_cycle']}
├── Previous Batch: {genealogy['previous_batch']}
└── Packaging Lot: {genealogy['packaging_lot']}
"""

    st.code(genealogy_text)

    st.markdown("### GMP Traceability Table")

    genealogy_df = pd.DataFrame({
        "Category": [
            "Raw Material Lot",
            "Supplier",
            "Operator",
            "Reactor ID",
            "Cleaning Cycle",
            "Previous Batch",
            "Packaging Lot",
        ],
        "Value": [
            genealogy["raw_material_lot"],
            genealogy["supplier"],
            genealogy["operator"],
            genealogy["reactor_id"],
            genealogy["cleaning_cycle"],
            genealogy["previous_batch"],
            genealogy["packaging_lot"],
        ]
    })

    st.dataframe(genealogy_df, use_container_width=True)

    st.markdown("### Traceability Assessment")

    st.success("All upstream and downstream genealogy links are connected.")

    st.warning(
        "This genealogy module simulates MES-style manufacturing traceability workflows used in regulated pharma environments."
    )

    if st.button(
        "Record Genealogy Review",
        disabled=st.session_state.user_role not in ["Admin", "QA Manager", "Process Engineer"],
    ):

        add_audit_event(
            event="Batch genealogy review completed",
            batch=genealogy_batch,
            details=f"Traceability score: {genealogy['traceability_score']}/100",
        )

        st.success("Genealogy review recorded in audit trail.")



# ============================================================
# Tab 16: AI Process Optimization
# ============================================================

with tab16:
    st.subheader("AI Process Optimization Engine")

    st.info(
        "Simulate smart manufacturing optimization for yield improvement, "
        "temperature tuning, pressure stability, energy efficiency, and process consistency."
    )

    optimization_batch = st.selectbox(
        "Select Batch for Process Optimization",
        df["batch_number"].tolist(),
        key="process_optimization_batch",
    )

    optimization_row = df[df["batch_number"] == optimization_batch].iloc[0]

    optimization = generate_process_optimization(optimization_row)
    optimization_report = format_process_optimization_report(optimization)

    st.markdown("### Optimization Summary")

    opt_col1, opt_col2, opt_col3, opt_col4 = st.columns(4)

    opt_col1.metric(
        "Optimization Score",
        f"{optimization['optimization_score']}/100",
    )

    opt_col2.metric(
        "Category",
        optimization["optimization_category"],
    )

    opt_col3.metric(
        "Yield Improvement",
        f"{optimization['yield_improvement_potential']}%",
    )

    opt_col4.metric(
        "AI Confidence",
        f"{optimization['confidence_score']}%",
    )

    st.markdown("### Process Optimization Progress")

    st.progress(optimization["optimization_score"] / 100)

    if optimization["optimization_category"] == "Optimized":
        st.success("Process is currently close to the optimized manufacturing window.")
    elif optimization["optimization_category"] == "Improvement Opportunity":
        st.warning("Moderate improvement opportunity detected.")
    else:
        st.error("Significant optimization opportunity detected. Process review recommended.")

    st.markdown("### Current vs Target Parameters")

    optimization_df = pd.DataFrame(
        {
            "Parameter": ["Temperature", "Pressure", "Yield"],
            "Current Value": [
                optimization["current_temperature"],
                optimization["current_pressure"],
                optimization["current_yield"],
            ],
            "Target Value": [
                optimization["target_temperature"],
                optimization["target_pressure"],
                optimization["target_yield"],
            ],
        }
    )

    st.dataframe(
        optimization_df,
        hide_index=True,
        use_container_width=True,
    )

    chart_df = pd.DataFrame(
        {
            "Parameter": [
                "Current Temperature",
                "Target Temperature",
                "Current Pressure x20",
                "Target Pressure x20",
                "Current Yield",
                "Target Yield",
                "Optimization Score",
            ],
            "Value": [
                optimization["current_temperature"],
                optimization["target_temperature"],
                optimization["current_pressure"] * 20,
                optimization["target_pressure"] * 20,
                optimization["current_yield"],
                optimization["target_yield"],
                optimization["optimization_score"],
            ],
        }
    )

    fig_optimization = px.bar(
        chart_df,
        x="Parameter",
        y="Value",
        text="Value",
        title=f"AI Process Optimization Profile — {optimization_batch}",
    )

    st.plotly_chart(
        fig_optimization,
        use_container_width=True,
    )

    st.markdown("### AI Process Optimization Recommendations")

    for action in optimization["optimization_actions"]:
        st.info(action)

    st.markdown("### Energy Optimization Assessment")

    if optimization["energy_saving_opportunity"] == "High":
        st.error("High energy-saving opportunity detected due to elevated process load.")
    elif optimization["energy_saving_opportunity"] == "Medium":
        st.warning("Moderate energy-saving opportunity detected.")
    else:
        st.success("Low energy-saving opportunity. Current energy profile appears acceptable.")

    st.markdown("### AI Process Optimization Report")

    st.text_area(
        "Generated Optimization Report",
        optimization_report,
        height=520,
    )

    st.download_button(
        label="Download Process Optimization Report",
        data=optimization_report,
        file_name=f"{optimization_batch}_process_optimization_report.txt",
        mime="text/plain",
    )

    if st.button(
        "Record Process Optimization Review",
        disabled=st.session_state.user_role not in ["Admin", "Process Engineer"],
    ):
        add_audit_event(
            event="AI process optimization review completed",
            batch=optimization_batch,
            details=f"Optimization score: {optimization['optimization_score']}/100 | Category: {optimization['optimization_category']}",
        )

        st.success("Process optimization review recorded in audit trail.")




# ============================================================
# Tab 17: AI Batch Failure Prediction
# ============================================================

with tab17:
    st.subheader("AI Batch Failure Prediction Engine")

    st.info(
        "Predict batch failure probability, release risk, yield-loss risk, "
        "process drift factors, and preventive actions before final QA disposition."
    )

    prediction_batch = st.selectbox(
        "Select Batch for Failure Prediction",
        df["batch_number"].tolist(),
        key="batch_failure_prediction_batch",
    )

    prediction_row = df[df["batch_number"] == prediction_batch].iloc[0]

    prediction = generate_batch_failure_prediction(prediction_row)
    prediction_report = format_batch_failure_prediction_report(prediction)

    st.markdown("### Failure Prediction Summary")

    pred_col1, pred_col2, pred_col3, pred_col4 = st.columns(4)

    pred_col1.metric(
        "Failure Probability",
        f"{prediction['failure_probability']}%",
    )

    pred_col2.metric(
        "Risk Level",
        prediction["failure_risk_level"],
    )

    pred_col3.metric(
        "Predicted Yield Loss",
        f"{prediction['predicted_yield_loss']}%",
    )

    pred_col4.metric(
        "AI Confidence",
        f"{prediction['ai_confidence']}%",
    )

    st.markdown("### Failure Probability Progress")

    st.progress(prediction["failure_probability"] / 100)

    if prediction["failure_risk_level"] == "High":
        st.error("High predicted failure risk. Immediate QA/process engineering review recommended.")
    elif prediction["failure_risk_level"] == "Medium":
        st.warning("Medium predicted failure risk. Preventive review recommended.")
    else:
        st.success("Low predicted failure risk. Continue routine monitoring.")

    st.markdown("### Predicted Release Risk")

    if prediction["release_risk"] == "Likely Hold / Investigation":
        st.error(prediction["release_risk"])
    elif prediction["release_risk"] == "QA Review Recommended":
        st.warning(prediction["release_risk"])
    else:
        st.success(prediction["release_risk"])

    st.markdown("### Detected Process Drift Factor(s)")

    for factor in prediction["drift_factors"]:
        st.info(factor)

    st.markdown("### Recommended Preventive Action(s)")

    for action in prediction["preventive_actions"]:
        st.warning(action)

    st.markdown("### Prediction Profile Chart")

    prediction_chart_df = pd.DataFrame(
        {
            "Metric": [
                "Failure Probability",
                "Predicted Yield Loss",
                "AI Confidence",
            ],
            "Value": [
                prediction["failure_probability"],
                prediction["predicted_yield_loss"],
                prediction["ai_confidence"],
            ],
        }
    )

    fig_prediction = px.bar(
        prediction_chart_df,
        x="Metric",
        y="Value",
        text="Value",
        title=f"AI Batch Failure Prediction Profile — {prediction_batch}",
    )

    st.plotly_chart(
        fig_prediction,
        use_container_width=True,
    )

    st.markdown("### AI Batch Failure Prediction Report")

    st.text_area(
        "Generated Failure Prediction Report",
        prediction_report,
        height=520,
    )

    st.download_button(
        label="Download Failure Prediction Report",
        data=prediction_report,
        file_name=f"{prediction_batch}_failure_prediction_report.txt",
        mime="text/plain",
    )

    if st.button(
        "Record Failure Prediction Review",
        disabled=st.session_state.user_role not in ["Admin", "QA Manager", "Process Engineer"],
    ):
        add_audit_event(
            event="AI batch failure prediction review completed",
            batch=prediction_batch,
            details=f"Failure probability: {prediction['failure_probability']}% | Risk: {prediction['failure_risk_level']}",
        )

        st.success("Failure prediction review recorded in audit trail.")




# ============================================================
# Tab 18: AI Manufacturing Copilot
# ============================================================

with tab18:

    st.subheader("AI Manufacturing Copilot")

    st.info(
        "Conversational AI assistant for manufacturing troubleshooting, GMP guidance, QA support, and process investigations."
    )

    copilot_batch = st.selectbox(
        "Select Batch Context",
        df["batch_number"].tolist(),
        key="copilot_batch"
    )

    selected_batch = df[df["batch_number"] == copilot_batch].iloc[0]

    st.markdown("### Example Questions")

    st.code(
        """Why is reactor pressure increasing?
Suggest CAPA for low yield.
Explain possible causes of process drift.
Should this batch be released?
What GMP risks exist in this batch?"""
    )

    user_prompt = st.text_area(
        "Ask AI Manufacturing Copilot",
        height=140,
        placeholder="Ask a manufacturing, QA, deviation, or GMP question..."
    )

    if st.button("Generate AI Copilot Response"):

        if user_prompt.strip() == "":
            st.warning("Please enter a question.")
        else:

            response = generate_copilot_response(
                user_prompt,
                selected_batch
            )

            st.markdown("### AI Copilot Response")

            st.success(response)

            st.markdown("### Copilot Context")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Temperature",
                f"{selected_batch['temperature']} °C"
            )

            col2.metric(
                "Pressure",
                selected_batch["pressure"]
            )

            col3.metric(
                "Yield",
                f"{selected_batch['yield_percent']}%"
            )

            st.download_button(
                label="Download Copilot Response",
                data=response,
                file_name=f"{copilot_batch}_copilot_response.txt",
                mime="text/plain"
            )



# ============================================================
# Tab 19: AI Digital Twin Simulation
# ============================================================

with tab19:
    st.subheader("AI Digital Twin Simulation")

    st.info(
        "Simulate virtual reactor parameter changes and estimate their impact on yield, risk, and process stability."
    )

    twin_batch = st.selectbox(
        "Select Batch for Digital Twin Simulation",
        df["batch_number"].tolist(),
        key="digital_twin_batch",
    )

    twin_row = df[df["batch_number"] == twin_batch].iloc[0]

    st.markdown("### Simulation Controls")

    control_col1, control_col2 = st.columns(2)

    with control_col1:
        temperature_adjustment = st.slider(
            "Temperature Adjustment (°C)",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.5,
        )

    with control_col2:
        pressure_adjustment = st.slider(
            "Pressure Adjustment",
            min_value=-1.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
        )

    simulation = run_digital_twin_simulation(
        twin_row,
        temperature_adjustment,
        pressure_adjustment,
    )

    simulation_report = format_digital_twin_report(simulation)

    st.markdown("### Digital Twin Scenario Summary")

    dt_col1, dt_col2, dt_col3, dt_col4 = st.columns(4)

    dt_col1.metric(
        "Predicted Yield",
        f"{simulation['simulated_yield']}%",
        delta=f"{simulation['yield_change']}%",
    )

    dt_col2.metric(
        "Simulated Risk",
        f"{simulation['simulated_risk']}/100",
    )

    dt_col3.metric(
        "Scenario Status",
        simulation["scenario_status"],
    )

    dt_col4.metric(
        "Batch",
        simulation["batch_number"],
    )

    st.markdown("### Risk Progress")

    st.progress(simulation["simulated_risk"] / 100)

    if simulation["scenario_status"] == "High-Risk Scenario":
        st.error("Digital twin predicts a high-risk manufacturing scenario.")
    elif simulation["scenario_status"] == "Moderate-Risk Scenario":
        st.warning("Digital twin predicts a moderate-risk process scenario.")
    else:
        st.success("Digital twin predicts a stable process scenario.")

    st.markdown("### Baseline vs Simulated Parameters")

    twin_df = pd.DataFrame(
        {
            "Parameter": ["Temperature", "Pressure", "Yield", "Risk"],
            "Baseline": [
                simulation["base_temperature"],
                simulation["base_pressure"],
                simulation["base_yield"],
                calculate_risk_score(twin_row),
            ],
            "Simulated": [
                simulation["simulated_temperature"],
                simulation["simulated_pressure"],
                simulation["simulated_yield"],
                simulation["simulated_risk"],
            ],
        }
    )

    st.dataframe(
        twin_df,
        hide_index=True,
        use_container_width=True,
    )

    chart_df = pd.DataFrame(
        {
            "Metric": [
                "Baseline Yield",
                "Simulated Yield",
                "Baseline Risk",
                "Simulated Risk",
            ],
            "Value": [
                simulation["base_yield"],
                simulation["simulated_yield"],
                calculate_risk_score(twin_row),
                simulation["simulated_risk"],
            ],
        }
    )

    fig_twin = px.bar(
        chart_df,
        x="Metric",
        y="Value",
        text="Value",
        title=f"Digital Twin Scenario — {twin_batch}",
    )

    st.plotly_chart(
        fig_twin,
        use_container_width=True,
    )

    st.markdown("### AI Digital Twin Report")

    st.text_area(
        "Generated Digital Twin Report",
        simulation_report,
        height=420,
    )

    st.download_button(
        label="Download Digital Twin Report",
        data=simulation_report,
        file_name=f"{twin_batch}_digital_twin_report.txt",
        mime="text/plain",
    )

    if st.button(
        "Record Digital Twin Simulation",
        disabled=st.session_state.user_role not in ["Admin", "Process Engineer"],
    ):
        add_audit_event(
            event="AI digital twin simulation completed",
            batch=twin_batch,
            details=f"Scenario: {simulation['scenario_status']} | Yield change: {simulation['yield_change']}%",
        )

        st.success("Digital twin simulation recorded in audit trail.")



st.caption(
    "Pharma Manufacturing Intelligence Dashboard | "
    "Built with Python, Pandas, Streamlit, FastAPI, PostgreSQL, "
    "OpenAI API, ChromaDB, Plotly, AI trend prediction, live monitoring, equipment monitoring, executive demo mode, and GMP-inspired RAG workflows"
)
