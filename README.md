# ⚡ RAG Chatbot — Smart-Meter Technical Support

> Production-oriented Retrieval-Augmented Generation chatbot for a smart electricity-meter
> manufacturer. Answers customer, technician and internal-staff questions from a structured
> knowledge base (product sheets, FAQ, installation guides, troubleshooting).

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM-Claude%20Sonnet-8b5cf6" />
  <img src="https://img.shields.io/badge/vector%20db-ChromaDB-26a69a" />
  <img src="https://img.shields.io/badge/embeddings-multilingual%20MiniLM-f59e0b" />
  <img src="https://img.shields.io/badge/cache-Redis-dc382d?logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/UI-Streamlit-ff4b4b?logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/deploy-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

## 📌 About this project

This repository is a **portfolio-ready reconstruction** of a production RAG chatbot I built
during my internship at an industrial client. The original deployment served real technicians
and customers; the real knowledge base and product data are confidential and **cannot be
published**. What you see here is:

- **The exact same architecture** (ingestion → retrieval → generation → cache → UI)
- **The exact same tech stack** (ChromaDB, SentenceTransformers, Claude API, Redis, Streamlit, Cloud Run)
- **Synthetic but realistic data** for a fictional smart-meter company (`MetriSmart`)

The goal is to let anyone run the system end-to-end locally or deploy it to Cloud Run,
without depending on any proprietary asset.

> **Note for recruiters:** the data is fake, the code and architecture are production-grade.
> Happy to walk through the real business constraints (scale, latency SLO, cost target,
> multilingual support, GDPR) in an interview.

---

## 🏗️ Architecture

```
                    ┌────────────────────────────────────────────┐
                    │              Streamlit UI                  │
                    │  (chat · source citations · debug panel)   │
                    └─────────────────────┬──────────────────────┘
                                          │
                                          ▼
                    ┌────────────────────────────────────────────┐
                    │              RAG Pipeline                  │
                    │  (orchestration · latency/cost metrics)    │
                    └─┬──────────────┬───────────────┬───────────┘
                      │              │               │
                      ▼              ▼               ▼
              ┌──────────────┐ ┌──────────┐ ┌────────────────┐
              │ Redis cache  │ │ Retrieval│ │   Generation   │
              │ (graceful    │ │ ChromaDB │ │  Claude Sonnet │
              │  fallback)   │ │  + MiniLM│ │  (grounded)    │
              └──────────────┘ └─────┬────┘ └────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │  Knowledge base (MD/JSON) │
                        │  ingested + chunked +    │
                        │  embedded once at build  │
                        └────────────────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design decisions and trade-offs.

---

## ✨ Key features

| Feature | What it does | Where to look |
|---|---|---|
| **Grounded generation** | Every answer must cite KB sections; refuses to answer if context is insufficient | `src/generation.py` |
| **Multilingual** | FR / EN / partial AR via `paraphrase-multilingual-MiniLM-L12-v2` | `src/config.py` |
| **Source-aware chunking** | MD split on `##` headings, JSON catalogs split per product | `src/ingestion.py` |
| **Score thresholding** | Low-similarity chunks are dropped to avoid prompt pollution | `src/retrieval.py` |
| **Redis cache w/ fallback** | In-memory LRU kicks in automatically if Redis is unreachable | `src/cache.py` |
| **Per-stage latency** | Each request reports timings for cache / retrieval / generation | `src/pipeline.py` |
| **Token & cost tracking** | Input/output tokens exposed in the debug panel | `src/pipeline.py` |
| **One-command deploy** | `docker compose up` locally, or push to Cloud Run with `deployment/` | `Dockerfile` |

---

## 🚀 Quick start

### 1. Clone & install

```bash
git clone https://github.com/<your-user>/rag-chatbot-metering.git
cd rag-chatbot-metering
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

### 3. Build the vector index

```bash
python -m scripts.build_index
```

This embeds the synthetic KB (≈50 chunks) into ChromaDB. Takes ~30s on CPU.

### 4. Run the UI

```bash
streamlit run app/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) and try one of the example questions in
the sidebar.

### 5. Optional — with Redis cache

```bash
docker compose up
```

This spins up Redis + the app. The cache kicks in automatically on repeated queries —
you'll see `cached: true` and sub-50 ms response times in the debug panel.

---

## 🧪 Running tests

```bash
pytest tests/ -v
```

Tests cover the ingestion, chunking, and cache-fallback paths. They do **not** hit the
LLM API (mocked) so they're free to run in CI.

---

## 📊 Example queries

The sidebar in the Streamlit UI ships with pre-filled examples, but here are a few to try:

- *"Mon compteur affiche ERR-05, que faire ?"* → expect a grounded answer from `troubleshooting.md`
- *"Quel couple de serrage pour les bornes du MS-MONO-100 ?"* → from `installation.md`
- *"How do I reload a prepaid meter?"* → answered in English from `faq.md`
- *"Combien de compteurs par concentrateur ?"* → from `products.json`
- *"Qui est président de la République ?"* → correctly refused as off-topic

---

## 📁 Project layout

```
rag-chatbot-metering/
├── src/
│   ├── config.py          # Pydantic settings
│   ├── ingestion.py       # Loaders + chunker
│   ├── retrieval.py       # ChromaDB + embeddings
│   ├── generation.py      # Claude API + prompt template
│   ├── cache.py           # Redis w/ in-memory fallback
│   └── pipeline.py        # End-to-end orchestration
├── app/
│   └── streamlit_app.py   # Chat UI
├── scripts/
│   └── build_index.py     # Build the vector index
├── data/synthetic/        # Fake KB (products, FAQ, installation, troubleshooting)
├── tests/                 # Pytest suite
├── deployment/
│   └── cloudrun.yaml      # Cloud Run service manifest
├── docs/
│   └── ARCHITECTURE.md    # Design decisions
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## ☁️ Deploying to Google Cloud Run

```bash
# 1. Build & push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/rag-metering

# 2. Deploy with Memorystore Redis attached
gcloud run deploy rag-metering \
  --image gcr.io/$PROJECT_ID/rag-metering \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "REDIS_URL=redis://<memorystore-ip>:6379/0" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-key:latest" \
  --vpc-connector rag-vpc-connector \
  --allow-unauthenticated
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#deployment) for the full Cloud Run
rationale (cold-start handling, index warm-up, VPC egress for Memorystore).

---

## 🛠️ Tech stack

| Layer | Tool | Why |
|---|---|---|
| LLM | Anthropic Claude Sonnet | Best price/quality ratio for grounded generation, robust at following "don't invent" instructions |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` | 50+ languages, tiny (120 MB), runs on CPU in <50 ms/query |
| Vector DB | ChromaDB | Zero-ops, persistent, good enough up to ~1M chunks |
| Cache | Redis (Memorystore) | Sub-ms lookup, TTL-based invalidation |
| UI | Streamlit | Fastest way to ship a chat UI with sources + debug |
| Runtime | Cloud Run | Serverless, scales to zero, pay-per-request |

---

## 🇫🇷 Version française (courte)

Chatbot de support technique pour un fabricant de compteurs électriques intelligents, basé
sur une architecture RAG (Retrieval-Augmented Generation). Ce dépôt est une **reconstruction
portfolio** d'un projet réalisé en stage industriel : l'architecture et la stack sont
identiques à la production, seules les données ont été reconstruites de façon synthétique
pour pouvoir être publiées.

**Points techniques clés :**
- Pipeline RAG complet (ingestion, chunking, embedding multilingue, recherche vectorielle, génération ancrée)
- Cache Redis avec fallback gracieux en mémoire (pas de crash si Redis indisponible)
- Mesure fine de latence par étape + suivi des tokens consommés
- UI Streamlit pensée utilisateur non-tech, avec citation des sources
- Déploiement Cloud Run + Memorystore en une commande

Lancement en local :

```bash
pip install -r requirements.txt
cp .env.example .env  # renseigner ANTHROPIC_API_KEY
python -m scripts.build_index
streamlit run app/streamlit_app.py
```

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).

All data in `data/synthetic/` is fictional and free to reuse.

---

## 🙋 About

Built by **Yassin Jait**, engineering student at ENSISA Mulhouse (Informatique et Réseaux),
alternant Data / ML at Michelin. Open to alternance opportunities starting September 2026 —
feel free to reach out.
