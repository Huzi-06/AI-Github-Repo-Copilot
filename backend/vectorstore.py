from __future__ import annotations

from typing import List

import numpy as np
import faiss

# Lazy-loaded to avoid startup delay (first use downloads ~80MB model)
_model = None

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _model


def _normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize rows so inner product == cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    return vectors / norms


def chunk_text(text: str, path: str) -> List[str]:
    """Split file content into overlapping chunks prefixed with the file path."""
    header = f"# File: {path}\n\n"
    max_content = CHUNK_SIZE - len(header)

    if not text.strip():
        return []

    if len(text) <= max_content:
        return [header + text]

    chunks = []
    start = 0
    while start < len(text):
        chunk_content = text[start : start + max_content]
        chunks.append(header + chunk_content)
        start += max_content - CHUNK_OVERLAP

    return chunks


class VectorStore:
    def __init__(self):
        self.index: faiss.IndexFlatIP | None = None
        self.chunks: List[str] = []

    def add_documents(self, files: List[dict]) -> int:
        """Embed and index all file chunks. Returns the number of chunks created."""
        model = get_model()

        all_chunks: List[str] = []
        for file in files:
            content = file.get("content", "")
            if not content:
                continue
            all_chunks.extend(chunk_text(content, file["path"]))

        if not all_chunks:
            return 0

        self.chunks = all_chunks

        embeddings = list(model.embed(all_chunks, batch_size=64))
        embeddings = np.array(embeddings, dtype="float32")
        embeddings = _normalize(embeddings)  # cosine similarity via inner product

        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.index.add(embeddings)

        return len(all_chunks)

    def search(self, query: str, k: int = 6) -> List[str]:
        """Return top-k most relevant chunks for a query."""
        if self.index is None or not self.chunks:
            return []

        model = get_model()
        query_embedding = list(model.embed([query]))
        query_embedding = np.array(query_embedding, dtype="float32")
        query_embedding = _normalize(query_embedding)

        k = min(k, len(self.chunks))
        _, indices = self.index.search(query_embedding, k)

        return [self.chunks[i] for i in indices[0] if i >= 0]