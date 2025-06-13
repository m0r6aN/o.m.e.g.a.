# agents/workflow_planner/internal/llm_adapter.py

import os
from typing import Optional, Dict, Any

class LLMAdapter:
    def __init__(self, default_model: Optional[str] = None):
        self.default_model = default_model or os.getenv("DEFAULT_MODEL_PROVIDER", "gpt-4o")

    def generate(self, prompt: str, model: Optional[str] = None, task_type: Optional[str] = None, **kwargs) -> str:
        if not model and task_type:
            model = os.getenv(f"{task_type.upper()}_MODEL")
        model = model or self.default_model

        if model.startswith("gpt"):
            return self._generate_openai(prompt, model, **kwargs)
        elif model.startswith("claude"):
            return self._generate_claude(prompt, model, **kwargs)
        elif model.startswith("gemini"):
            return self._generate_gemini(prompt, model, **kwargs)
        elif model.startswith("grok"):
            return self._generate_grok(prompt, model, **kwargs)
        else:
            raise ValueError(f"Unsupported model: {model}")

    def _generate_openai(self, prompt: str, model: str, **kwargs) -> str:
        print(f"🔮 [OpenAI] Model: {model} | Prompt: {prompt}")
        return f"[OpenAI:{model}] {prompt}"

    def _generate_claude(self, prompt: str, model: str, **kwargs) -> str:
        print(f"🦙 [Claude] Model: {model} | Prompt: {prompt}")
        return f"[Claude:{model}] {prompt}"

    def _generate_gemini(self, prompt: str, model: str, **kwargs) -> str:
        print(f"🔷 [Gemini] Model: {model} | Prompt: {prompt}")
        return f"[Gemini:{model}] {prompt}"

    def _generate_grok(self, prompt: str, model: str, **kwargs) -> str:
        print(f"🧠 [Grok] Model: {model} | Prompt: {prompt}")
        return f"[Grok:{model}] {prompt}"

# Singleton instance
llm_adapter = LLMAdapter()
