"""Ollama LLM client for local AI processing.

All AI calls go through this client, ensuring everything stays local.
"""

import json
from typing import Any, Optional

import httpx
from langchain_community.llms import Ollama
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM

from app.config import settings


class TaxFlowOllama:
    """Wrapper around Ollama for local LLM inference."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        self.top_p = top_p if top_p is not None else settings.OLLAMA_TOP_P
        self.max_tokens = max_tokens if max_tokens is not None else settings.OLLAMA_MAX_TOKENS

        self._llm = Ollama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            num_predict=self.max_tokens,
            num_ctx=8192,
        )

    def invoke(self, prompt: str, system: Optional[str] = None, temperature: Optional[float] = None) -> str:
        """Send a prompt to the LLM and get a response."""
        full_prompt = prompt
        if system:
            full_prompt = f"<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{prompt} [/INST]"

        kwargs = {}
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self._llm.invoke(full_prompt, **kwargs)
        return response.strip()

    def chat(self, messages: list[dict], temperature: Optional[float] = None) -> str:
        """Chat completion with message history.

        messages: [{"role": "system"/"user"/"assistant", "content": "..."}]
        """
        system_msg = ""
        user_msgs = []

        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m["content"])

        prompt = "\n".join(user_msgs)
        return self.invoke(prompt, system=system_msg, temperature=temperature)

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m["name"].startswith(self.model) for m in models)
            return False
        except Exception:
            return False

    def list_available_models(self) -> list[str]:
        """List all available models in Ollama."""
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
            return []
        except Exception:
            return []

    def pull_model(self, model_name: Optional[str] = None) -> dict:
        """Pull a model in Ollama."""
        target = model_name or self.model
        try:
            response = httpx.post(
                f"{self.base_url}/api/pull",
                json={"name": target, "stream": False},
                timeout=300.0,
            )
            return {"success": response.status_code == 200, "message": response.text}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_model_info(self) -> dict:
        """Get info about the current model."""
        try:
            response = httpx.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}

    def update_settings(self, model: str, temperature: float):
        """Update model settings."""
        self.model = model
        self.temperature = temperature
        self._llm = Ollama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            num_predict=self.max_tokens,
            num_ctx=8192,
        )
