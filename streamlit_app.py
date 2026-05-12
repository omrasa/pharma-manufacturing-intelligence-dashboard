import streamlit as st
import pandas as pd
from datetime import datetime

batch_data = {
    "id": [2, 3],
    "batch_number": ["B-1001", "B-1002"],
    "product_name": ["Vaccine-A", "Vaccine-B"],
    "manufacturing_date": ["2026-05-08", "2026-05-09"],
    "temperature": [37.5, 42.0],
    "pressure": [1.2, 2.5],
    "ph_level": [7.1, 6.8],
    "yield_percent": [95.4, 84.2],
    "status": ["Approved", "Approved"]
}

deviation_data = {
    "deviation_id": [1, 2],
    "batch_number": ["B-1002", "B-1002"],
    "product_name": ["Vaccine-B", "Vaccine-B"],
    "issue_type": ["High Temperature", "Low Yield"],
    "severity": ["Critical", "High"],
    "investigation_status": ["Open", "Open"],
    "description": [
        "Temperature exceeded operating limit",
        "Yield dropped below acceptable threshold"
    ],
    "detected_date": ["2026-05-09", "2026-05-09"]
}

df = pd.DataFrame(batch_data)
deviation_df = pd.DataFrame(deviation_data)

st.sidebar.title("Batch Filter")

search_batch = st.sidebar.text_input("Search Batch Number")

batch_options = ["All Batches"] + list(df["batch_number"])

selected_batch = st.sidebar.selectbox(
    "Select Batch",
    batch_options
)

if search_batch:
    filtered_df = df[
        df["batch_number"].str.contains(search_batch, case=False)
    ]

elif selected_batch == "All Batches":
    filtered_df = df

else:
    filtered_df = df[
        df["batch_number"] == selected_batch
    ]

st.title("Pharma Manufacturing Intelligence Dashboard")

st.write(
    "Public demo version showing batch monitoring, deviation tracking, "
    "CAPA recommendations, QA review, and GMP-inspired traceability."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Risk & Alerts",
    "Deviation Management",
    "QA / CAPA",
    "Reports"
])

with tab1:

    st.subheader("Key Manufacturing KPIs")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Batches", len(filtered_df))

    col2.metric(
        "Average Yield",
        f"{filtered_df['yield_percent'].mean():.1f}%"
    )

    col3.metric(
        "Max Temperature",
        f"{filtered_df['temperature'].max():.1f} °C"
    )

    st.subheader("Batch Data")
    st.dataframe(filtered_df)

    st.subheader("Yield Comparison")

    st.bar_chart(
        filtered_df.set_index("batch_number")["yield_percent"]
    )

    st.subheader("Temperature Trend")

    st.line_chart(
        filtered_df.set_index("batch_number")["temperature"]
    )

    st.subheader("Batch Health Score")

    for index, row in filtered_df.iterrows():

        health_score = 100

        if row["temperature"] > 40:
            health_score -= 25

        if row["pressure"] > 2:
            health_score -= 20

        if row["yield_percent"] < 90:
            health_score -= 30

        if health_score >= 80:
            st.success(f"{row['batch_number']} Health Score: {health_score}/100")

        elif health_score >= 60:
            st.warning(f"{row['batch_number']} Health Score: {health_score}/100")

        else:
            st.error(f"{row['batch_number']} Health Score: {health_score}/100")


with tab2:

    st.subheader("Live Manufacturing Risk Status")

    for index, row in filtered_df.iterrows():

        if row["temperature"] > 40 and row["yield_percent"] < 90:
            st.error(f"🔴 HIGH RISK — {row['batch_number']}")

        elif row["pressure"] > 2 or row["yield_percent"] < 90:
            st.warning(f"🟠 MEDIUM RISK — {row['batch_number']}")

        else:
            st.success(f"🟢 LOW RISK — {row['batch_number']}")

    st.subheader("Risk Trend")

    risk_data = []

    for index, row in filtered_df.iterrows():

        risk_score = 0

        if row["temperature"] > 40:
            risk_score += 25

        if row["pressure"] > 2:
            risk_score += 20

        if row["yield_percent"] < 90:
            risk_score += 30

        risk_data.append({
            "batch_number": row["batch_number"],
            "risk_score": risk_score
        })

    risk_df = pd.DataFrame(risk_data)

    st.line_chart(
        risk_df.set_index("batch_number")["risk_score"]
    )

    st.subheader("Process Alerts")

    for index, row in filtered_df.iterrows():

        if row["temperature"] > 40:
            st.error(f"High Temperature Alert in {row['batch_number']}")

        if row["yield_percent"] < 90:
            st.warning(f"Low Yield Alert in {row['batch_number']}")

        if row["pressure"] > 2:
            st.warning(f"High Pressure Alert in {row['batch_number']}")

    st.subheader("Batch Release Decision")

    for index, row in filtered_df.iterrows():

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

    dev_col2.metric(
        "Critical Deviations",
        len(deviation_df[deviation_df["severity"] == "Critical"])
    )

    dev_col3.metric(
        "Open Investigations",
        len(deviation_df[deviation_df["investigation_status"] == "Open"])
    )

    st.subheader("Deviation Management")

    st.dataframe(deviation_df)

    st.subheader("Deviations by Severity")

    severity_counts = deviation_df["severity"].value_counts()

    st.bar_chart(severity_counts)

    st.subheader("Severity Review")

    for index, row in deviation_df.iterrows():

        if row["severity"] == "Critical":
            st.error(f"CRITICAL: {row['issue_type']} in {row['batch_number']}")

        elif row["severity"] == "High":
            st.warning(f"HIGH: {row['issue_type']} in {row['batch_number']}")

        elif row["severity"] == "Medium":
            st.info(f"MEDIUM: {row['issue_type']} in {row['batch_number']}")

        else:
            st.success(f"LOW: {row['issue_type']} in {row['batch_number']}")

    st.subheader("Investigation Status Overview")

    status_counts = deviation_df["investigation_status"].value_counts()

    st.bar_chart(status_counts)

    st.subheader("CAPA Tracking")

    open_count = len(deviation_df[deviation_df["investigation_status"] == "Open"])
    closed_count = len(deviation_df[deviation_df["investigation_status"] == "Closed"])

    capa_col1, capa_col2 = st.columns(2)

    capa_col1.metric("Open Investigations", open_count)
    capa_col2.metric("Closed Investigations", closed_count)

    for index, row in deviation_df.iterrows():

        if row["investigation_status"] == "Open":
            st.warning(
                f"CAPA required for {row['batch_number']} — Investigation still OPEN"
            )

        else:
            st.success(
                f"CAPA completed for {row['batch_number']} — Investigation CLOSED"
            )


with tab4:

    st.subheader("Root Cause Analysis & CAPA Recommendation")

    for index, row in filtered_df.iterrows():

        st.write(f"### Batch {row['batch_number']}")

        if row["temperature"] > 40:
            st.error("Likely Root Cause: Reactor cooling instability")
            st.write("• Investigate reactor cooling system")

        if row["yield_percent"] < 90:
            st.warning("Likely Root Cause: Raw material variability or process loss")
            st.write("• Review raw material quality")

        if row["pressure"] > 2:
            st.warning("Likely Root Cause: Pressure control valve malfunction")
            st.write("• Inspect pressure control valve")

        if row["temperature"] > 40 and row["yield_percent"] < 90:
            st.error("Batch should be escalated to QA investigation")
            st.error(f"CRITICAL RISK detected in {row['batch_number']}")

    st.subheader("Operator Notes")

    operator_note = st.text_area(
        "Add operator or QA note for selected batch"
    )

    if st.button("Submit Note"):
        st.success("Note recorded successfully")
        st.write("Submitted note:")
        st.write(operator_note)

    st.subheader("QA Sign-Off")

    qa_name = st.text_input("QA Reviewer Name")

    qa_decision = st.selectbox(
        "QA Decision",
        ["Pending", "Approved", "Rejected", "Requires Investigation"]
    )

    if st.button("Submit QA Decision"):
        st.success("QA decision submitted")
        st.write(f"Reviewer: {qa_name}")
        st.write(f"Decision: {qa_decision}")


with tab5:

    st.subheader("Download Batch Report")

    report_text = f"""
Batch Report

Batch Number: {selected_batch}

Average Yield:
{filtered_df['yield_percent'].mean():.1f}%

Total Batches Displayed:
{len(filtered_df)}

Generated:
{datetime.now()}

This is a public demo version using sample manufacturing data.
"""

    st.download_button(
        label="Download Report",
        data=report_text,
        file_name=f"{selected_batch}_report.txt",
        mime="text/plain"
    )

    st.subheader("Audit Trail")

    current_time = datetime.now()

    st.write(f"Last dashboard review: {current_time}")

    st.write("Audit status: Traceability enabled")

st.markdown("---")

st.caption(
    "Pharma Manufacturing Intelligence Dashboard | "
    "Built with Python, Pandas, Streamlit, and GMP-inspired workflows"
)