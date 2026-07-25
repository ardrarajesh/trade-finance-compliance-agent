"""
The LLM abstraction: one interface, many backends.

WHY AN INTERFACE?
-----------------
The rest of the system should not know or care *which* LLM it is talking to.
It depends on this abstract `LLMClient`, not on Ollama or OpenAI. That is the
Dependency Inversion Principle: high-level code (extraction, compliance)
depends on an abstraction, and the concrete backends depend on that same
abstraction. Swapping providers becomes "write one new subclass", not "edit the
whole codebase".
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Contract for anything that can turn a prompt into text."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        """Return the model's text response to `prompt`.

        Args:
            prompt: the user message / instruction.
            system: optional system message that sets the model's role/rules.
            temperature: 0.0 = deterministic (what we want for extraction);
                higher = more random. Extraction and compliance want 0.0 so the
                same document always yields the same answer.
        """
        raise NotImplementedError
