# Build Roadmap

Each module is a coherent unit ending in a git commit, so the history reads like a professional project.

| # | Module | Status | Key deliverable |
|---|--------|--------|-----------------|
| 0 | Foundations & scaffold | ✅ done | Repo structure, env, git |
| 1 | Synthetic data generator | ✅ done | Generate realistic LC / Invoice / BoL PDFs |
| 2 | Ingestion layer | ✅ done | PDF parsing + doc-type detection |
| 3 | LLM setup (local) | ✅ done | Provider-agnostic LLM client (Ollama) |
| 4 | Extraction agent | ✅ done | Schema-driven structured extraction (validated + retry). OCR fallback deferred to a later scanned-doc step. |
| 5 | Compliance engine | ⬜ todo | Rules-as-code + RAG over UCP 600 with citations |
| 6 | Orchestration | ⬜ todo | LangGraph state machine, retries, aggregation |
| 7 | API + UI + Docker | ⬜ todo | FastAPI + Streamlit + container |
| 8 | Evaluation & polish | ⬜ todo | Test set, accuracy metrics, portfolio README |

## Glossary (trade-finance terms you'll be able to explain in interviews)

- **Letter of Credit (LC):** a bank's written promise to pay the seller once compliant documents are presented.
- **Commercial Invoice:** the seller's bill listing goods, quantities, and amount.
- **Bill of Lading (BoL):** issued by the carrier; proves goods were shipped; a document of title.
- **UCP 600:** *Uniform Customs and Practice for Documentary Credits* — the ICC rulebook (39 articles) governing how banks examine documents.
- **Discrepancy:** any mismatch between presented documents and the LC terms / UCP 600 that lets a bank refuse payment.
