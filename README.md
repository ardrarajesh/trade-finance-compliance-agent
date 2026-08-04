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

### 1. Setup

```bash
conda activate tradefin
pip install -r requirements.txt
pip install -e .
pytest -q                     # run the test suite
```

### 2. Generate synthetic documents

```bash
python scripts/generate_data.py --n 8 --out data/synthetic
```

### 3. See a compliance audit report (no LLM / RAM needed)

The compliance engine is deterministic, so this always works:

```bash
python scripts/compliance_demo.py --seed 5 --discrepancies AMOUNT_OVER_LC PORT_MISMATCH
```

### 4. Run the full app (API + UI)

Terminal 1 — the API:

```bash
uvicorn tradefin.api.app:app --reload
```

Terminal 2 — the UI (talks to the API):

```bash
streamlit run ui/streamlit_app.py
```

Then open the UI at http://localhost:8501 and the API docs at http://localhost:8000/docs.
The pipeline uses a local Ollama model by default — set `OLLAMA_MODEL=llama3.2:1b`
on low-RAM machines, or `LLM_PROVIDER=mock` to run without a model.

### 5. Run everything in Docker

```bash
docker compose up --build
docker compose exec ollama ollama pull llama3.2:3b   # one-time model pull
```

## Evaluation

The discrepancy check is evaluated as a multi-label classification task against
the generator's ground-truth labels:

```bash
python scripts/evaluate.py --n 100
```

On 100 synthetic cases the deterministic compliance engine scores **1.00
precision / recall / F1** across all seven discrepancy types. Note what this
does and does not show: it confirms the engine's *rules correctly implement the
discrepancy definitions* when given correctly-read documents. Measuring how
accurately a live LLM extracts fields from the PDFs is a separate evaluation
(it requires a running model) and is intentionally kept distinct.

## Roadmap & progress

See [docs/ROADMAP.md](docs/ROADMAP.md). Each module is a self-contained, reviewable commit.

## License

MIT
