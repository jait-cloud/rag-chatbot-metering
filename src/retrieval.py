"""
Vector store wrapper around ChromaDB + sentence-transformers.

Kept intentionally thin — Chroma already does the heavy lifting. The value
this module adds is:
  * a single place to swap the embedding backend or vector DB later
  * score thresholding (Chroma returns distances, we convert to similarity)
  * metadata-aware formatting for downstream prompt building
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from sentence_transformers import SentenceTransformer

from .config import settings
from .ingestion import Document


@dataclass
class RetrievedChunk:
    content: str
    metadata: dict
    score: float  # cosine similarity in [0, 1], higher is better


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Lazy-loaded embedding model, cached so Streamlit reruns stay cheap."""
    logger.info(f"Loading embedding model: {settings.embedding_model}")
    return SentenceTransformer(settings.embedding_model, device=settings.embedding_device)


@lru_cache(maxsize=1)
def get_client() -> chromadb.api.ClientAPI:
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(settings.chroma_persist_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_or_create_collection():
    client = get_client()
    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def index_documents(docs: Sequence[Document]) -> int:
    """Embed and insert documents. Returns the number of chunks added."""
    if not docs:
        return 0
    embedder = get_embedder()
    collection = _get_or_create_collection()

    texts = [d.content for d in docs]
    ids = [d.doc_id for d in docs]
    metadatas = [d.metadata for d in docs]
    logger.info(f"Embedding {len(texts)} chunks…")
    embeddings = embedder.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    # upsert is idempotent — safe to re-run the ingestion script
    collection.upsert(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )
    logger.success(f"Indexed {len(texts)} chunks into '{settings.collection_name}'")
    return len(texts)


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Return the top_k most relevant chunks for a query, filtered by min_score."""
    top_k = top_k or settings.top_k
    embedder = get_embedder()
    collection = _get_or_create_collection()

    query_emb = embedder.encode([query], normalize_embeddings=True)
    result = collection.query(
        query_embeddings=query_emb.tolist(),
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    # Chroma returns cosine *distance* = 1 - similarity (since we set hnsw:space=cosine)
    dists = result["distances"][0]
    chunks = [
        RetrievedChunk(content=d, metadata=m, score=max(0.0, 1.0 - dist))
        for d, m, dist in zip(docs, metas, dists)
    ]
    filtered = [c for c in chunks if c.score >= settings.min_score]
    logger.debug(
        f"Retrieved {len(chunks)} chunks, kept {len(filtered)} after score>={settings.min_score}"
    )
    return filtered


def collection_stats() -> dict:
    collection = _get_or_create_collection()
    return {
        "name": settings.collection_name,
        "count": collection.count(),
        "embedding_model": settings.embedding_model,
    }
