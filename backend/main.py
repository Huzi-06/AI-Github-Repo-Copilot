import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from claude_client import ClaudeClient
from github_client import GitHubClient
from models import GenerateRequest, IngestRequest, QARequest
from prompts import (
    ARCHITECTURE_SYSTEM,
    ARCHITECTURE_USER,
    QA_SYSTEM,
    QA_USER,
    README_SYSTEM,
    README_USER,
    TEST_SYSTEM,
    TEST_USER,
)
from vectorstore import VectorStore, get_model

load_dotenv()

# In-memory stores keyed by repo URL
_stores: dict[str, VectorStore] = {}
_metadata: dict[str, dict] = {}

github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
claude = ClaudeClient(api_key=os.getenv("GROQ_API_KEY"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm the sentence-transformers model on startup
    # (downloads ~80MB all-MiniLM-L6-v2 on first run)
    get_model()
    yield


app = FastAPI(title="AI GitHub Repo Copilot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://ai-github-repo-copilot.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "indexed_repos": len(_stores)}


@app.get("/repos")
async def list_repos():
    """Return all currently indexed repositories."""
    return {
        "repos": [
            {
                "url": url,
                "repo": meta.get("full_name", url),
                "language": meta.get("language", ""),
                "stars": meta.get("stars", 0),
                "chunks": len(_stores[url].chunks),
            }
            for url, meta in _metadata.items()
        ]
    }


@app.post("/ingest")
async def ingest_repo(request: IngestRequest):
    """Fetch a GitHub repository and index it into FAISS for RAG."""
    repo_url = request.repo_url.strip().rstrip("/")

    try:
        metadata, files = await github.fetch_repo(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub fetch failed: {e}")

    try:
        store = VectorStore()
        chunk_count = store.add_documents(files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

    _stores[repo_url] = store
    _metadata[repo_url] = metadata

    return {
        "status": "success",
        "repo": metadata["full_name"],
        "files_indexed": len(files),
        "chunks_created": chunk_count,
        "language": metadata.get("language", ""),
        "stars": metadata.get("stars", 0),
        "description": metadata.get("description", ""),
    }


def _require_store(repo_url: str) -> tuple[VectorStore, dict]:
    store = _stores.get(repo_url)
    if not store:
        raise HTTPException(
            status_code=404,
            detail="Repository not indexed. Please ingest it first.",
        )
    return store, _metadata.get(repo_url, {})


@app.post("/qa")
async def answer_question(request: QARequest):
    """Answer a question about the repository using RAG + Claude."""
    store, meta = _require_store(request.repo_url)

    chunks = store.search(request.question, k=8)
    context = "\n\n---\n\n".join(chunks)
    repo_name = meta.get("full_name", request.repo_url)

    answer = await claude.complete(
        system=QA_SYSTEM.format(repo_name=repo_name),
        user=QA_USER.format(repo_name=repo_name, context=context, question=request.question),
        max_tokens=2048,
    )
    return {"answer": answer}


@app.post("/readme")
async def generate_readme(request: GenerateRequest):
    """Generate a README for the repository."""
    store, meta = _require_store(request.repo_url)

    # Pull context from multiple angles for a well-rounded README
    seen: set[str] = set()
    chunks: list[str] = []
    for query in ["entry point main overview", "installation setup dependencies", "usage examples features"]:
        for chunk in store.search(query, k=5):
            if chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)

    repo_name = meta.get("full_name", request.repo_url)
    readme = await claude.complete(
        system=README_SYSTEM,
        user=README_USER.format(
            repo_name=repo_name,
            description=meta.get("description", ""),
            language=meta.get("language", ""),
            topics=", ".join(meta.get("topics", [])) or "N/A",
            context="\n\n---\n\n".join(chunks[:12]),
        ),
        max_tokens=4096,
    )
    return {"readme": readme}


@app.post("/tests")
async def generate_tests(request: GenerateRequest):
    """Generate unit tests for the repository."""
    store, meta = _require_store(request.repo_url)

    query = request.target_file or "main functions classes methods core logic"
    chunks = store.search(query, k=10)
    repo_name = meta.get("full_name", request.repo_url)

    tests = await claude.complete(
        system=TEST_SYSTEM,
        user=TEST_USER.format(
            repo_name=repo_name,
            language=meta.get("language", "Python"),
            target=request.target_file or "the main source files",
            context="\n\n---\n\n".join(chunks),
        ),
        max_tokens=4096,
    )
    return {"tests": tests}


@app.post("/architecture")
async def generate_architecture(request: GenerateRequest):
    """Generate an architecture summary for the repository."""
    store, meta = _require_store(request.repo_url)

    seen: set[str] = set()
    chunks: list[str] = []
    for query in ["components services modules architecture", "database models schema", "API routes endpoints handlers"]:
        for chunk in store.search(query, k=5):
            if chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)

    repo_name = meta.get("full_name", request.repo_url)
    summary = await claude.complete(
        system=ARCHITECTURE_SYSTEM,
        user=ARCHITECTURE_USER.format(
            repo_name=repo_name,
            description=meta.get("description", ""),
            language=meta.get("language", ""),
            file_tree=meta.get("file_tree", "")[:3000],
            context="\n\n---\n\n".join(chunks[:15]),
        ),
        max_tokens=4096,
    )
    return {"architecture": summary}
