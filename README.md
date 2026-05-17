# Upgrade 11 — Cloud Deployment Readiness

## Upgrade Tracker

✅ Upgrade 1: Plotly charts  
✅ Upgrade 2: AI deviation report  
✅ Upgrade 3: AI trend prediction  
✅ Upgrade 4: Equipment monitoring  
✅ Upgrade 5: Live manufacturing monitor  
✅ Upgrade 6: Authentication & roles  
✅ Upgrade 7: Docker deployment  
✅ Upgrade 8: GitHub documentation  
✅ Upgrade 9: GitHub deployment package  
✅ Upgrade 10: Executive demo center  
✅ Upgrade 11: Cloud deployment readiness  

## What This Upgrade Adds

- Cloud Deployment tab
- Environment-variable-based API URLs
- Cloud readiness checklist
- Deployment instructions inside the app
- Downloadable cloud instructions
- Render deployment file
- Procfiles for cloud platforms
- Runtime file

## How to Use

1. Rename:

```text
streamlit_app_upgrade11_cloud_ready.py
```

to:

```text
streamlit_app.py
```

2. Replace your current file.

3. Restart Streamlit:

```bash
streamlit run streamlit_app.py
```

4. Login:

```text
admin / admin123
```

5. Open:

```text
Cloud Deployment
```

## Important

The app now uses:

```python
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/batches")
RISK_URL = os.getenv("RISK_URL", "http://127.0.0.1:8000/risk-summary")
DEVIATION_URL = os.getenv("DEVIATION_URL", "http://127.0.0.1:8000/auto-deviations")
```

This makes it ready for cloud deployment.

## Next Upgrade

Upgrade 12: Database-backed audit trail and user activity logging.
