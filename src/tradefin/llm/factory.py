"""
Choose an LLM backend from configuration (environment variables).

Everything downstream calls `get_llm()` and receives *some* LLMClient. Whether
that is Ollama or the mock is a config decision, not a code decision. Set:

    LLM_PROVIDER = ollama | mock      (default: ollama)
    OLLAMA_MODEL = llama3.2:3b        (default)
"""

from __future__ import annotations

import os

from tradefin.llm.base import LLMClient
from tradefin.llm.mock_client import MockLLMClient
from tradefin.llm.ollama_client import DEFAULT_MODEL, OllamaClient


def get_llm(provider: str | None = None) -> LLMClient:
    provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()

    if provider == "ollama":
        return OllamaClient(model=os.getenv("OLLAMA_MODEL", DEFAULT_MODEL))
    if provider == "mock":
        return MockLLMClient(response="(mock response)")

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use 'ollama' or 'mock'.")
