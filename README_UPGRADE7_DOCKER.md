# Upgrade 7 — Docker Deployment Package

## Upgrade Tracker

✅ Upgrade 1: Plotly professional charts  
✅ Upgrade 2: AI-generated deviation report  
✅ Upgrade 3: AI Manufacturing Trend Prediction  
✅ Upgrade 4: Predictive Maintenance & Equipment Monitoring  
✅ Upgrade 5: Live Manufacturing Monitoring  
✅ Upgrade 6: Enterprise Authentication & User Roles  
✅ Upgrade 7: Docker deployment files  

## Files Included

- Dockerfile
- Dockerfile.api
- docker-compose.yml
- requirements.txt
- .dockerignore
- .env.example

## How to Use

Copy these files into your project folder:

```text
pharma_project/
```

Your folder should contain:

```text
streamlit_app.py
api.py
Dockerfile
Dockerfile.api
docker-compose.yml
requirements.txt
.dockerignore
.env
```

## Step 1 — Create .env

Rename:

```text
.env.example
```

to:

```text
.env
```

Add your OpenAI key:

```text
OPENAI_API_KEY=your_real_key_here
```

## Step 2 — Build and Run

From the project folder, run:

```bash
docker compose up --build
```

## Step 3 — Open Apps

Frontend:

```text
http://localhost:8501
```

Backend:

```text
http://localhost:8000/docs
```

## Important Note

Your current app uses local API URLs inside `streamlit_app.py`:

```python
API_URL = "http://127.0.0.1:8000/batches"
```

For Docker, the Streamlit app should read environment variables instead:

```python
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/batches")
RISK_URL = os.getenv("RISK_URL", "http://127.0.0.1:8000/risk-summary")
DEVIATION_URL = os.getenv("DEVIATION_URL", "http://127.0.0.1:8000/auto-deviations")
```

If your current `streamlit_app.py` does not use this yet, this will be the next small correction.

## Next Upgrade

➡️ Upgrade 8: GitHub README + Architecture Documentation
