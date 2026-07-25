"""
Build synthetic ShipmentCases: coherent, fully-compliant trade transactions,
optionally mutated to inject specific, labelled discrepancies.

DESIGN IDEA
-----------
1. `build_compliant_case()` creates an LC + Invoice + BoL that all agree with
   each other and satisfy UCP 600 -> zero discrepancies.
2. Each `Discrepancy` enum value has a small "mutator" function that breaks the
   case in exactly one way (e.g. push the invoice amount above the LC amount).
3. `build_case(seed, discrepancies=[...])` builds a compliant case, applies the
   requested mutators, and records their codes in `injected_discrepancies`.

This gives us labelled data for free: we know precisely what is wrong with each
case, so later we can measure whether the compliance engine finds it.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from faker import Faker

from tradefin.schemas import (
    BillOfLading,
    CommercialInvoice,
    Incoterm,
    LetterOfCredit,
    Money,
    Party,
    ShipmentCase,
)


class Discrepancy(str, Enum):
    """The kinds of problems we can deliberately plant in a case."""

    AMOUNT_OVER_LC = "AMOUNT_OVER_LC"                 # invoice > LC amount + tolerance
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"           # invoice currency != LC currency
    GOODS_DESCRIPTION_MISMATCH = "GOODS_DESCRIPTION_MISMATCH"
    LATE_SHIPMENT = "LATE_SHIPMENT"                   # shipped after latest_shipment_date
    PORT_MISMATCH = "PORT_MISMATCH"                   # BoL ports != LC ports
    BENEFICIARY_NAME_MISMATCH = "BENEFICIARY_NAME_MISMATCH"


# A few plausible goods so cases look realistic.
_GOODS = [
    ("Cotton bath towels, 500 GSM", 1000, Decimal("12.50")),
    ("Stainless steel kitchen sinks", 300, Decimal("85.00")),
    ("Organic Arabica coffee beans (60kg bags)", 200, Decimal("410.00")),
    ("LED panel lights 40W", 1500, Decimal("9.75")),
    ("Basmati rice, 25kg sacks", 800, Decimal("38.00")),
]

_PORTS = [
    ("Nhava Sheva, India", "New York, USA"),
    ("Shanghai, China", "Rotterdam, Netherlands"),
    ("Hamburg, Germany", "Santos, Brazil"),
    ("Busan, South Korea", "Long Beach, USA"),
]


def _party(fake: Faker, country: str | None = None) -> Party:
    return Party(
        name=fake.company(),
        address=fake.street_address(),
        country=country or fake.country(),
    )


def build_compliant_case(seed: int) -> ShipmentCase:
    """Create a case where every document agrees and UCP 600 is satisfied."""
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)

    description, quantity, unit_price = rng.choice(_GOODS)
    pol, pod = rng.choice(_PORTS)
    currency = "USD"

    total = (unit_price * quantity).quantize(Decimal("0.01"))
    # LC amount is a round number at or above the invoice total, tolerance 5%.
    lc_amount = (total * Decimal("1.05")).quantize(Decimal("1"))

    issue = date(2026, 1, 10)
    latest_shipment = issue + timedelta(days=40)
    expiry = latest_shipment + timedelta(days=21)  # UCP: present within 21 days
    shipment = latest_shipment - timedelta(days=5)  # comfortably on time

    applicant = _party(fake, "USA")            # buyer
    beneficiary = _party(fake, "India")        # seller
    bank = Party(name="First Global Bank", address="1 Finance Plaza", country="USA")

    lc = LetterOfCredit(
        lc_number=f"LC-{seed:05d}",
        issue_date=issue,
        expiry_date=expiry,
        latest_shipment_date=latest_shipment,
        applicant=applicant,
        beneficiary=beneficiary,
        issuing_bank=bank,
        amount=Money(amount=lc_amount, currency=currency),
        tolerance_pct=Decimal("5"),
        goods_description=description,
        port_of_loading=pol,
        port_of_discharge=pod,
        incoterm=Incoterm.CIF,
        partial_shipment_allowed=False,
        transshipment_allowed=False,
    )

    invoice = CommercialInvoice(
        invoice_number=f"INV-{seed:05d}",
        invoice_date=shipment,
        lc_number=lc.lc_number,
        seller=beneficiary,
        buyer=applicant,
        goods_description=description,
        quantity=quantity,
        unit_price=Money(amount=unit_price, currency=currency),
        total_amount=Money(amount=total, currency=currency),
        incoterm=Incoterm.CIF,
    )

    bol = BillOfLading(
        bl_number=f"BL-{seed:05d}",
        shipment_date=shipment,
        shipper=beneficiary,
        consignee=applicant,
        port_of_loading=pol,
        port_of_discharge=pod,
        goods_description=description,
        number_of_packages=max(1, quantity // 50),
        clean_on_board=True,
        freight_prepaid=True,
    )

    return ShipmentCase(
        case_id=f"CASE-{seed:05d}",
        letter_of_credit=lc,
        commercial_invoice=invoice,
        bill_of_lading=bol,
        injected_discrepancies=[],
    )


# ---------------------------------------------------------------------------
# Mutators: each breaks the case in exactly one way.
# ---------------------------------------------------------------------------
def _inject_amount_over_lc(case: ShipmentCase) -> None:
    lc_amt = case.letter_of_credit.amount.amount
    # Push invoice total to 15% over the LC amount -> beyond the 5% tolerance.
    new_total = (lc_amt * Decimal("1.15")).quantize(Decimal("0.01"))
    inv = case.commercial_invoice
    inv.total_amount.amount = new_total
    inv.unit_price.amount = (new_total / inv.quantity).quantize(Decimal("0.01"))


def _inject_currency_mismatch(case: ShipmentCase) -> None:
    case.commercial_invoice.total_amount.currency = "EUR"
    case.commercial_invoice.unit_price.currency = "EUR"


def _inject_goods_description_mismatch(case: ShipmentCase) -> None:
    case.commercial_invoice.goods_description = "Assorted general merchandise"


def _inject_late_shipment(case: ShipmentCase) -> None:
    late = case.letter_of_credit.latest_shipment_date + timedelta(days=7)
    case.bill_of_lading.shipment_date = late


def _inject_port_mismatch(case: ShipmentCase) -> None:
    case.bill_of_lading.port_of_discharge = "Felixstowe, UK"


def _inject_beneficiary_name_mismatch(case: ShipmentCase) -> None:
    case.commercial_invoice.seller.name = case.commercial_invoice.seller.name + " International"


_MUTATORS = {
    Discrepancy.AMOUNT_OVER_LC: _inject_amount_over_lc,
    Discrepancy.CURRENCY_MISMATCH: _inject_currency_mismatch,
    Discrepancy.GOODS_DESCRIPTION_MISMATCH: _inject_goods_description_mismatch,
    Discrepancy.LATE_SHIPMENT: _inject_late_shipment,
    Discrepancy.PORT_MISMATCH: _inject_port_mismatch,
    Discrepancy.BENEFICIARY_NAME_MISMATCH: _inject_beneficiary_name_mismatch,
}


def build_case(seed: int, discrepancies: list[Discrepancy] | None = None) -> ShipmentCase:
    """Build a case and optionally inject one or more labelled discrepancies."""
    case = build_compliant_case(seed)
    for d in discrepancies or []:
        _MUTATORS[d](case)
        case.injected_discrepancies.append(d.value)
    return case
