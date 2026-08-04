r"""
The end-to-end pipeline as a LangGraph state machine.

WHY A GRAPH INSTEAD OF A FUNCTION?
----------------------------------
Our flow is currently linear, but real document workflows branch and retry:
some documents need OCR, some fail extraction, some presentations are missing a
required document. Modelling the flow as an explicit graph of nodes + edges
makes those branches first-class and inspectable, and it is exactly the
"agentic workflow / LangGraph" pattern used in production. Each node is a small
pure function that reads the shared state and returns updates to it.

    ingest -> extract -> (all 3 docs present?) --yes--> compliance -> END
                                              \--no--> END (report why)
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from tradefin.compliance import ComplianceReport, check_compliance
from tradefin.extraction import ExtractionError, extract_document
from tradefin.ingestion import DocumentType, IngestedDocument, ingest_directory
from tradefin.llm import LLMClient
from tradefin.schemas import BillOfLading, CommercialInvoice, LetterOfCredit

# The document types this pipeline needs to run a compliance check.
_REQUIRED = {
    DocumentType.LETTER_OF_CREDIT,
    DocumentType.COMMERCIAL_INVOICE,
    DocumentType.BILL_OF_LADING,
}


class PipelineState(TypedDict, total=False):
    """Shared state passed between nodes. `total=False` = keys are optional."""

    case_dir: str
    documents: list[IngestedDocument]
    extracted: dict[str, object]  # DocumentType.value -> extracted Pydantic object
    report: ComplianceReport | None
    errors: list[str]


def build_pipeline(llm: LLMClient):
    """Compile a LangGraph pipeline that uses the given LLM for extraction."""

    def ingest_node(state: PipelineState) -> PipelineState:
        docs = ingest_directory(Path(state["case_dir"]))
        return {"documents": docs, "extracted": {}, "errors": []}

    def extract_node(state: PipelineState) -> PipelineState:
        extracted: dict[str, object] = {}
        errors: list[str] = list(state.get("errors", []))
        for doc in state["documents"]:
            if doc.doc_type not in _REQUIRED:
                continue
            try:
                extracted[doc.doc_type.value] = extract_document(doc, llm)
            except ExtractionError as e:
                errors.append(f"{doc.doc_type.value}: {e}")
        return {"extracted": extracted, "errors": errors}

    def compliance_node(state: PipelineState) -> PipelineState:
        ex = state["extracted"]
        lc: LetterOfCredit = ex[DocumentType.LETTER_OF_CREDIT.value]
        invoice: CommercialInvoice = ex[DocumentType.COMMERCIAL_INVOICE.value]
        bol: BillOfLading = ex[DocumentType.BILL_OF_LADING.value]
        report = check_compliance(lc, invoice, bol, case_id=Path(state["case_dir"]).name)
        return {"report": report}

    def have_all_documents(state: PipelineState) -> str:
        """Conditional edge: only run compliance if all 3 docs were extracted."""
        present = set(state.get("extracted", {}).keys())
        return "yes" if {t.value for t in _REQUIRED} <= present else "no"

    graph = StateGraph(PipelineState)
    graph.add_node("ingest", ingest_node)
    graph.add_node("extract", extract_node)
    graph.add_node("compliance", compliance_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "extract")
    graph.add_conditional_edges("extract", have_all_documents, {"yes": "compliance", "no": END})
    graph.add_edge("compliance", END)

    return graph.compile()


def run_pipeline(case_dir: str | Path, llm: LLMClient) -> PipelineState:
    """Convenience wrapper: build the graph and run one case through it."""
    pipeline = build_pipeline(llm)
    return pipeline.invoke({"case_dir": str(case_dir)})
