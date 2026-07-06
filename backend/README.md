# SupportMind — Backend Setup Guide

FastAPI backend for the SupportMind Intelligent Customer Support AI Assistant.

---

## Requirements

| Tool | Minimum Version |
|---|---|
| Python | 3.11 |
| pip | 23+ |

---

## Quick Start

### 1. Clone and navigate

```bash
git clone <repo-url>
cd SupportMind/backend
```

### 2. Create a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and configure your `OLLAMA_BASE_URL`. All other values have safe defaults for local development.

### 5. Run the development server

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**.

---

## Available Endpoints (Phase 1)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Liveness check — returns 200 when the server is running |
| `GET` | `/api/v1/health/ready` | Readiness check — validates ChromaDB directory |
| `GET` | `/docs` | Swagger UI (interactive API documentation) |
| `GET` | `/redoc` | ReDoc API documentation |
| `POST` | `/api/v1/documents/upload` | Upload a document *(stub — Phase 2)* |
| `GET` | `/api/v1/documents/` | List indexed documents *(stub — Phase 2)* |
| `DELETE` | `/api/v1/documents/{doc_id}` | Delete a document *(stub — Phase 2)* |
| `POST` | `/api/v1/chat/message` | Send a chat message *(stub — Phase 3)* |
| `GET` | `/api/v1/chat/history/{session_id}` | Get conversation history *(stub — Phase 3)* |

---

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py               # Aggregates all v1 endpoint routers
│   │       └── endpoints/
│   │           ├── health.py           # GET /health, GET /health/ready
│   │           ├── documents.py        # Document upload, list, delete
│   │           └── chat.py             # Chat message, history
│   ├── core/
│   │   ├── config.py                   # pydantic-settings Settings class
│   │   ├── logging.py                  # Structured JSON logging
│   │   └── exceptions.py              # Typed domain exception hierarchy
│   ├── schemas/
│   │   └── common.py                   # Shared Pydantic response models
│   ├── services/                       # Business logic (Phase 2 & 3)
│   ├── utils/
│   │   ├── file_utils.py               # File validation helpers
│   │   └── text_utils.py               # Text preprocessing helpers
│   └── main.py                         # App factory, CORS, exception handlers
├── requirements.txt
├── .env.example
└── README.md
```

---

## Environment Variables Reference

| Variable | Default | Required | Description |
|---|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | No | Base URL for local Ollama instance |
| `OLLAMA_CHAT_MODEL` | `llama3.2:3b` | No | LLM model for answer generation |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | No | Embedding model for indexing |
| `CHROMA_PERSIST_DIR` | `./chromadb_data` | No | ChromaDB persistence directory |
| `CHUNK_SIZE` | `800` | No | Text chunk size in tokens |
| `CHUNK_OVERLAP` | `150` | No | Overlap between consecutive chunks |
| `RETRIEVAL_TOP_K` | `5` | No | Chunks retrieved per query |
| `SIMILARITY_THRESHOLD` | `0.35` | No | Minimum similarity score to include a chunk |
| `MAX_UPLOAD_SIZE_MB` | `10` | No | Maximum file upload size |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | No | CORS allowed origins (JSON array) |
| `LOG_LEVEL` | `INFO` | No | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `DEBUG` | `false` | No | Enables FastAPI debug mode |

---

## Verify Your Setup

After starting the server, run:

```bash
# Liveness
curl http://localhost:8000/api/v1/health

# Readiness (checks ChromaDB dir)
curl http://localhost:8000/api/v1/health/ready
```

Expected liveness response:
```json
{
  "status": "ok",
  "app_name": "SupportMind API",
  "version": "0.1.0"
}
```

---

## Logging

All log output is structured JSON (one object per line), written to stdout. Example:

```json
{
  "timestamp": "2026-07-05T16:00:00+00:00",
  "level": "INFO",
  "logger": "app.main",
  "message": "application_startup",
  "app_name": "SupportMind API",
  "version": "0.1.0"
}
```

---

## What's Next

| Phase | Work |
|---|---|
| **Phase 2** | Document parsing, chunking, embedding, ChromaDB ingestion |
| **Phase 3** | LCEL RAG chain, similarity gate, `RunnableWithMessageHistory` |
| **Phase 4** | React + Vite frontend |
