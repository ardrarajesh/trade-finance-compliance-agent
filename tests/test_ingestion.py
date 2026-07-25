"""Tests for the ingestion layer (Module 2)."""

from tradefin.generation import build_case
from tradefin.generation.render import render_case
from tradefin.ingestion import (
    DocumentType,
    classification_confidence,
    detect_document_type,
    ingest,
    ingest_directory,
)


def test_detect_document_type_from_text():
    assert detect_document_type("IRREVOCABLE DOCUMENTARY CREDIT ... issuing bank") \
        == DocumentType.LETTER_OF_CREDIT
    assert detect_document_type("COMMERCIAL INVOICE\nInvoice No. INV-1") \
        == DocumentType.COMMERCIAL_INVOICE
    assert detect_document_type("BILL OF LADING\nShipper ...") \
        == DocumentType.BILL_OF_LADING
    assert detect_document_type("random unrelated text") == DocumentType.UNKNOWN


def test_ingest_generated_case_roundtrip(tmp_path):
    # Generate -> render to PDFs -> ingest, and check we recover the doc types.
    case = build_case(seed=123)
    case_dir = render_case(case, tmp_path)

    docs = ingest_directory(case_dir)
    found_types = {d.doc_type for d in docs}

    assert DocumentType.LETTER_OF_CREDIT in found_types
    assert DocumentType.COMMERCIAL_INVOICE in found_types
    assert DocumentType.BILL_OF_LADING in found_types

    # Digital PDFs have a text layer, so none should be routed to OCR.
    assert all(not d.needs_ocr for d in docs)


def test_ingest_finds_key_fields_in_text(tmp_path):
    case = build_case(seed=123)
    case_dir = render_case(case, tmp_path)

    lc_doc = ingest(case_dir / "letter_of_credit.pdf")
    # The LC number should survive the object -> PDF -> text round trip.
    assert case.letter_of_credit.lc_number in lc_doc.text


def test_classification_confidence_scores():
    # A clear Letter of Credit should score above zero...
    assert classification_confidence("IRREVOCABLE DOCUMENTARY CREDIT, issuing bank") > 0
    # ...and unrelated text should score exactly zero.
    assert classification_confidence("the quick brown fox") == 0


def test_ingest_populates_classification_score(tmp_path):
    case = build_case(seed=123)
    case_dir = render_case(case, tmp_path)
    lc_doc = ingest(case_dir / "letter_of_credit.pdf")
    # A confidently-classified document carries a positive score.
    assert lc_doc.classification_score > 0
