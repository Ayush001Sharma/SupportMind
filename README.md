# SupportMind

This is a take-home assignment implementing an end-to-end Retrieval-Augmented Generation (RAG) system. The project provides an AI assistant that can answer questions based on documents uploaded by the user.

All inference runs locally using Ollama. There are no paid API dependencies.

## Features

- **Document Upload:** Supports uploading PDF, DOCX, and TXT files.
- **Local RAG:** Uses local embeddings and a local LLM for inference.
- **Chat Interface:** A React-based frontend to interact with the assistant and see citations.
- **Session Memory:** Retains conversation context per session.
- **Context Sanitization:** Filters common prompt injection phrases from retrieved chunks.

## Project Architecture

The backend is structured to separate concerns. This keeps the code modular and makes it easier to test or swap out providers.

The flow works like this:
1. **Document Upload:** The API receives the file and hands it off to a document service to validate and save it.
2. **Processing:** Text is extracted from the raw file formats and cleaned up (e.g. normalizing whitespace).
3. **Chunking:** The cleaned text is split into smaller, semantic chunks so that they fit into the LLM context window.
4. **Vector Storage:** Chunks are embedded and stored in ChromaDB.
5. **Retrieval:** When a user asks a question, the retrieval service pulls the most relevant chunks from ChromaDB and filters them by a similarity threshold.
6. **RAG Generation:** The RAG service sanitizes the retrieved chunks, builds the prompt, and passes it to the LLM to generate an answer.
7. **Conversation Memory:** A memory service keeps track of recent messages per session so the LLM understands follow-up questions.
8. **Response:** The chat endpoint returns the generated answer along with the source citations.

## Tech Stack

**Backend:**
- Python
- FastAPI
- LangChain (`langchain-ollama`)
- ChromaDB
- Pytest

**Frontend:**
- React (Vite)
- TypeScript
- Tailwind CSS
- Vitest & React Testing Library

**Inference:**
- Ollama

## Folder Structure

```
SupportMind/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── core/         # Config, exceptions, logging
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # Business logic (RAG, chunking, retrieval)
│   │   └── utils/        # Text cleaning helpers
│   └── tests/            # Pytest test suite
└── frontend/
    ├── src/
    │   ├── components/   # UI components (chat, upload)
    │   ├── context/      # React context (session state)
    │   ├── hooks/        # Custom hooks for API interaction
    │   ├── utils/        # Session ID management
    │   └── __tests__/    # Frontend tests
```

## Setup

### 1. Prerequisites
You will need Python 3.11+, Node.js (v18+), and Ollama installed.

### 2. Ollama & Models
Make sure Ollama is running, then pull the required models:
```bash
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

### 3. Backend
Navigate to the `backend` directory, set up a virtual environment, and install dependencies:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the example environment file:
```bash
cp .env.example .env
```
*(The defaults in `.env` are configured to point to standard local Ollama and ChromaDB paths).*

### 4. Frontend
Navigate to the `frontend` directory and install dependencies:
```bash
cd frontend
npm install
```

## Running the Project

Start the backend (from the `backend` directory with the virtual environment activated):
```bash
fastapi dev app/main.py
```
The API will be available at `http://localhost:8000`.

Start the frontend (from the `frontend` directory):
```bash
npm run dev
```
The app will be available at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Upload and process a document (PDF, DOCX, TXT) |
| `POST` | `/api/v1/chat/message` | Send a message to the assistant and get a response |

*Stub endpoints for `GET` and `DELETE` on `/api/v1/documents` are also present but currently return `501 Not Implemented`.*

## Testing

The project includes an automated testing suite for both the frontend and backend. External dependencies (like Ollama and ChromaDB) are completely mocked out during tests so they run quickly and deterministically.

**Run backend tests:**
```bash
cd backend
pytest tests/ -v
```

**Run frontend tests:**
```bash
cd frontend
npm test
```

All tests are currently passing.

## Design Decisions

- **Local Inference:** I migrated the stack from OpenAI to Ollama. This ensures the project can be run entirely offline without needing paid API keys.
- **Separation of Concerns:** Retrieval logic is separated from RAG generation logic. This makes it easier to test them in isolation and prevents the RAG service from being tightly coupled to ChromaDB.
- **Thin Routers:** FastAPI route handlers do almost nothing except receive the request and pass it to a service layer. This keeps the HTTP logic decoupled from business logic.
- **In-Memory History:** Chat history is maintained in memory per session ID. This was chosen for simplicity during the assignment, but it is abstracted behind a service so it can be swapped for a database later.

## Known Limitations

- **Volatile Memory:** Conversation history is stored in memory. Restarting the backend will clear all ongoing chat contexts.
- **No Streaming:** The chat endpoint waits for the LLM to finish generating the entire response before returning it.
- **Synchronous Ingestion:** Document processing and indexing happen inline during the HTTP request. Uploading a very large document might time out the request.
- **No Auth:** There is no authentication or multi-tenant isolation. All users query the same ChromaDB collection.

## Future Improvements

- **Streaming Responses:** Implementing Server-Sent Events (SSE) on the `/chat/message` endpoint to stream tokens to the frontend as they generate.
- **Background Jobs:** Moving document ingestion into an asynchronous worker queue (like Celery) so the upload API can return immediately.
- **Persistent Storage:** Storing chat history and document metadata in a relational database (like PostgreSQL or SQLite).
- **Hybrid Search:** Adding keyword search (BM25) alongside vector search to improve retrieval accuracy for specific nouns or part numbers.

## License

MIT
