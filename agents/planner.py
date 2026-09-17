from __future__ import annotations

import json
import re
import time

from app.schemas import ResearchPlan
from models.providers import ModelProvider
from tools.memory import VectorMemory


STOP_WORDS = {
    "what", "why", "how", "when", "where", "which", "who", "is", "are", "the", "a", "an",
    "for", "and", "or", "to", "of", "in", "on", "it", "its", "with", "from", "by", "be",
    "does", "do", "did", "use", "used", "using", "about", "into", "this", "that", "these", "those"
}


class PlannerAgent:
    """Generates a structured research plan for a user query."""

    def __init__(self, provider: ModelProvider, memory: VectorMemory):
        self.provider = provider
        self.memory = memory

    @staticmethod
    def normalize_search_term(term: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", term.lower())
        tokens = [token for token in cleaned.split() if token and token not in STOP_WORDS]
        if not tokens:
            return ""

        # SearXNG is more reliable on short, keyword-like queries than on full questions or
        # long noun phrases. Keep the most salient concept, not the entire sentence.
        return tokens[0].strip()

    def plan(self, user_input: str) -> ResearchPlan:
        prompt = f"""
Sei un agente di ricerca web affidabile.

Utente: {user_input}

Genera un piano di ricerca in JSON valido con il seguente schema:
- intent: breve descrizione dell'obiettivo
- core_topics: 3-5 topic chiave
- related_topics: topic collegati
- search_terms: 3-8 query di ricerca efficaci, preferibilmente keyword, non frasi complete
- allowed_domains: domini preferiti (es. python.org, docs, github, arxiv, official docs)
- freshness: uno tra pd, pw, pm, py, custom
- quality_constraints: regole di qualità da rispettare

Rispondi SOLO con JSON valido.
"""

        raw = self.provider.chat(prompt, temperature=0.2, max_tokens=900)
        start = raw.find("{")
        end = raw.rfind("}")
        payload = raw[start : end + 1] if start != -1 and end != -1 and end > start else raw

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {
                "intent": user_input,
                "core_topics": [user_input[:60]],
                "related_topics": [],
                "search_terms": [user_input[:60]],
                "allowed_domains": [],
                "freshness": "pw",
                "quality_constraints": ["source grounding"],
            }

        raw_search_terms = data.get("search_terms") or [user_input]
        normalized_terms = [self.normalize_search_term(term) for term in raw_search_terms if term]
        normalized_terms = list(dict.fromkeys(term for term in normalized_terms if term))[:8]
        if not normalized_terms:
            normalized_terms = [self.normalize_search_term(user_input)]

        plan = ResearchPlan(
            intent=data.get("intent") or user_input,
            core_topics=data.get("core_topics") or [user_input[:60]],
            related_topics=data.get("related_topics") or [],
            search_terms=normalized_terms,
            allowed_domains=data.get("allowed_domains") or ["python.org", "docs", "github.com", "arxiv.org"],
            freshness=data.get("freshness") or "pw",
            quality_constraints=data.get("quality_constraints") or ["source grounding"],
        )

        self.memory.upsert(
            texts=[json.dumps(plan.model_dump(), ensure_ascii=False)],
            metadatas=[{"type": "research_plan", "timestamp": int(time.time()), "user_query": user_input}],
        )

        return plan
