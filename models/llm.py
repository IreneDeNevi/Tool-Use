import os
from huggingface_hub import InferenceClient
import asyncio

class LocalLLM:
    def __init__(self, model_name: str = "gpt2", device_map: str | None = None):
        self.model_name = model_name
        self.device_map = device_map
        self.hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")

        # Try to load model locally first
        self.tokenizer = None
        self.model = None
        self.inference = None
        
        try:
            # Try to load model with transformers
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print(f"[LocalLLM] Loading {model_name} locally...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device_map or device,
                torch_dtype=torch.float32
            )
            print(f"[LocalLLM] Model loaded successfully on {device}")
        except Exception as e:
            print(f"[LocalLLM] Could not load model locally: {e}")
            print(f"[LocalLLM] Falling back to HuggingFace Inference API")
            
            # Fallback to HF Inference API if available
            if self.hf_token:
                self.inference = InferenceClient(
                    model=self.model_name,
                    token=self.hf_token
                )
            else:
                raise RuntimeError("Could not load model locally and HUGGINGFACE_HUB_TOKEN not set")

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

        # Fallback to Hugging Face Inference API (using InferenceClient)
        try:
            result = self.inference.text_generation(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            # If text_generation fails, try to return error message
            return f"[Error in LLM inference: {str(exc)}]"
        
        if isinstance(result, str):
            return result
        # result may be a dict or an object with attributes
        if hasattr(result, "generated_text"):
            return result.generated_text
        if isinstance(result, dict):
            return result.get("generated_text") or str(result)
        return str(result)

    async def achat(self, prompt: str, **gen_kwargs) -> str:
        # esegue la generazione in thread per non bloccare l'event loop
        return await asyncio.to_thread(self.chat, prompt, **gen_kwargs)