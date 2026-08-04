"""
FastAPI app: upload a case's PDFs, get back a compliance audit report.

Endpoints:
  GET  /health   -> liveness check
  POST /check    -> multipart upload of PDFs -> CheckResponse (JSON)

The LLM is provided via a dependency (`llm_dependency`) so tests can override it
with the mock -- no model or RAM needed to test the API.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, UploadFile
from pydantic import BaseModel

from tradefin.compliance import ComplianceFinding
from tradefin.llm import LLMClient, get_llm
from tradefin.orchestration import run_pipeline

app = FastAPI(
    title="Trade-Finance Document Compliance Checker",
    description="Upload a Letter of Credit, Commercial Invoice and Bill of Lading; "
    "receive a UCP 600 compliance audit report.",
    version="0.1.0",
)


class CheckResponse(BaseModel):
    case_id: str | None = None
    is_compliant: bool
    documents_detected: list[str]
    findings: list[ComplianceFinding]
    errors: list[str]


def llm_dependency() -> LLMClient:
    """Which LLM the API uses. Overridden in tests with a mock."""
    return get_llm()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/check", response_model=CheckResponse)
async def check(
    files: list[UploadFile] = File(...),
    llm: LLMClient = Depends(llm_dependency),
) -> CheckResponse:
    """Save the uploaded PDFs to a temp folder and run the full pipeline."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for i, upload in enumerate(files):
            name = Path(upload.filename or f"document_{i}.pdf").name
            (tmpdir / name).write_bytes(await upload.read())

        result = run_pipeline(tmpdir, llm)

    report = result.get("report")
    return CheckResponse(
        case_id=report.case_id if report else None,
        is_compliant=report.is_compliant if report else False,
        documents_detected=[d.doc_type.value for d in result.get("documents", [])],
        findings=report.findings if report else [],
        errors=result.get("errors", []),
    )
