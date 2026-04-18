"""
Document ingestion: load files from disk, normalise them into a list of
Document objects with metadata, then split into overlapping chunks.

Design notes
------------
- We keep chunking deliberately simple (recursive character split) because
  the knowledge base is structured prose (FAQs, guides, product sheets).
  For heavy PDFs you'd swap in a layout-aware parser (unstructured / docling).
- Each chunk carries the source file, section heading and a stable chunk_id.
  These metadata fields are what lets us cite sources back to the user,
  which is a critical UX feature in industrial support chatbots.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from loguru import logger


@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)

    @property
    def doc_id(self) -> str:
        h = hashlib.sha1(self.content.encode("utf-8")).hexdigest()[:12]
        src = self.metadata.get("source", "unknown")
        return f"{Path(src).stem}__{h}"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def _load_markdown(path: Path) -> list[Document]:
    """Split a markdown file by H2 headings so each section becomes a Document."""
    text = path.read_text(encoding="utf-8")
    # Split on ## headings while keeping the heading attached to its body.
    sections = re.split(r"(?m)^(?=##\s)", text)
    docs: list[Document] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"##\s+(.+)", section)
        heading = heading_match.group(1).strip() if heading_match else path.stem
        docs.append(
            Document(
                content=section,
                metadata={"source": path.name, "section": heading, "type": "markdown"},
            )
        )
    return docs


def _load_json_catalog(path: Path) -> list[Document]:
    """Turn each product in a catalog JSON into its own Document."""
    data = json.loads(path.read_text(encoding="utf-8"))
    docs: list[Document] = []
    for product in data.get("products", []):
        lines = [f"Product: {product['name']} (ref. {product['ref']})"]
        lines.append(f"Category: {product['category']}")
        lines.append(f"Description: {product['description']}")
        specs = product.get("specs", {})
        if specs:
            lines.append("Specifications:")
            for k, v in specs.items():
                lines.append(f"  - {k}: {v}")
        if features := product.get("features"):
            lines.append("Key features: " + "; ".join(features))
        docs.append(
            Document(
                content="\n".join(lines),
                metadata={
                    "source": path.name,
                    "section": product["name"],
                    "product_ref": product["ref"],
                    "type": "product_sheet",
                },
            )
        )
    return docs


def load_documents(data_dir: Path) -> list[Document]:
    """Load every supported file from the knowledge-base directory."""
    docs: list[Document] = []
    for path in sorted(data_dir.iterdir()):
        if path.suffix == ".md":
            docs.extend(_load_markdown(path))
        elif path.suffix == ".json":
            docs.extend(_load_json_catalog(path))
        else:
            logger.debug(f"Skipping unsupported file: {path.name}")
    logger.info(f"Loaded {len(docs)} raw documents from {data_dir}")
    return docs


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------
def chunk_documents(
    docs: Iterable[Document],
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> list[Document]:
    """
    Split each Document into overlapping chunks, preserving metadata.

    We prefer sentence boundaries when possible so embeddings stay semantically
    coherent. If a doc is already smaller than chunk_size, we keep it intact.
    """
    chunks: list[Document] = []
    for doc in docs:
        if len(doc.content) <= chunk_size:
            chunks.append(doc)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", doc.content)
        buffer = ""
        for sent in sentences:
            if len(buffer) + len(sent) + 1 <= chunk_size:
                buffer = f"{buffer} {sent}".strip()
            else:
                if buffer:
                    chunks.append(Document(content=buffer, metadata=dict(doc.metadata)))
                # start new buffer with overlap
                tail = buffer[-chunk_overlap:] if chunk_overlap else ""
                buffer = f"{tail} {sent}".strip()
        if buffer:
            chunks.append(Document(content=buffer, metadata=dict(doc.metadata)))

    logger.info(f"Produced {len(chunks)} chunks from {len(list(docs))} docs")
    return chunks
