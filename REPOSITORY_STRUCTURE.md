# Recommended Repository Structure

```text
pharma_project/
│
├── streamlit_app.py
├── api.py
├── requirements.txt
├── Dockerfile
├── Dockerfile.api
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── README.md
├── ARCHITECTURE.md
├── INTERVIEW_STORY.md
│
├── database/
│   └── database_setup.sql
│
├── knowledge_base/
│   └── capa_guidance.txt
│
├── chroma_db/
│
├── backend/
│
├── frontend/
│
├── services/
│
└── utils/
```

## GitHub Upload Notes

Do NOT upload:

```text
.env
pharma_env/
__pycache__/
*.pdf
```

Make sure `.gitignore` excludes these files.
