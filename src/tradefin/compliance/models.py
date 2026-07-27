"""Data models for compliance results."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """How serious a finding is."""

    DISCREPANCY = "DISCREPANCY"  # would justify a bank refusing the documents
    WARNING = "WARNING"          # worth a human's attention, not an outright refusal


class ComplianceFinding(BaseModel):
    """One problem found in a presentation, with the rule it offends."""

    code: str = Field(description="Stable machine code, e.g. AMOUNT_OVER_LC")
    title: str
    detail: str = Field(description="Human-readable explanation with the specifics")
    ucp_article: str = Field(description="e.g. 'UCP 600 Article 18'")
    ucp_summary: str = Field(description="Paraphrased summary of the cited rule")
    severity: Severity = Severity.DISCREPANCY


class ComplianceReport(BaseModel):
    """The full result of checking one presentation against a credit."""

    case_id: str | None = None
    findings: list[ComplianceFinding] = Field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return len(self.findings) == 0

    @property
    def codes(self) -> set[str]:
        """The set of finding codes -- handy for evaluation against labels."""
        return {f.code for f in self.findings}
