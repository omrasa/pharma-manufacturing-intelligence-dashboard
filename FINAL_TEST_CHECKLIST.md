# Final Test Checklist

## Startup

Terminal 1:

```bash
source pharma_env/bin/activate
uvicorn api:app --reload
```

Terminal 2:

```bash
source pharma_env/bin/activate
streamlit run streamlit_app.py
```

## Test Login

```text
admin / admin123
```

## Test Core Tabs

- Overview loads
- Risk & Alerts loads
- Deviation Management loads
- QA / CAPA loads
- Reports loads
- RAG QA Assistant loads
- Audit Trail loads
- Batch Comparison loads
- AI Deviation Report loads
- AI Trend Prediction loads
- Live Manufacturing Monitor loads
- Equipment Monitoring loads
- Executive Demo Center loads
- AI Root Cause Investigation loads
- Batch Genealogy loads
- AI Process Optimization loads
- AI Batch Failure Prediction loads
- AI Manufacturing Copilot loads

## Test Download Buttons

- QA PDF report
- AI deviation report
- root cause report
- process optimization report
- failure prediction report
- copilot response

## Test Audit Trail

Click at least one record button and verify the audit trail updates.

## Final Success Criteria

- No red error screens
- Backend terminal shows no tracebacks
- Frontend terminal shows no tracebacks
- All tabs open
- Core charts render
- Reports download
- Login/logout works
