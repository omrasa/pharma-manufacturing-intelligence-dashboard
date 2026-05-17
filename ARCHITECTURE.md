# System Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        User / Browser                         │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                        │
│                                                              │
│  - Login & user roles                                        │
│  - Overview dashboard                                        │
│  - Risk & alerts                                             │
│  - QA/CAPA workflow                                          │
│  - AI deviation report                                       │
│  - RAG QA assistant                                          │
│  - Live monitoring                                           │
│  - Equipment monitoring                                      │
│  - Audit trail                                               │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP requests
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                         │
│                                                              │
│  GET /batches                                                │
│  GET /risk-summary                                           │
│  GET /auto-deviations                                        │
└──────────────────────────────┬───────────────────────────────┘
                               │ SQL queries
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                      │
│                                                              │
│  - batches                                                   │
│  - deviations                                                │
│  - CAPA actions                                              │
│  - process parameters                                        │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│                          AI Layer                             │
│                                                              │
│  OpenAI API                                                  │
│  LangChain                                                   │
│  ChromaDB vector store                                       │
│  GMP/CAPA knowledge base                                     │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

1. User logs in through Streamlit.
2. Streamlit calls FastAPI endpoints.
3. FastAPI retrieves manufacturing data from PostgreSQL.
4. Streamlit calculates risk scores, release recommendations, and CAPA actions.
5. RAG assistant retrieves relevant knowledge chunks from ChromaDB.
6. AI-assisted outputs are displayed in the dashboard.
7. Key actions are recorded in the audit trail.
