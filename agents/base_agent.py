class BaseAgent:
    def __init__(self, llm):
        self.llm = llm

    def ask(self, prompt):
        return self.llm.chat(prompt)