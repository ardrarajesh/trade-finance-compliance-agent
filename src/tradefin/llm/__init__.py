"""Provider-agnostic LLM layer (Module 3)."""

from tradefin.llm.base import LLMClient
from tradefin.llm.factory import get_llm
from tradefin.llm.mock_client import MockLLMClient
from tradefin.llm.ollama_client import DEFAULT_MODEL, OllamaClient

__all__ = [
    "LLMClient",
    "MockLLMClient",
    "OllamaClient",
    "DEFAULT_MODEL",
    "get_llm",
]
