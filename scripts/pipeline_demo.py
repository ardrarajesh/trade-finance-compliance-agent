"""
Run the full LangGraph pipeline on a case folder with a live LLM.

ingest -> extract (LLM) -> compliance -> report

Needs a working LLM backend. With free RAM:
  $env:OLLAMA_MODEL = "llama3.2:1b"
  python scripts\\pipeline_demo.py --case data\\synthetic\\CASE-13435
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tradefin.llm import get_llm
from tradefin.orchestration import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, default=Path("data/synthetic/CASE-13435"))
    args = parser.parse_args()

    print(f"Running pipeline on {args.case} ...\n")
    result = run_pipeline(args.case, get_llm())

    if result.get("errors"):
        print("Extraction issues:")
        for e in result["errors"]:
            print("  -", e)
        print()

    report = result.get("report")
    if report is None:
        print("No compliance report (a required document was missing or failed).")
        return

    print(f"Result: {'COMPLIANT' if report.is_compliant else 'DISCREPANCIES FOUND'}")
    for i, f in enumerate(report.findings, 1):
        print(f"  [{i}] {f.code}: {f.detail}  ({f.ucp_article})")


if __name__ == "__main__":
    main()
