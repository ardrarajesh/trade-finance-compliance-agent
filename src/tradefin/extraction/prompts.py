"""
Prompts for schema-driven extraction.

KEY IDEA
--------
We don't hand-write "extract the invoice number, then the date, then...".
Instead we hand the model the Pydantic model's *JSON Schema* and say "fill this
in". The schema is generated from the same classes the rest of the system uses,
so the prompt can never drift out of sync with our data model. One source of
truth.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

EXTRACTION_SYSTEM = (
    "You are a meticulous trade-finance document analyst. "
    "You read a document and extract its fields as structured data. "
    "You reply with ONLY a single valid JSON object -- no prose, no explanations, "
    "no markdown code fences."
)


def build_extraction_prompt(text: str, schema: type[BaseModel]) -> str:
    """Ask the model to fill in `schema` from `text`."""
    json_schema = json.dumps(schema.model_json_schema(), indent=2)
    return f"""Extract the information from the DOCUMENT into a JSON object that conforms
to the following JSON Schema.

JSON SCHEMA:
{json_schema}

RULES:
- Output ONLY one JSON object. No commentary, no code fences.
- Use the exact field names from the schema.
- Dates must be in ISO format: YYYY-MM-DD.
- Numbers must be plain numeric values: no currency symbols, no thousands separators.
- Nested objects (like parties and money) must follow their sub-schemas exactly.

DOCUMENT:
\"\"\"
{text}
\"\"\"
"""


def build_repair_prompt(
    text: str, schema: type[BaseModel], bad_output: str, error: str
) -> str:
    """Follow-up prompt when the first answer failed validation."""
    return f"""Your previous response could not be parsed/validated.

PREVIOUS RESPONSE:
{bad_output}

VALIDATION ERROR:
{error}

Produce a corrected JSON object that fixes the error above.
{build_extraction_prompt(text, schema)}"""
