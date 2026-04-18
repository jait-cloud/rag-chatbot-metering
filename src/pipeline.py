"""
End-to-end RAG pipeline.

    query ──► cache lookup ──► retrieval ──► LLM generation ──► cache write ──► response

Measures latency at each stage so the Streamlit UI (and future Prometheus
scraping) can surface exactly where time is spent. This is how you find the
bottleneck in production — is it the embedding call, Chroma, or the LLM?
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from loguru import logger

from .cache import ResponseCache
from .config import settings
from .generation import GenerationResult, generate_answer
from .retrieval import retrieve


@dataclass
class PipelineResponse:
    question: str
    answer: str
    sources: list[dict]
    cached: bool = False
    timings_ms: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


class RAGPipeline:
    def __init__(self, cache: ResponseCache | None = None):
        self.cache = cache or ResponseCache()

    # ------------------------------------------------------------------
    def answer(self, question: str) -> PipelineResponse:
        question = question.strip()
        if not question:
            return PipelineResponse(question="", answer="Please ask a question.", sources=[])

        timings: dict[str, float] = {}
        cache_key = self.cache.build_key(
            question,
            extra={"model": settings.llm_model, "top_k": settings.top_k},
        )

        # --- cache lookup ----------------------------------------------------
        t0 = time.perf_counter()
        cached = self.cache.get(cache_key)
        timings["cache_lookup"] = (time.perf_counter() - t0) * 1000
        if cached:
            logger.info(f"Cache HIT for key {cache_key[:16]}…")
            return PipelineResponse(
                question=question,
                answer=cached["answer"],
                sources=cached.get("sources", []),
                cached=True,
                timings_ms=timings,
                usage=cached.get("usage", {}),
            )

        # --- retrieval -------------------------------------------------------
        t0 = time.perf_counter()
        chunks = retrieve(question)
        timings["retrieval"] = (time.perf_counter() - t0) * 1000

        # --- generation ------------------------------------------------------
        t0 = time.perf_counter()
        gen: GenerationResult = generate_answer(question, chunks)
        timings["generation"] = (time.perf_counter() - t0) * 1000

        payload = PipelineResponse(
            question=question,
            answer=gen.answer,
            sources=gen.sources,
            cached=False,
            timings_ms=timings,
            usage={
                "input_tokens": gen.input_tokens,
                "output_tokens": gen.output_tokens,
                "model": gen.model,
            },
        )

        # --- cache write -----------------------------------------------------
        try:
            self.cache.set(cache_key, asdict(payload))
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

        logger.info(
            "answered q=%r | retrieval=%.0fms gen=%.0fms total=%.0fms | tokens in/out=%d/%d",
            question[:60],
            timings["retrieval"],
            timings["generation"],
            sum(timings.values()),
            gen.input_tokens,
            gen.output_tokens,
        )
        return payload
