from __future__ import annotations

from typing import Any, Protocol, TypeVar, Type

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelProvider(Protocol):
    name: str

    def chat(self, prompt: str, **kwargs: Any) -> str:
        ...

    def structured_chat(self, prompt: str, response_model: Type[T], **kwargs: Any) -> T:
        ...


class ProviderError(RuntimeError):
    """Raised when a model provider fails to answer or parse the response."""

    pass
