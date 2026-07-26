"""LLM-based structured extraction (Module 4)."""

from tradefin.extraction.extractor import (
    SCHEMA_BY_TYPE,
    ExtractionError,
    extract_document,
)

__all__ = [
    "SCHEMA_BY_TYPE",
    "ExtractionError",
    "extract_document",
]
