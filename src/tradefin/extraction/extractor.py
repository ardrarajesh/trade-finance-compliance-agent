"""
Turn an IngestedDocument into a validated Pydantic object using an LLM.

FLOW
----
    text + schema  ->  LLM  ->  raw string  ->  parse JSON  ->  validate
                                                     |              |
                                                     +--- retry <---+ (on failure)

The safety net is Pydantic: even if the model returns slightly wrong JSON, we
catch it, feed the error back, and ask for a fix. If it still fails after the
allowed retries we raise a clear ExtractionError rather than returning garbage.
This "LLM proposes, schema disposes" pattern is how you make LLM output
trustworthy enough for downstream logic.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from tradefin.extraction.prompts import (
    EXTRACTION_SYSTEM,
    build_extraction_prompt,
    build_repair_prompt,
)
from tradefin.ingestion import DocumentType, IngestedDocument
from tradefin.llm import LLMClient
from tradefin.schemas import BillOfLading, CommercialInvoice, LetterOfCredit

# Which Pydantic model to extract for each detected document type.
SCHEMA_BY_TYPE: dict[DocumentType, type[BaseModel]] = {
    DocumentType.LETTER_OF_CREDIT: LetterOfCredit,
    DocumentType.COMMERCIAL_INVOICE: CommercialInvoice,
    DocumentType.BILL_OF_LADING: BillOfLading,
}


class ExtractionError(RuntimeError):
    """Raised when we cannot produce a valid object from the model's output."""


def _extract_json_object(raw: str) -> dict:
    """Pull the outermost { ... } out of a raw model response and parse it.

    Tolerates the common cases where a model wraps JSON in prose or ```json
    fences: we simply take everything between the first '{' and the last '}'.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ExtractionError("No JSON object found in model response.")
    return json.loads(raw[start : end + 1])


def extract_document(
    doc: IngestedDocument,
    llm: LLMClient,
    *,
    max_retries: int = 1,
) -> BaseModel:
    """Extract a validated Pydantic object from an ingested document.

    Args:
        doc: the ingested document (text + detected type).
        llm: any LLMClient (real or mock).
        max_retries: how many *extra* attempts after the first, feeding the
            validation error back to the model each time.

    Returns:
        A validated instance of the schema for this document's type.

    Raises:
        ExtractionError: if the type has no schema, or all attempts fail.
    """
    schema = SCHEMA_BY_TYPE.get(doc.doc_type)
    if schema is None:
        raise ExtractionError(
            f"No extraction schema for document type {doc.doc_type.value!r}."
        )

    prompt = build_extraction_prompt(doc.text, schema)
    last_error: Exception | None = None

    for _attempt in range(max_retries + 1):
        raw = llm.complete(prompt, system=EXTRACTION_SYSTEM, temperature=0.0)
        try:
            data = _extract_json_object(raw)
            return schema.model_validate(data)
        except (ExtractionError, json.JSONDecodeError, ValidationError) as err:
            last_error = err
            prompt = build_repair_prompt(doc.text, schema, raw, str(err))

    raise ExtractionError(
        f"Failed to extract a valid {schema.__name__} after "
        f"{max_retries + 1} attempt(s). Last error: {last_error}"
    )
