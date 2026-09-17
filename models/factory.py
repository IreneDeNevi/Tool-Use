from __future__ import annotations

from models.hf_provider import HFProvider
from models.providers import ModelProvider


def build_model_provider(provider_name: str = "hf") -> ModelProvider:
    provider_name = (provider_name or "hf").lower()
    if provider_name == "hf":
        return HFProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")


__all__ = ["build_model_provider"]
