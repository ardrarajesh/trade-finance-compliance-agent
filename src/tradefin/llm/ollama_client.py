"""
The real local backend: talks to an Ollama server running on your machine.

Ollama exposes a local HTTP API (default http://localhost:11434). The `ollama`
Python package is a thin client over it. Install the Ollama app, `ollama pull`
a model, and this class can chat with it -- all offline.
"""

from __future__ import annotations

from tradefin.llm.base import LLMClient

# Default model: small enough for ~8 GB RAM, good at following instructions.
DEFAULT_MODEL = "llama3.2:3b"


class OllamaClient(LLMClient):
    def __init__(self, model: str = DEFAULT_MODEL, host: str | None = None):
        # Import lazily so the whole project does not require `ollama` to be
        # installed unless you actually use this backend.
        import ollama

        self._model = model
        self._client = ollama.Client(host=host) if host else ollama.Client()

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": temperature},
        )
        return response["message"]["content"]
