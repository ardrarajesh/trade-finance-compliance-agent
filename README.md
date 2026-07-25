# Agentic Trade-Finance Document Compliance Checker

> Upload a Letter of Credit and the documents presented against it (Commercial Invoice, Bill of Lading). An agentic pipeline reads them, extracts structured data, and checks them for discrepancies — both cross-document and against **UCP 600**, the international rulebook banks use — then produces a reviewable audit report with rule citations.

**Status:** 🚧 In active development (built module-by-module — see [docs/ROADMAP.md](docs/ROADMAP.md)).

---

## Why this project exists

In trade finance, banks manually check whether presented documents comply with the terms of a Letter of Credit and with UCP 600 rules. It is slow, expensive, and error-prone. This project automates that check with a modern, agentic LLM pipeline — using **fully synthetic data**, so it demonstrates the technique without any confidential information.

## Architecture

```
Upload → Ingestion (PDF text / OCR) → Extraction Agent (LLM → structured JSON)
       → Compliance Engine (deterministic cross-checks + RAG over UCP 600)
       → Orchestrator (LangGraph) → Audit Report + API + UI
```

## Tech stack

| Layer | Tools |
|-------|-------|
| Language | Python 3.11 |
| Data models | Pydantic v2 |
| Documents | ReportLab (generation), pdfplumber, Tesseract OCR |
| LLM | Provider-agnostic (Ollama local by default; pluggable OpenAI/Anthropic) |
| Retrieval | Vector store over UCP 600 rulebook (RAG) |
| Orchestration | LangGraph |
| Serving | FastAPI + Streamlit |
| Packaging | Docker |
| Quality | pytest, evaluation suite with accuracy metrics |

## Quickstart

> Full instructions land as each module is completed.

```bash
conda activate tradefin
pip install -r requirements.txt
pip install -e .
```

## Roadmap & progress

See [docs/ROADMAP.md](docs/ROADMAP.md). Each module is a self-contained, reviewable commit.

## License

MIT
