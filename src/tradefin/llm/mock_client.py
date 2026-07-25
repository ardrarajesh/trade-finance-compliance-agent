"""
A deterministic, offline LLMClient for tests and development.

It never runs a model. You give it the response(s) it should return, and it
records every call it received so tests can assert on them. This lets us build
and test extraction/compliance logic without a GPU, an API key, or a running
Ollama server.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tradefin.llm.base import LLMClient


@dataclass
class RecordedCall:
    prompt: str
    system: str | None
    temperature: float


class MockLLMClient(LLMClient):
    """Return canned responses; remember how it was called.

    - Pass `response` for a single fixed answer, or
    - Pass `responses` for a queue consumed one per call (repeats the last one
      once the queue is exhausted, so tests never crash on an extra call).
    """

    def __init__(self, response: str = "", *, responses: list[str] | None = None):
        self._responses = list(responses) if responses else [response]
        self.calls: list[RecordedCall] = []

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        self.calls.append(RecordedCall(prompt=prompt, system=system, temperature=temperature))
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]
