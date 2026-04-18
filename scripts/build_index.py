"""
Build (or rebuild) the vector index from the synthetic knowledge base.

Usage:
    python -m scripts.build_index
"""
from loguru import logger

from src.config import settings
from src.ingestion import chunk_documents, load_documents
from src.retrieval import collection_stats, index_documents


def main() -> None:
    logger.info(f"Loading documents from {settings.data_dir}")
    docs = load_documents(settings.data_dir)
    if not docs:
        logger.error("No documents found — make sure data/synthetic/ is populated.")
        raise SystemExit(1)

    chunks = chunk_documents(
        docs,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    n = index_documents(chunks)
    logger.success(f"Index built — {n} chunks")
    logger.info(f"Collection stats: {collection_stats()}")


if __name__ == "__main__":
    main()
