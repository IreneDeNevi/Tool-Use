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
        
        plan = {}
        if start != -1 and end != -1:
            plan_json_str = raw[start:end+1]
            
            # Prova parsing con varie strategie
            try:
                plan = json.loads(plan_json_str)
            except json.JSONDecodeError:
                # Se fallisce, prova a correggere errori comuni
                # Rimuovi commenti//
                plan_json_str = '\n'.join([
                    line.split('//')[0] if '//' in line else line
                    for line in plan_json_str.split('\n')
                ])
                try:
                    plan = json.loads(plan_json_str)
                except json.JSONDecodeError:
                    # Se ancora fallisce, usa default
                    plan = {
                        "core_topics": [user_input[:50]],
                        "related_topics": [],
                        "search_terms": [user_input[:50]]
                    }

        # Assicurati di avere i campi necessari
        if not plan:
            plan = {
                "core_topics": [user_input[:50]],
                "related_topics": [],
                "search_terms": [user_input[:50]]
            }

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