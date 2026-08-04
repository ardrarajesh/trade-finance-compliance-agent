"""Tests for the LangGraph pipeline (Module 6). Fully offline via a smart mock."""

import json

from tradefin.generation import Discrepancy, build_case
from tradefin.generation.render import render_case
from tradefin.llm import MockLLMClient
from tradefin.orchestration import run_pipeline


def make_handler(case):
    """A prompt-aware mock: return each document's ground-truth JSON based on
    which schema (LetterOfCredit / CommercialInvoice / BillOfLading) the
    extraction prompt is asking for."""
    lc_json = json.dumps(case.letter_of_credit.model_dump(mode="json"))
    inv_json = json.dumps(case.commercial_invoice.model_dump(mode="json"))
    bol_json = json.dumps(case.bill_of_lading.model_dump(mode="json"))

    def handler(prompt: str) -> str:
        if "LetterOfCredit" in prompt:
            return lc_json
        if "CommercialInvoice" in prompt:
            return inv_json
        if "BillOfLading" in prompt:
            return bol_json
        return "{}"

    return handler


def test_pipeline_runs_end_to_end_on_compliant_case(tmp_path):
    case = build_case(seed=123)
    case_dir = render_case(case, tmp_path)

    result = run_pipeline(case_dir, MockLLMClient(handler=make_handler(case)))

    report = result["report"]
    assert report is not None
    assert report.is_compliant
    assert not result["errors"]


def test_pipeline_detects_injected_discrepancies(tmp_path):
    case = build_case(
        seed=5, discrepancies=[Discrepancy.AMOUNT_OVER_LC, Discrepancy.PORT_MISMATCH]
    )
    case_dir = render_case(case, tmp_path)

    result = run_pipeline(case_dir, MockLLMClient(handler=make_handler(case)))

    assert result["report"].codes == {"AMOUNT_OVER_LC", "PORT_MISMATCH"}


def test_pipeline_skips_compliance_when_a_document_is_missing(tmp_path):
    case = build_case(seed=7)
    case_dir = render_case(case, tmp_path)
    # Remove the Letter of Credit -> compliance cannot run.
    (case_dir / "letter_of_credit.pdf").unlink()

    result = run_pipeline(case_dir, MockLLMClient(handler=make_handler(case)))

    # The conditional edge routed to END; no report was produced.
    assert result.get("report") is None
