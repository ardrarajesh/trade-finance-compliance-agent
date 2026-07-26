"""Tests for the extraction agent (Module 4). Fully offline via MockLLMClient."""

import json

import pytest

from tradefin.extraction import ExtractionError, extract_document
from tradefin.generation import build_case
from tradefin.ingestion import DocumentType, IngestedDocument
from tradefin.llm import MockLLMClient
from tradefin.schemas import CommercialInvoice


def _doc(text: str, doc_type: DocumentType) -> IngestedDocument:
    """Helper to build an IngestedDocument without touching disk."""
    return IngestedDocument(
        source_path="mem://test.pdf",
        doc_type=doc_type,
        text=text,
        num_pages=1,
        needs_ocr=False,
        classification_score=10,
    )


def _invoice_json() -> tuple[str, CommercialInvoice]:
    """A guaranteed-valid invoice + its JSON string (our 'ground truth')."""
    invoice = build_case(seed=123).commercial_invoice
    payload = json.dumps(invoice.model_dump(mode="json"))
    return payload, invoice


def test_extracts_and_validates_invoice():
    payload, expected = _invoice_json()
    llm = MockLLMClient(response=payload)

    result = extract_document(_doc("(invoice text)", DocumentType.COMMERCIAL_INVOICE), llm)

    assert isinstance(result, CommercialInvoice)
    assert result.invoice_number == expected.invoice_number
    assert result.total_amount.amount == expected.total_amount.amount


def test_tolerates_prose_and_code_fences_around_json():
    payload, expected = _invoice_json()
    noisy = f"Sure! Here is the JSON you asked for:\n```json\n{payload}\n```\nHope that helps."
    llm = MockLLMClient(response=noisy)

    result = extract_document(_doc("(invoice text)", DocumentType.COMMERCIAL_INVOICE), llm)
    assert result.invoice_number == expected.invoice_number


def test_retries_after_invalid_first_response():
    payload, _ = _invoice_json()
    # First reply is unparseable; second is valid -> should recover on retry.
    llm = MockLLMClient(responses=["not json at all", payload])

    result = extract_document(
        _doc("(invoice text)", DocumentType.COMMERCIAL_INVOICE), llm, max_retries=1
    )
    assert isinstance(result, CommercialInvoice)
    assert len(llm.calls) == 2  # proves it actually retried


def test_gives_up_after_exhausting_retries():
    llm = MockLLMClient(response="never valid json")
    with pytest.raises(ExtractionError):
        extract_document(
            _doc("(invoice text)", DocumentType.COMMERCIAL_INVOICE), llm, max_retries=1
        )


def test_unknown_document_type_raises():
    payload, _ = _invoice_json()
    llm = MockLLMClient(response=payload)
    with pytest.raises(ExtractionError):
        extract_document(_doc("(text)", DocumentType.UNKNOWN), llm)
