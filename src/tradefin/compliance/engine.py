"""
The compliance engine: deterministic rules-as-code.

Each check compares the extracted Letter of Credit, Commercial Invoice and Bill
of Lading and returns a ComplianceFinding when something is wrong, or None when
that rule is satisfied. `check_compliance` runs them all and collects a report.

WHY DETERMINISTIC (not an LLM)?
------------------------------
Compliance decisions must be explainable, reproducible, and auditable. "Invoice
total 30,791.25 exceeds credit 26,775 + 5% tolerance" is a fact you can defend to
a regulator. An LLM guessing yes/no is not. We use code for the verdict and cite
UCP 600 for the justification. (The LLM's job was the messy part -- reading the
PDF -- back in Module 4.)
"""

from __future__ import annotations

from decimal import Decimal

from tradefin.compliance.models import ComplianceFinding, ComplianceReport
from tradefin.compliance.rulebook import get_rule
from tradefin.schemas import BillOfLading, CommercialInvoice, LetterOfCredit


def _norm(text: str) -> str:
    """Normalise a string for comparison: collapse whitespace, lower-case."""
    return " ".join(text.split()).strip().lower()


def _finding(code: str, title: str, detail: str, rule_key: str) -> ComplianceFinding:
    """Build a finding, pulling the citation from the rulebook."""
    rule = get_rule(rule_key)
    return ComplianceFinding(
        code=code,
        title=title,
        detail=detail,
        ucp_article=rule["article"],
        ucp_summary=rule["summary"],
    )


# --------------------------------------------------------------------------
# Individual checks. Each returns ComplianceFinding | None.
# --------------------------------------------------------------------------
def check_amount_within_tolerance(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    max_allowed = lc.amount.amount * (Decimal(1) + lc.tolerance_pct / Decimal(100))
    if invoice.total_amount.amount > max_allowed:
        return _finding(
            "AMOUNT_OVER_LC",
            "Invoice amount exceeds the credit amount",
            f"Invoice total {invoice.total_amount.currency} "
            f"{invoice.total_amount.amount:,.2f} exceeds the credit amount "
            f"{lc.amount.currency} {lc.amount.amount:,.2f} plus the stated "
            f"{lc.tolerance_pct}% tolerance (maximum {max_allowed:,.2f}).",
            "art_30",
        )
    return None


def check_currency_match(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    if invoice.total_amount.currency != lc.amount.currency:
        return _finding(
            "CURRENCY_MISMATCH",
            "Invoice currency differs from the credit",
            f"Invoice is in {invoice.total_amount.currency} but the credit is "
            f"issued in {lc.amount.currency}. The invoice must be in the same "
            f"currency as the credit.",
            "art_18",
        )
    return None


def check_goods_description(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    if _norm(invoice.goods_description) != _norm(lc.goods_description):
        return _finding(
            "GOODS_DESCRIPTION_MISMATCH",
            "Goods description does not correspond with the credit",
            f"Invoice describes the goods as '{invoice.goods_description}', which "
            f"does not correspond with the credit's '{lc.goods_description}'.",
            "art_18",
        )
    return None


def check_ports(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    if _norm(bol.port_of_loading) != _norm(lc.port_of_loading) or _norm(
        bol.port_of_discharge
    ) != _norm(lc.port_of_discharge):
        return _finding(
            "PORT_MISMATCH",
            "Bill of Lading ports differ from the credit",
            f"Bill of Lading shows loading '{bol.port_of_loading}' -> discharge "
            f"'{bol.port_of_discharge}', but the credit requires "
            f"'{lc.port_of_loading}' -> '{lc.port_of_discharge}'.",
            "art_20",
        )
    return None


def check_latest_shipment_date(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    if bol.shipment_date > lc.latest_shipment_date:
        return _finding(
            "LATE_SHIPMENT",
            "Shipment later than the latest shipment date",
            f"Goods were shipped on {bol.shipment_date.isoformat()}, after the "
            f"credit's latest shipment date of "
            f"{lc.latest_shipment_date.isoformat()}.",
            "art_20",
        )
    return None


def check_beneficiary_name(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    if _norm(invoice.seller.name) != _norm(lc.beneficiary.name):
        return _finding(
            "BENEFICIARY_NAME_MISMATCH",
            "Invoice seller does not match the credit beneficiary",
            f"Invoice is issued by '{invoice.seller.name}', but the credit's "
            f"beneficiary is '{lc.beneficiary.name}'. The invoice must appear to "
            f"be issued by the beneficiary.",
            "art_18",
        )
    return None


def check_transshipment(
    lc: LetterOfCredit, invoice: CommercialInvoice, bol: BillOfLading
) -> ComplianceFinding | None:
    transshipment_evident = "transship" in _norm(bol.goods_description)
    if not lc.transshipment_allowed and transshipment_evident:
        return _finding(
            "TRANSSHIPMENT_VIOLATION",
            "Transshipment occurred but is not allowed",
            "The Bill of Lading indicates transshipment, but the credit does not "
            "allow transshipment.",
            "art_20",
        )
    return None


# Order matters only for display; findings are independent.
CHECKS = [
    check_amount_within_tolerance,
    check_currency_match,
    check_goods_description,
    check_ports,
    check_latest_shipment_date,
    check_beneficiary_name,
    check_transshipment,
]


def check_compliance(
    lc: LetterOfCredit,
    invoice: CommercialInvoice,
    bol: BillOfLading,
    *,
    case_id: str | None = None,
) -> ComplianceReport:
    """Run every check and collect the findings into a report."""
    findings = []
    for check in CHECKS:
        result = check(lc, invoice, bol)
        if result is not None:
            findings.append(result)
    return ComplianceReport(case_id=case_id, findings=findings)


def check_case(case) -> ComplianceReport:
    """Convenience: run compliance directly on a ShipmentCase (ground truth)."""
    return check_compliance(
        case.letter_of_credit,
        case.commercial_invoice,
        case.bill_of_lading,
        case_id=case.case_id,
    )
