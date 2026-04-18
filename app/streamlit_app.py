"""
Streamlit UI — conversational front-end for the RAG chatbot.

Design goals (from the original internship deployment):
  * Non-technical users must be able to use it with zero onboarding.
  * Every answer must show its sources so operators can verify.
  * Latency, cost and cache status are exposed in the sidebar for ops.
"""
import streamlit as st
from loguru import logger

from src.config import settings
from src.pipeline import RAGPipeline
from src.retrieval import collection_stats


st.set_page_config(
    page_title="MetriSmart Support",
    page_icon="⚡",
    layout="wide",
)


@st.cache_resource
def get_pipeline() -> RAGPipeline:
    return RAGPipeline()


# --- Header -----------------------------------------------------------------
st.title("⚡ MetriSmart — Assistant Support")
st.caption(
    "RAG-powered support chatbot for smart electricity meters. "
    "Running on synthetic data — see README for details."
)

# --- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    stats = collection_stats()
    st.metric("Documents indexés", stats["count"])
    st.caption(f"Modèle LLM : `{settings.llm_model}`")
    st.caption(f"Embedding : `{settings.embedding_model.split('/')[-1]}`")
    st.caption(f"Top-K : {settings.top_k} | seuil : {settings.min_score}")
    st.caption(f"Cache : {'✅ activé' if settings.enable_cache else '❌ désactivé'}")

    st.divider()
    st.header("💡 Exemples de questions")
    samples = [
        "Mon compteur affiche ERR-05, que faire ?",
        "Comment recharger un compteur prépayé ?",
        "Quel couple de serrage pour les bornes du MS-MONO-100 ?",
        "Combien de compteurs un concentrateur peut-il gérer ?",
        "How do I read my consumption on the display?",
    ]
    for s in samples:
        if st.button(s, use_container_width=True):
            st.session_state["_pending_question"] = s

    st.divider()
    if st.button("🗑️  Réinitialiser la conversation"):
        st.session_state["messages"] = []
        st.rerun()

# --- Chat state -------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Sources"):
                for s in msg["sources"]:
                    st.caption(
                        f"**{s.get('section', '?')}** — `{s.get('source', '?')}` "
                        f"(score {s.get('score', 0):.2f})"
                    )
        if msg.get("debug"):
            with st.expander("🔎 Debug (latence & coût)"):
                st.json(msg["debug"])

# --- Input ------------------------------------------------------------------
pending = st.session_state.pop("_pending_question", None)
user_input = pending or st.chat_input("Posez votre question…")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans la base de connaissances…"):
            try:
                response = get_pipeline().answer(user_input)
            except Exception as e:
                logger.exception("Pipeline failure")
                st.error(f"Erreur : {e}")
                st.stop()

        st.markdown(response.answer)

        if response.sources:
            with st.expander("📚 Sources"):
                for s in response.sources:
                    st.caption(
                        f"**{s.get('section', '?')}** — `{s.get('source', '?')}` "
                        f"(score {s.get('score', 0):.2f})"
                    )

        debug = {
            "cached": response.cached,
            "timings_ms": {k: round(v, 1) for k, v in response.timings_ms.items()},
            "usage": response.usage,
        }
        with st.expander("🔎 Debug (latence & coût)"):
            st.json(debug)

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": response.answer,
                "sources": response.sources,
                "debug": debug,
            }
        )
