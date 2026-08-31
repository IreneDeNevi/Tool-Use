import os
from huggingface_hub import InferenceClient


class LocalLLM:
    def __init__(
        self,
        model_name: str = os.getenv("LLM_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.3"),
        device_map: str | None = None,  # kept for API compatibility, unused
    ):
        self.model_name = model_name
        token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not token:
            raise RuntimeError("HUGGINGFACE_HUB_TOKEN is not set. Add it to your .env file.")
        self.inference = InferenceClient(model=model_name, token=token)
        print(f"[LLM] Using HuggingFace Inference API → {model_name}")

    def chat(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.3) -> str:
        try:
            result = self.inference.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            return result.choices[0].message.content
        except Exception as exc:
            return f"[Error in LLM inference: {str(exc)}]"

        if isinstance(result, dict):
            return result.get("generated_text") or str(result)
        return str(result)

    async def achat(self, prompt: str, **gen_kwargs) -> str:
        # esegue la generazione in thread per non bloccare l'event loop
        return await asyncio.to_thread(self.chat, prompt, **gen_kwargs)