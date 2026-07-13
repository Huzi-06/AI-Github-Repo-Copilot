# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in ANTHROPIC_API_KEY
uvicorn main:app --reload     # starts on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # starts on http://localhost:5173
```

### Both together (two terminals)
```bash
# terminal 1
cd backend && uvicorn main:app --reload
# terminal 2
cd frontend && npm run dev
```

Health check: `curl http://localhost:8000/health`
List indexed repos: `curl http://localhost:8000/repos`

## Architecture

### Data flow
1. **Ingest** (`POST /ingest`): GitHub API fetches repo metadata, file tree, commits, issues → text chunked (1200 chars, 200 overlap) → embedded with `all-MiniLM-L6-v2` (384-dim) → stored in `faiss.IndexFlatIP` (cosine similarity) in-memory
2. **Q&A** (`POST /qa`): query embedded → top-5 chunks retrieved → injected into Claude prompt
3. **README / Architecture** (`POST /readme`, `POST /architecture`): 3 different search queries for diverse context → deduplicated chunks → Claude prompt
4. **Tests** (`POST /tests`): searches for target file + test patterns → Claude prompt with framework detection

### Backend structure (`backend/`)
- `main.py` — FastAPI app, all routes, `_stores: dict[str, VectorStore]`, `_metadata: dict[str, dict]`
- `github_client.py` — async GitHub REST client; parallel fetch with `asyncio.Semaphore(10)`; filters binary files, large files (>80KB), and noise dirs (`node_modules`, `vendor`, `dist`)
- `vectorstore.py` — FAISS index wrapper; lazy singleton embedding model
- `claude_client.py` — thin `AsyncAnthropic` wrapper; reads model from `CLAUDE_MODEL` env var
- `prompts.py` — all system/user prompt strings
- `models.py` — Pydantic request schemas

### Frontend structure (`frontend/src/`)
- `App.jsx` — root; manages `isIngested` state, tab switching, repo reset
- `api/client.js` — all `fetch` calls; Vite proxies `/api/*` → `http://localhost:8000/*`
- `components/RepoInput.jsx` — URL form with animated ingestion progress steps
- `components/ChatInterface.jsx` — scrollable chat, suggestion chips, react-markdown for assistant messages
- `components/ReadmeTab.jsx`, `TestsTab.jsx`, `ArchitectureTab.jsx` — generate + copy-to-clipboard panels

### Key environment variables
| Variable | Required | Default |
|---|---|---|
| `GROQ_API_KEY` | Yes | — |
| `GITHUB_TOKEN` | No | — (60 req/hr without it) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` |

### State management
All repo data is stored in Python dicts in `main.py` (`_stores`, `_metadata`) — purely in-memory, lost on restart. No database. Re-ingest to reload after restart.
