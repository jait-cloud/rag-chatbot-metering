# Architecture & Design Decisions

This document captures **why** the system is built the way it is — the kind of trade-offs
I'd walk through in a design review or interview. It's intentionally opinionated: every
choice here was made against an alternative, not out of habit.

## 1. Scope & constraints

The real-world system this repo reconstructs had to serve three audiences from a single
entry point:

- **End customers** (non-technical, ~80 % of traffic) asking billing / consumption /
  "how do I read my meter" questions.
- **Field technicians** (~15 %) asking installation and diagnostic questions from a phone
  on site, sometimes with poor connectivity.
- **Internal staff** (~5 %) asking product / commercial questions for quick sales support.

Design constraints:

| Constraint | Target |
|---|---|
| P95 latency | < 3 s (cold), < 500 ms (cached) |
| Monthly LLM cost | < €X per 10 k queries |
| Languages | French primary, English secondary, Arabic nice-to-have |
| Deployment | Serverless, scale-to-zero (idle periods dominate) |
| Availability | 99.5 % — outage of LLM provider must degrade gracefully |

## 2. Why RAG (not fine-tuning, not pure prompting)

**Ruled out: fine-tuning.** The knowledge base changes monthly (new product firmware,
updated procedures). Fine-tuning would require a retraining pipeline, an eval harness,
and model hosting — overkill for <100 k tokens of relatively static prose.

**Ruled out: pure prompting (stuff the whole KB in the prompt).** The KB is ~150 k tokens
and growing. Prompt-stuffing would be slow, expensive, and hit context limits within a
year. It also gives poor attribution — the model can't cite a specific passage.

**RAG wins** because:
- Knowledge updates = re-run the ingestion script (minutes, no model retraining).
- Retrieval surfaces exactly the ~4 chunks relevant to a query, keeping prompts short.
- Attribution is natural: we know which chunks we sent, so we can cite them.

## 3. Ingestion & chunking

**Decision: chunk on semantic boundaries where possible.**

For Markdown files we split on `##` headings first. Each FAQ entry, troubleshooting code
or installation step becomes its own Document with a meaningful `section` metadata field.
Only *within* an oversized section do we fall back to sentence-level chunking with
overlap.

Why it matters: a search for `"ERR-05"` returns the full troubleshooting section for that
error code as one chunk, not half of it with the other half missing. This directly
improves answer quality because the LLM sees complete procedures, not fragments.

For the product catalog JSON, each product becomes one Document. The LLM then gets all
specs of the relevant product together — no broken "courant max: 100" with the unit on
another chunk.

**Chunk size: 700 chars, 120 overlap.** Smaller than typical (~1000) because our KB is
dense technical prose with sharp semantic boundaries. 700 chars ≈ 1 complete FAQ answer.

## 4. Embedding model

**Decision: `paraphrase-multilingual-MiniLM-L12-v2`.**

Candidates considered:

| Model | Size | Multilingual | Notes |
|---|---|---|---|
| `all-MiniLM-L6-v2` | 80 MB | EN only | Fast but doesn't handle FR queries |
| `paraphrase-multilingual-MiniLM-L12-v2` | 120 MB | 50+ langs | **Chosen** |
| `multilingual-e5-large` | 2.2 GB | 100+ langs | Better quality but 10× slower, overkill |
| OpenAI `text-embedding-3-small` | API | many | Adds external dependency + cost |

The chosen model runs on CPU in ~30 ms/query, fits in any Cloud Run container, and scores
high enough on our internal eval (83 % top-3 recall on a 200-query benchmark from the
real deployment).

## 5. Vector store

**Decision: ChromaDB with persistent local storage.**

- For our KB size (<10 k chunks) a managed vector DB (Pinecone, Weaviate Cloud) would be
  paying for capacity we don't use.
- Chroma is embedded, zero-ops, and handles cosine similarity natively.
- The persist directory is packaged **into the Docker image** at build time. Cloud Run
  cold starts thus don't pay an indexing tax — they're ~2 s instead of ~30 s.

Trade-off: re-indexing requires rebuilding the image. Acceptable given KB update
frequency (monthly). For a faster update cycle we'd move to a sidecar ingestion job
writing to Memorystore or a managed vector DB.

## 6. Generation & grounding

**Decision: strict system prompt with refusal rule.**

The system prompt (in `src/generation.py`) has four non-negotiable rules:

1. Ground every claim in the `<context>` block.
2. Refuse + suggest human escalation if context is insufficient.
3. Reply in the user's language.
4. Always cite section names.

Why this matters: hallucinations in a **support context** are actively dangerous. A
wrong torque value in an installation answer could destroy equipment or injure a
technician. The refusal rule trades off some "helpfulness" for safety, which is the
correct trade-off for this domain.

**Temperature: 0.2.** Not zero (some phrasing variation is natural and more pleasant),
but low enough that the same question gets essentially the same answer every time.

## 7. Caching strategy

**Decision: query-level cache keyed on (question, model, top_k).**

Not a semantic cache (which would match *similar* queries). Semantic caches are
tempting but risky: two queries with similar embeddings can have genuinely different
correct answers (e.g. "ERR-01" vs "ERR-07" embed similarly but mean very different
things). The hit rate would go up but so would the wrong-answer rate.

Query-level caching is boring and safe. In the real deployment, repeated questions
("how do I recharge my meter?") accounted for ~35 % of traffic and we got ~30 % cache
hit rate after a month. Average latency dropped from ~1.8 s to ~1.2 s and LLM spend
dropped by ~30 %.

**The fallback.** When Memorystore has a blip (rare but it happens on GCP), the service
must not crash. `src/cache.py` catches Redis errors and falls back to an in-memory LRU
dict. Users see no impact; we just lose cross-instance cache sharing until Redis
recovers.

## 8. Observability

Each request records:

- Timings per stage (cache lookup / retrieval / generation)
- Token usage (input/output)
- Cache status
- Retrieved chunks + scores

Exposed in the Streamlit debug panel for development. In production, these would be
emitted as structured logs and scraped into Cloud Monitoring dashboards, with alerts on:

- P95 generation latency > 3 s (5 min window)
- Cache hit rate < 15 % (likely cache or KB-version problem)
- Refusal rate > 10 % (likely a new topic is trending and needs KB coverage)

## 9. Deployment

**Decision: Cloud Run + Memorystore Redis, serverless.**

- **Scale to zero.** Traffic is bursty (business hours only). Paying for idle VMs made
  no sense.
- **Image includes pre-built index.** This is the single biggest cold-start optimization.
  Without it, first-request latency would be 30+ s while Chroma builds its index.
- **Memorystore in the same VPC.** Redis must be reachable from Cloud Run, which requires
  a Serverless VPC Connector. Extra ~€10/month but cuts cache latency to <5 ms.
- **Secrets via Secret Manager**, not env vars. The Anthropic API key never touches
  disk or logs.

## 10. What I'd do differently at higher scale

If this system had to handle >100 k queries/day and a 10× bigger KB:

- Move from ChromaDB to a managed vector DB (Vertex Vector Search or Weaviate Cloud).
- Separate the ingestion pipeline into its own service with a proper eval harness
  (retrieval recall @ k, answer groundedness scored by a judge LLM).
- Add a re-ranker (Cohere Rerank or a cross-encoder) between retrieval and generation —
  doubles recall but adds ~100 ms of latency.
- Introduce a guardrail model (small, cheap) on inputs to filter out-of-scope questions
  before the expensive retrieval + generation round-trip.
- Per-audience routing (customer / technician / staff) with different prompts and
  possibly different KB partitions.
