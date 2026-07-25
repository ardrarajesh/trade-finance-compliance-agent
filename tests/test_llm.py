"""Tests for the LLM abstraction (Module 3).

These run fully offline using the mock backend -- no Ollama, no network.
"""

import pytest

from tradefin.llm import LLMClient, MockLLMClient, get_llm


def test_mock_returns_fixed_response():
    llm = MockLLMClient(response="hello world")
    assert llm.complete("anything") == "hello world"


def test_mock_records_calls():
    llm = MockLLMClient(response="ok")
    llm.complete("prompt A", system="be terse", temperature=0.0)
    assert len(llm.calls) == 1
    assert llm.calls[0].prompt == "prompt A"
    assert llm.calls[0].system == "be terse"


def test_mock_consumes_response_queue():
    llm = MockLLMClient(responses=["first", "second"])
    assert llm.complete("a") == "first"
    assert llm.complete("b") == "second"
    # Queue exhausted -> repeats the last response instead of crashing.
    assert llm.complete("c") == "second"


def test_mock_is_an_llmclient():
    # The mock must satisfy the same interface as the real backend.
    assert isinstance(MockLLMClient(), LLMClient)


def test_factory_returns_mock_when_requested():
    assert isinstance(get_llm("mock"), MockLLMClient)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        get_llm("nonsense-provider")
