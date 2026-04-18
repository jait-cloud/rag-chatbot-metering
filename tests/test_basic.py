"""
Tests for the ingestion, chunking and cache-fallback logic.

We deliberately don't test retrieval.py or generation.py here because they
depend on external services (ChromaDB with persisted state, Anthropic API).
Those belong in integration tests run against a real-ish environment.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.ingestion import Document, _load_markdown, chunk_documents, load_documents
from src.cache import _MemoryLRU, ResponseCache


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------
def test_markdown_splits_on_h2(tmp_path: Path):
    md = tmp_path / "sample.md"
    md.write_text(
        "# Title\n\n## Section A\nBody A.\n\n## Section B\nBody B.\n",
        encoding="utf-8",
    )
    docs = _load_markdown(md)
    # Preamble (H1 title) + 2 H2 sections = 3 documents.
    # Preserving the preamble matters for real KBs that often carry context there.
    assert len(docs) == 3
    sections = {d.metadata["section"] for d in docs}
    assert {"Section A", "Section B"}.issubset(sections)
    assert all(d.metadata["source"] == "sample.md" for d in docs)


def test_load_documents_mixes_md_and_json(tmp_path: Path):
    (tmp_path / "faq.md").write_text("## Q1\nA1.", encoding="utf-8")
    (tmp_path / "products.json").write_text(
        json.dumps(
            {
                "products": [
                    {
                        "ref": "X-1",
                        "name": "X-One",
                        "category": "cat",
                        "description": "desc",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")

    docs = load_documents(tmp_path)
    assert len(docs) == 2
    types = {d.metadata["type"] for d in docs}
    assert types == {"markdown", "product_sheet"}


def test_chunker_preserves_short_docs():
    doc = Document(content="Short content.", metadata={"source": "x"})
    chunks = chunk_documents([doc], chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0].content == "Short content."


def test_chunker_splits_long_doc_with_overlap():
    long_text = " ".join([f"Sentence {i}." for i in range(100)])
    doc = Document(content=long_text, metadata={"source": "x"})
    chunks = chunk_documents([doc], chunk_size=120, chunk_overlap=30)
    assert len(chunks) > 1
    # all chunks carry the source metadata
    assert all(c.metadata["source"] == "x" for c in chunks)
    # chunks stay under size + some slack
    assert all(len(c.content) <= 200 for c in chunks)


def test_doc_id_is_deterministic():
    a = Document(content="hello world", metadata={"source": "a.md"})
    b = Document(content="hello world", metadata={"source": "a.md"})
    assert a.doc_id == b.doc_id


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
def test_memory_lru_basic():
    lru = _MemoryLRU(capacity=3)
    lru.setex("a", 60, 1)
    lru.setex("b", 60, 2)
    lru.setex("c", 60, 3)
    assert lru.get("a") == 1
    lru.setex("d", 60, 4)  # evicts "b" (least recently used)
    assert lru.get("b") is None
    assert lru.get("d") == 4


def test_memory_lru_respects_ttl():
    lru = _MemoryLRU()
    lru.setex("k", 1, "v")
    assert lru.get("k") == "v"
    time.sleep(1.1)
    assert lru.get("k") is None


def test_cache_key_is_deterministic_and_case_insensitive(monkeypatch):
    monkeypatch.setenv("ENABLE_CACHE", "false")
    # Reload settings after env change
    from importlib import reload
    from src import config as config_module

    reload(config_module)
    cache = ResponseCache()
    k1 = cache.build_key("How Do I Reset?", extra={"model": "claude", "top_k": 4})
    k2 = cache.build_key("how do i reset?", extra={"top_k": 4, "model": "claude"})
    assert k1 == k2
    assert k1.startswith("rag:")


def test_cache_falls_back_gracefully_without_redis(monkeypatch):
    """If Redis is unreachable, ResponseCache should silently use memory LRU."""
    # Point to a port where nothing is listening
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    monkeypatch.setenv("ENABLE_CACHE", "true")
    from importlib import reload
    from src import config as config_module, cache as cache_module

    reload(config_module)
    reload(cache_module)

    cache = cache_module.ResponseCache()
    key = cache.build_key("test query")
    cache.set(key, {"answer": "hello", "sources": []})
    assert cache.get(key) == {"answer": "hello", "sources": []}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
