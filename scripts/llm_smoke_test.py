"""
Live smoke test for the local Ollama backend.

Run this AFTER you have:
  1. installed the Ollama app, and
  2. pulled a model:  ollama pull llama3.2:3b

Usage (PowerShell):
  & "C:\\Users\\ardrakr\\anaconda3\\envs\\tradefin\\python.exe" scripts\\llm_smoke_test.py

It asks the model a trivial question and prints the answer, confirming your
whole local-LLM setup works end to end.
"""

from __future__ import annotations

from tradefin.llm import get_llm


def main() -> None:
    llm = get_llm("ollama")  # or set LLM_PROVIDER=ollama and call get_llm()
    print("Sending a test prompt to the local model...\n")
    answer = llm.complete(
        "Reply with exactly one short sentence confirming you are working.",
        system="You are a concise assistant.",
    )
    print("Model replied:\n ", answer.strip())


if __name__ == "__main__":
    main()
