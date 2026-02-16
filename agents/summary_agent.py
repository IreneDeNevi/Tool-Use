from agents.base_agent import BaseAgent
from tools.memory import VectorMemory
import json, time

class SummaryReportAgent(BaseAgent):
    def __init__(self, llm, memory: VectorMemory):
        super().__init__(llm)
        self.memory = memory

    def _build_context(self, search_results):
        # usa i titoli/snippet come query per recuperare memorie rilevanti
        queries = []
        for r in search_results:
            if r.get("title"):
                queries.append(r["title"])
            elif r.get("snippet"):
                queries.append(r["snippet"])
        # Unisci query per una ricerca globale
        query_text = ". ".join(queries)[:2000] if queries else "web research results"
        matches = self.memory.query(query_text, top_k=10, where={"type": "web_page"})
        ctx = "\n\n".join([m["text"][:1500] for m in matches])  # limitiamo il contesto
        return ctx

    def summarize(self, search_results):
        context = self._build_context(search_results)

        prompt = f"""
Sei un assistente che redige report in Markdown.

Contesto recuperato dalla memoria (estratti):
---
{context}
---

Risultati di ricerca (con link):
{json.dumps(search_results, ensure_ascii=False, indent=2)}

Richiesta:
- Crea un report in **Markdown** ben strutturato.
- Includi sezioni per argomento.
- Cita i link tra parentesi dopo i punti rilevanti.
- Evita testo superfluo. Solo il report.
"""
        md = self.ask(prompt)

        # salva il report in LTM
        self.memory.upsert(
            texts=[md],
            metadatas=[{
                "type": "summary_report",
                "timestamp": int(time.time())
            }]
        )
        return md