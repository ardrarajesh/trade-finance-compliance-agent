"""Tests for the FastAPI service (Module 7). Uses TestClient + mock LLM."""

import json

from fastapi.testclient import TestClient

from tradefin.api.app import app, llm_dependency
from tradefin.generation import Discrepancy, build_case
from tradefin.generation.render import render_case
from tradefin.llm import MockLLMClient


def _handler_for(case):
    lc = json.dumps(case.letter_of_credit.model_dump(mode="json"))
    inv = json.dumps(case.commercial_invoice.model_dump(mode="json"))
    bol = json.dumps(case.bill_of_lading.model_dump(mode="json"))

    def handler(prompt: str) -> str:
        if "LetterOfCredit" in prompt:
            return lc
        if "CommercialInvoice" in prompt:
            return inv
        if "BillOfLading" in prompt:
            return bol
        return "{}"

    return handler


def _upload_files(case_dir):
    """Open the three PDFs as multipart upload tuples."""
    return [
        ("files", (p.name, p.read_bytes(), "application/pdf"))
        for p in sorted(case_dir.glob("*.pdf"))
    ]


def test_health():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_check_endpoint_flags_discrepancies(tmp_path):
    case = build_case(
        seed=5, discrepancies=[Discrepancy.AMOUNT_OVER_LC, Discrepancy.PORT_MISMATCH]
    )
    case_dir = render_case(case, tmp_path)

    # Inject the smart mock in place of the real LLM.
    app.dependency_overrides[llm_dependency] = lambda: MockLLMClient(handler=_handler_for(case))
    try:
        client = TestClient(app)
        resp = client.post("/check", files=_upload_files(case_dir))
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_compliant"] is False
    codes = {f["code"] for f in body["findings"]}
    assert codes == {"AMOUNT_OVER_LC", "PORT_MISMATCH"}
    assert len(body["documents_detected"]) == 3


def test_check_endpoint_passes_clean_case(tmp_path):
    case = build_case(seed=123)
    case_dir = render_case(case, tmp_path)

    app.dependency_overrides[llm_dependency] = lambda: MockLLMClient(handler=_handler_for(case))
    try:
        client = TestClient(app)
        resp = client.post("/check", files=_upload_files(case_dir))
    finally:
        app.dependency_overrides.clear()

    body = resp.json()
    assert body["is_compliant"] is True
    assert body["findings"] == []
