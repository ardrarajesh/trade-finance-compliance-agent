"""
Live end-to-end demo: ingest a case's PDFs and extract structured data with the
configured LLM (Ollama by default).

Run when your RAM is free (close browsers first):

  $env:OLLAMA_MODEL = "llama3.2:1b"
  python scripts\\extract_demo.py --case data\\synthetic\\CASE-13435

Uses the mock backend instead if you set LLM_PROVIDER=mock.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tradefin.extraction import ExtractionError, extract_document
from tradefin.ingestion import ingest_directory
from tradefin.llm import get_llm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, default=Path("data/synthetic/CASE-13435"))
    args = parser.parse_args()

    llm = get_llm()
    print(f"Ingesting {args.case} ...\n")

    for doc in ingest_directory(args.case):
        name = Path(doc.source_path).name
        print(f"=== {name}  ({doc.doc_type.value}) ===")
        try:
            obj = extract_document(doc, llm)
            print(obj.model_dump_json(indent=2))
        except ExtractionError as e:
            print(f"  extraction failed: {e}")
        print()


if __name__ == "__main__":
    main()
