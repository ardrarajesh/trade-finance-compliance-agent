"""
A deterministic, offline LLMClient for tests and development.

It never runs a model. You give it the response(s) it should return, and it
records every call it received so tests can assert on them. This lets us build
and test extraction/compliance logic without a GPU, an API key, or a running
Ollama server.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tradefin.llm.base import LLMClient


@dataclass
class RecordedCall:
    prompt: str
    system: str | None
    temperature: float


class MockLLMClient(LLMClient):
    """Return canned responses; remember how it was called.

    Three ways to configure the reply, in priority order:
    - `handler`: a function of the prompt -> response. Most flexible; lets a test
      return different JSON depending on which document/schema is in the prompt.
    - `responses`: a queue consumed one per call (repeats the last once exhausted).
    - `response`: a single fixed answer.
    """

    def __init__(
        self,
        response: str = "",
        *,
        responses: list[str] | None = None,
        handler: Callable[[str], str] | None = None,
    ):
        self._handler = handler
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
        if self._handler is not None:
            return self._handler(prompt)
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]
