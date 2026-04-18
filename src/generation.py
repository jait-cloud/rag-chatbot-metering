"""
LLM generation layer.

Uses the official Anthropic SDK. The prompt template is deliberately strict
about two things that matter for a support chatbot in an industrial context:

  1. Grounding — the model must cite retrieved sources and must not invent
     product references. If the context is insufficient, it must say so.
  2. Language — answer in the user's language (FR / EN / AR if present in KB).

For a customer-facing deployment you'd add:
  - output moderation
  - a guardrail model / PII scrubber on inputs
  - a fallback to a human agent above a configurable uncertainty threshold
"""
from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic
from loguru import logger

from .config import settings
from .retrieval import RetrievedChunk


SYSTEM_PROMPT = """You are a technical support assistant for a smart-meter manufacturer.
Your role is to help three audiences: end-customers (non-technical), field technicians
(installation / troubleshooting), and internal staff (product & commercial questions).

RULES — follow them strictly:
1. Ground every factual claim in the <context> provided. If the context does not contain
   the answer, say clearly that you don't have the information and suggest contacting
   human support. Never invent product references, specifications, or procedures.
2. Reply in the language the user used (French, English, or Arabic).
3. Keep answers concise and actionable. For troubleshooting, use short numbered steps.
4. Always end factual answers with a "Sources" line listing the section names you used,
   in the format: "Sources: <section1>, <section2>".
5. If the question is off-topic (not about smart meters, billing, installation, or
   related services), politely redirect.
"""


USER_TEMPLATE = """<context>
{context}
</context>

<question>
{question}
</question>

Answer the question using only the context above. Respect the rules."""


@dataclass
class GenerationResult:
    answer: str
    sources: list[dict]
    input_tokens: int
    output_tokens: int
    model: str


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no relevant passages retrieved)"
    blocks = []
    for i, c in enumerate(chunks, start=1):
        section = c.metadata.get("section", "unknown")
        source = c.metadata.get("source", "unknown")
        blocks.append(
            f"[{i}] source={source} | section={section} | score={c.score:.2f}\n{c.content}"
        )
    return "\n\n---\n\n".join(blocks)


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    client: Anthropic | None = None,
) -> GenerationResult:
    """Call Claude with the retrieved context and return a structured result."""
    client = client or Anthropic(api_key=settings.anthropic_api_key)
    context = _format_context(chunks)

    logger.debug(f"Generating with {len(chunks)} chunks, model={settings.llm_model}")
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_TEMPLATE.format(context=context, question=question),
            }
        ],
    )

    answer_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    sources = [
        {
            "source": c.metadata.get("source"),
            "section": c.metadata.get("section"),
            "score": round(c.score, 3),
        }
        for c in chunks
    ]

    return GenerationResult(
        answer=answer_text.strip(),
        sources=sources,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        model=response.model,
    )
