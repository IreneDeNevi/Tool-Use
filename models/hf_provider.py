from __future__ import annotations

import json
from typing import Any, Type, TypeVar

from huggingface_hub import InferenceClient
from pydantic import BaseModel

from app.config import settings
from models.providers import ModelProvider, ProviderError

T = TypeVar("T", bound=BaseModel)


class HFProvider:
    """Wrapper around Hugging Face Inference API."""

    name = "hf"

    def __init__(self, model_name: str | None = None, token: str | None = None):
        self.model_name = model_name or settings.llm_model_name
        self.token = token or settings.huggingface_hub_token
        if not self.token:
            raise ProviderError("HUGGINGFACE_HUB_TOKEN is not set.")
        self.client = InferenceClient(model=self.model_name, token=self.token)

    def chat(self, prompt: str, **kwargs: Any) -> str:
        response = self.client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 768),
            temperature=kwargs.get("temperature", 0.2),
        )
        return response.choices[0].message.content

    def structured_chat(self, prompt: str, response_model: Type[T], **kwargs: Any) -> T:
        raw = self.chat(prompt, **kwargs)
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw_json = raw[start : end + 1]
        else:
            raw_json = raw

        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Model did not return valid JSON: {raw[:300]}") from exc

        return response_model.model_validate(payload)


__all__ = ["HFProvider"]
