"""Tests for the synthetic case generator (Module 1)."""

from decimal import Decimal

from tradefin.generation import Discrepancy, build_case


def test_compliant_case_has_no_injected_discrepancies():
    case = build_case(seed=1)
    assert case.injected_discrepancies == []
    # Invoice total should sit within the LC amount + tolerance.
    lc = case.letter_of_credit
    max_allowed = lc.amount.amount * (1 + lc.tolerance_pct / Decimal("100"))
    assert case.commercial_invoice.total_amount.amount <= max_allowed


def test_amount_over_lc_pushes_invoice_beyond_tolerance():
    case = build_case(seed=1, discrepancies=[Discrepancy.AMOUNT_OVER_LC])
    lc = case.letter_of_credit
    max_allowed = lc.amount.amount * (1 + lc.tolerance_pct / Decimal("100"))
    assert case.commercial_invoice.total_amount.amount > max_allowed
    assert "AMOUNT_OVER_LC" in case.injected_discrepancies


def test_port_mismatch_breaks_discharge_port():
    case = build_case(seed=2, discrepancies=[Discrepancy.PORT_MISMATCH])
    assert (
        case.bill_of_lading.port_of_discharge
        != case.letter_of_credit.port_of_discharge
    )


def test_transshipment_violation():
    case = build_case(seed=1, discrepancies=[Discrepancy.TRANSSHIPMENT_VIOLATION])
    # 1. The LC forbids transshipment...
    assert case.letter_of_credit.transshipment_allowed is False
    # 2. ...yet the Bill of Lading shows it happened (the evidence).
    assert "transship" in case.bill_of_lading.goods_description.lower()
    # 3. The discrepancy was labelled for later evaluation.
    assert "TRANSSHIPMENT_VIOLATION" in case.injected_discrepancies


def test_generation_is_reproducible():
    a = build_case(seed=7)
    b = build_case(seed=7)
    assert a.model_dump(mode="json") == b.model_dump(mode="json")


def test_documents_own_independent_party_objects():
    # Regression: the invoice's seller must NOT be the same object as the LC's
    # beneficiary, or mutating one silently changes the other (aliasing bug).
    case = build_case(seed=7)
    assert case.commercial_invoice.seller is not case.letter_of_credit.beneficiary


def test_beneficiary_mismatch_is_a_real_mismatch():
    case = build_case(seed=5, discrepancies=[Discrepancy.BENEFICIARY_NAME_MISMATCH])
    assert case.commercial_invoice.seller.name != case.letter_of_credit.beneficiary.name
