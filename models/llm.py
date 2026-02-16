from transformers import AutoTokenizer, AutoModelForCausalLM
import torch, asyncio

class LocalLLM:
    def __init__(self, model_name="mistralai/Mistral-7B-Instruct-v0.3", device_map="auto"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=device_map
        )

    def chat(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.3) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        output = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature
        )
        return self.tokenizer.decode(output[0], skip_special_tokens=True)

    async def achat(self, prompt: str, **gen_kwargs) -> str:
        # esegue la generazione in thread per non bloccare l'event loop
        return await asyncio.to_thread(self.chat, prompt, **gen_kwargs)