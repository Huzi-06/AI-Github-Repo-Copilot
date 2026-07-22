# AI GitHub Repo Copilot

An AI-powered assistant that lets you point at any public GitHub repo and instantly chat with it — ask questions about the codebase, generate a README, get an architecture overview, or scaffold tests, all grounded in the actual repo content via retrieval-augmented generation (RAG).

## Features

- **Ingest any public repo** — fetches file tree, commits, and issues via the GitHub API
- **Chat with the codebase** — ask natural-language questions, get answers grounded in real code (RAG, not hallucination)
- **Auto-generate a README** — pulls diverse context via multiple search queries, then drafts one
- **Architecture overview** — summarizes structure and data flow
- **Test scaffolding** — detects the test framework in use and generates relevant test cases

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Python |
| Vector search | FAISS (`IndexFlatIP`, cosine similarity) |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` (384-dim) |
| LLM | Claude (Anthropic API, `claude-sonnet-5` by default) |
| Frontend | React + Vite |
| Data source | GitHub REST API |

## Architecture

1. **Ingest** (`POST /ingest`) — GitHub API fetches repo metadata, file tree, commits, and issues → text is chunked (1200 chars, 200 overlap) → embedded → stored in an in-memory FAISS index
2. **Q&A** (`POST /qa`) — query is embedded → top-5 relevant chunks retrieved → injected into the LLM prompt
3. **README / Architecture** (`POST /readme`, `POST /architecture`) — three separate search queries pull diverse context, deduplicated, then passed to the LLM
4. **Tests** (`POST /tests`) — searches for the target file plus existing test patterns, detects the framework in use, and prompts accordingly

All repo data is stored in-memory (Python dicts) — nothing persists across a backend restart; re-ingest the repo to reload it.

## Project Structure

```
backend/
├── main.py           # FastAPI app, all routes
├── github_client.py  # async GitHub REST client (parallel fetch, filters binaries/large files)
├── vectorstore.py     # FAISS index wrapper
├── claude_client.py   # thin AsyncAnthropic (Claude) wrapper
├── prompts.py         # system/user prompt strings
└── models.py           # Pydantic request schemas

frontend/src/
├── App.jsx                    # root component, tab switching, ingestion state
├── api/client.js               # all fetch calls to the backend
└── components/
    ├── RepoInput.jsx           # repo URL form + ingestion progress
    ├── ChatInterface.jsx        # chat UI
    ├── ReadmeTab.jsx
    ├── TestsTab.jsx
    └── ArchitectureTab.jsx
```

## Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your API key(s), see below
uvicorn main:app --reload     # starts on http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # starts on http://localhost:5173
```

### Run both (two terminals)

```bash
# terminal 1
cd backend && uvicorn main:app --reload

# terminal 2
cd frontend && npm run dev
```

Health check: `curl http://localhost:8000/health`
List indexed repos: `curl http://localhost:8000/repos`

### Environment Variables

| Variable | Required | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — |
| `GITHUB_TOKEN` | No | none (limited to 60 requests/hr without it) |
| `CLAUDE_MODEL` | No | `claude-sonnet-5` |
