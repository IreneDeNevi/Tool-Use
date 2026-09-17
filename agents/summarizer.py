from __future__ import annotations

import json
import time

from models.providers import ModelProvider
from tools.memory import VectorMemory


class SummarizerAgent:
    """Creates a grounded Markdown report for the retrieved sources."""

    def __init__(self, provider: ModelProvider, memory: VectorMemory):
        self.provider = provider
        self.memory = memory

    def _build_context(self, documents: list[dict], user_query: str) -> str:
        query_text = user_query or "research summary"
        matches = self.memory.query(query_text, top_k=8, where={"type": "web_page"})

        text_bits = []
        for document in documents:
            text = document.get("text") or ""
            if text:
                text_bits.append(text[:1800])

        for match in matches:
            text = match.get("text") or ""
            if text:
                text_bits.append(text[:1800])

        return "\n\n---\n\n".join(text_bits)[:12000]

    def summarize(self, documents: list[dict], user_query: str) -> str:
        context = self._build_context(documents, user_query)

        prompt = f"""
Sei un assistente di ricerca affidabile.

Contesto recuperato:
---
{context}
---

Documenti ottenuti:
{json.dumps(documents, ensure_ascii=False, indent=2)[:8000]}

Richiesta:
- rispondi in Markdown ben strutturato
- usa sezioni chiare
- aggiungi citazioni in formato [URL]
- non inventare fonti
- se un fatto non è supportato, non includerlo

Domanda dell'utente: {user_query}
"""

        md = self.provider.chat(prompt, temperature=0.2, max_tokens=1200)
        self.memory.upsert(
            texts=[md],
            metadatas=[{"type": "summary_report", "timestamp": int(time.time())}],
        )
        return md
