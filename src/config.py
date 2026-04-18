"""
Central configuration using pydantic-settings.

All values can be overridden via environment variables or a .env file.
This pattern mirrors what you'd ship to production (Cloud Run / K8s),
where secrets are injected as env vars rather than hardcoded.
"""
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    anthropic_api_key: str = Field(default="", description="Claude API key")
    llm_model: str = Field(default="claude-sonnet-4-5", description="Claude model name")
    llm_max_tokens: int = Field(default=800)
    llm_temperature: float = Field(default=0.2)

    # --- Embeddings ---
    # Multilingual model to support FR + EN (and decent AR coverage),
    # matching a real-world deployment for a North African client.
    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_device: Literal["cpu", "cuda"] = Field(default="cpu")

    # --- Vector store ---
    chroma_persist_dir: Path = Field(default=ROOT_DIR / "data" / "chroma")
    collection_name: str = Field(default="metering_kb")

    # --- Chunking ---
    chunk_size: int = Field(default=700, description="Approximate chars per chunk")
    chunk_overlap: int = Field(default=120)

    # --- Retrieval ---
    top_k: int = Field(default=4)
    min_score: float = Field(default=0.25, description="Min cosine similarity to keep a chunk")

    # --- Cache (Redis) ---
    redis_url: str = Field(default="redis://localhost:6379/0")
    cache_ttl_seconds: int = Field(default=3600)
    enable_cache: bool = Field(default=True)

    # --- App ---
    log_level: str = Field(default="INFO")
    data_dir: Path = Field(default=ROOT_DIR / "data" / "synthetic")


settings = Settings()
