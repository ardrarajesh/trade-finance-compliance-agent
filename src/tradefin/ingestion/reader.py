"""
Ingestion: turn a PDF file on disk into text + a detected document type.

PIPELINE POSITION
-----------------
    PDF file  ->  [ INGESTION ]  ->  IngestedDocument(text, doc_type, ...)
                                     |
                                     v
                              extraction agent (Module 4)

Design decisions worth being able to explain:
- We separate "get the text" from "decide what it is". Each is simple and
  independently testable.
- If a PDF has little/no embedded text it is probably a *scan* (an image).
  We do not fail; we set `needs_ocr=True` so a later stage can OCR it. This is
  exactly how real document pipelines degrade gracefully.
- Document-type detection here is deliberately a cheap, transparent keyword
  scorer -- not an LLM. Cheap, deterministic, and good enough to route the
  document. (We save the LLM for the hard part: field extraction.)
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import pdfplumber
from pydantic import BaseModel

# If total extracted text is shorter than this, we assume the PDF is a scan
# with no embedded text layer and route it to OCR later.
_MIN_TEXT_CHARS = 30


class DocumentType(str, Enum):
    LETTER_OF_CREDIT = "LETTER_OF_CREDIT"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    BILL_OF_LADING = "BILL_OF_LADING"
    UNKNOWN = "UNKNOWN"


# Keywords that vote for each document type. Lower-cased substring matches.
# We give strong, distinctive phrases a higher weight than generic ones.
_TYPE_KEYWORDS: dict[DocumentType, list[tuple[str, int]]] = {
    DocumentType.LETTER_OF_CREDIT: [
        ("documentary credit", 5),
        ("irrevocable", 3),
        ("issuing bank", 3),
        ("applicant", 2),
        ("beneficiary", 2),
        ("latest date of shipment", 2),
    ],
    DocumentType.COMMERCIAL_INVOICE: [
        ("commercial invoice", 5),
        ("invoice no", 3),
        ("unit price", 2),
        ("total amount", 2),
    ],
    DocumentType.BILL_OF_LADING: [
        ("bill of lading", 5),
        ("b/l no", 3),
        ("shipper", 2),
        ("consignee", 2),
        ("on board", 2),
        ("port of loading", 1),
    ],
}


class IngestedDocument(BaseModel):
    """The output of ingesting a single PDF."""

    source_path: str
    doc_type: DocumentType
    text: str
    num_pages: int
    needs_ocr: bool


def extract_text(pdf_path: Path) -> tuple[str, int]:
    """Return (all_text, page_count) from a PDF's embedded text layer.

    Returns empty text (not an error) when the PDF has no text layer -- that is
    a valid signal that the document is a scan needing OCR.
    """
    pages_text: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text).strip(), len(pages_text)


def detect_document_type(text: str) -> DocumentType:
    """Score the text against each type's keywords; return the best match."""
    haystack = text.lower()
    best_type = DocumentType.UNKNOWN
    best_score = 0
    for doc_type, keywords in _TYPE_KEYWORDS.items():
        score = sum(weight for phrase, weight in keywords if phrase in haystack)
        if score > best_score:
            best_score, best_type = score, doc_type
    return best_type


def ingest(pdf_path: Path) -> IngestedDocument:
    """Full ingestion for one PDF: extract text and detect its type."""
    pdf_path = Path(pdf_path)
    text, num_pages = extract_text(pdf_path)
    needs_ocr = len(text) < _MIN_TEXT_CHARS

    # If we could not read text, we cannot classify yet -> UNKNOWN until OCR.
    doc_type = DocumentType.UNKNOWN if needs_ocr else detect_document_type(text)

    return IngestedDocument(
        source_path=str(pdf_path),
        doc_type=doc_type,
        text=text,
        num_pages=num_pages,
        needs_ocr=needs_ocr,
    )


def ingest_directory(case_dir: Path) -> list[IngestedDocument]:
    """Ingest every PDF in a folder (e.g. one case's three documents)."""
    case_dir = Path(case_dir)
    return [ingest(p) for p in sorted(case_dir.glob("*.pdf"))]
