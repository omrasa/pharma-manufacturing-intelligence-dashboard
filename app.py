import psycopg2
import pandas as pd

print("Connecting to Pharma Database...")

connection = psycopg2.connect(
    host="localhost",
    database="pharma_dashboard",
    user="saifullah",
    password=""
)

query = """
SELECT *
FROM batches;
"""

df = pd.read_sql(query, connection)

print("Database connected successfully!")
print("\nBatch Summary:\n")

print(df[[
    "batch_number",
    "product_name",
    "temperature",
    "pressure",
    "yield_percent",
    "status"
]])


print("\nPotential Process Alerts:\n")

for index, row in df.iterrows():

    if row["temperature"] > 40:
        print(f"⚠️ High Temperature Alert in {row['batch_number']}")

    if row["yield_percent"] < 90:
        print(f"⚠️ Low Yield Alert in {row['batch_number']}")
    if row["pressure"] > 2:
        print(f"⚠️ High Pressure Alert in {row['batch_number']}")
    if row["temperature"] > 40 and row["yield_percent"] < 90:
        print(f"🚨 CRITICAL RISK in {row['batch_number']}")
    if (
        row["temperature"] <= 40
        and row["yield_percent"] >= 90
        and row["pressure"] <= 2
    ):
        print(f"✅ SAFE BATCH: {row['batch_number']}")
connection.close()