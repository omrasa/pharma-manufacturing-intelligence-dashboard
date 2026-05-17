# Optional Cloud Deployment Guide

## Recommended Platforms

### Beginner-Friendly
- Streamlit Community Cloud
- Render
- Railway

### Professional
- AWS
- Azure
- Google Cloud

---

# Recommended First Deployment

## Streamlit Community Cloud

### Step 1
Push project to GitHub.

### Step 2
Open:

https://share.streamlit.io

### Step 3
Connect GitHub repository.

### Step 4
Select:

```text
streamlit_app.py
```

### Step 5
Add secrets:

```text
OPENAI_API_KEY=your_key
```

### Step 6
Deploy.

---

# Production Architecture (Future)

```text
Users
  ↓
NGINX Load Balancer
  ↓
Streamlit Frontend
  ↓
FastAPI Backend
  ↓
PostgreSQL Database
  ↓
Cloud Storage / Monitoring
```
