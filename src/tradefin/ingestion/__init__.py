"""PDF ingestion: text extraction + document-type detection (Module 2)."""

from tradefin.ingestion.reader import (
    DocumentType,
    IngestedDocument,
    detect_document_type,
    extract_text,
    ingest,
    ingest_directory,
)

__all__ = [
    "DocumentType",
    "IngestedDocument",
    "detect_document_type",
    "extract_text",
    "ingest",
    "ingest_directory",
]
