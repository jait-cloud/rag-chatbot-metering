"""RAG chatbot package for smart-meter technical support."""
# Keep imports lazy so that lightweight tooling (ingestion, tests) doesn't
# have to pull in anthropic/chromadb/sentence-transformers.
__all__ = ["RAGPipeline", "PipelineResponse"]
__version__ = "0.1.0"


def __getattr__(name):  # PEP 562 — lazy attribute access
    if name in ("RAGPipeline", "PipelineResponse"):
        from .pipeline import RAGPipeline, PipelineResponse

        return {"RAGPipeline": RAGPipeline, "PipelineResponse": PipelineResponse}[name]
    raise AttributeError(f"module 'src' has no attribute {name!r}")
