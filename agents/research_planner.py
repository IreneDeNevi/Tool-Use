import json, time
from agents.base_agent import BaseAgent
from tools.memory import VectorMemory

class ResearchPlannerAgent(BaseAgent):
    def __init__(self, llm, memory: VectorMemory):
        super().__init__(llm)
        self.memory = memory

    def plan(self, user_input: str) -> dict:
        prompt = f"""
Sei un agente che pianifica ricerche web.
L'utente chiede: {user_input}

Genera un piano di ricerca con formato JSON:
{{
  "core_topics": ["...", "..."],
  "related_topics": ["...", "..."],
  "avoid": ["...", "..."],
  "freshness": "pd|pw|pm|py|YYYY-MM-DDtoYYYY-MM-DD",
  "search_terms": ["...", "..."]  // opzionale, se vuoi derivarli già
}}
Rispondi SOLO con JSON valido.
"""
        raw = self.ask(prompt)
        # estrai solo la parte JSON in caso il modello aggiunga testo prima/dopo
        start = raw.find("{")
        end = raw.rfind("}")
        plan_json = raw[start:end+1] if start != -1 and end != -1 else "{}"
        plan = json.loads(plan_json)

        # Salva in LTM
        ts = int(time.time())
        self.memory.upsert(
            texts=[json.dumps(plan, ensure_ascii=False)],
            metadatas=[{
                "type": "research_plan",
                "timestamp": ts,
                "user_query": user_input
            }]
        )
        return plan