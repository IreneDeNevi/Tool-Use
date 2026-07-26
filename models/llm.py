import os
from huggingface_hub import InferenceApi
import asyncio

class LocalLLM:
    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.3", device_map: str | None = None):
        self.model_name = model_name
        self.device_map = device_map
        self.hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")

        if not self.hf_token:
            raise RuntimeError("HUGGINGFACE_HUB_TOKEN is required for Hugging Face inference")

        self.inference = InferenceApi(
            repo_id=self.model_name,
            token=self.hf_token,
            task="text-generation"
        )
        # If you want to use a local model/tokenizer, assign them to these
        # attributes (e.g. via a `load_local_model()` helper). By default
        # the class will fall back to the Hugging Face Inference API.
        self.tokenizer = None
        self.model = None

    def chat(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.3) -> str:
        """Generate text from either a local model (if loaded) or the
        Hugging Face Inference API. Prefers a loaded local model/tokenizer
        when both `self.model` and `self.tokenizer` are set.
        """
        # If a local model/tokenizer are available, use them.
        if self.model is not None and self.tokenizer is not None:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            try:
                import torch
                if torch.cuda.is_available():
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            except Exception:
                # torch might not be installed or GPU not available; continue
                pass
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )
            return self.tokenizer.decode(output[0], skip_special_tokens=True)

        # Fallback to Hugging Face Inference API
        result = self.inference(
            inputs=prompt,
            parameters={
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
            },
            wait_for_model=True,
        )
        if isinstance(result, str):
            return result
        # result may be a list of dicts or a dict
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                return first.get("generated_text") or str(result)
        if isinstance(result, dict):
            return result.get("generated_text") or str(result)
        return str(result)

    async def achat(self, prompt: str, **gen_kwargs) -> str:
        # esegue la generazione in thread per non bloccare l'event loop
        return await asyncio.to_thread(self.chat, prompt, **gen_kwargs)