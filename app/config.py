from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass
class Settings:
    """Runtime settings for the research pipeline."""

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    searxng_base_url: str = field(default_factory=lambda: os.getenv("SEARXNG_BASE_URL", "http://localhost:8080"))
    searxng_secret: str | None = field(default_factory=lambda: os.getenv("SEARXNG_SECRET") or None)
    searxng_language: str | None = field(default_factory=lambda: os.getenv("SEARXNG_LANGUAGE") or None)
    searxng_engines: list[str] = field(default_factory=lambda: [e.strip() for e in (os.getenv("SEARXNG_ENGINES") or "").split(",") if e.strip()])
    huggingface_hub_token: str | None = field(default_factory=lambda: os.getenv("HUGGINGFACE_HUB_TOKEN") or None)
    llm_model_name: str = field(default_factory=lambda: os.getenv("LLM_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.3"))
    chroma_host: str | None = field(default_factory=lambda: os.getenv("CHROMA_HOST") or None)
    chroma_port: int = field(default_factory=lambda: int(os.getenv("CHROMA_PORT", "8000")))
    chroma_ssl: bool = field(default_factory=lambda: (os.getenv("CHROMA_SSL", "false").lower() in {"1", "true", "yes"}))
    chroma_persist_path: str = field(default_factory=lambda: os.getenv("CHROMA_PERSIST_PATH", "./memory_store"))
    chroma_collection: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "research-cache"))
    chroma_embedding_model: str = field(default_factory=lambda: os.getenv("CHROMA_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))

    @property
    def is_local_chroma(self) -> bool:
        return not bool(self.chroma_host)


settings = Settings()
