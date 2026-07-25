"""
Typed data models for the three trade-finance documents plus a bundling
"ShipmentCase".

WHY THIS FILE MATTERS
---------------------
These Pydantic models are the single source of truth for "what a document
contains". Every other layer speaks in these types:

  - the synthetic generator (Module 1) *produces* these objects, then renders
    them to PDF;
  - the extraction agent (Module 4) *reconstructs* these objects from a PDF via
    the LLM;
  - the compliance engine (Module 5) *compares* these objects to find
    discrepancies.

Because the same schema is used to generate AND to extract, we get a free,
exact "ground truth" to evaluate extraction accuracy against later.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Small shared value objects
# ---------------------------------------------------------------------------
class Party(BaseModel):
    """A company involved in the trade (buyer, seller, bank, carrier...)."""

    name: str
    address: str
    country: str


class Money(BaseModel):
    """An amount together with its currency.

    We use Decimal, not float, because money must be exact. 0.1 + 0.2 != 0.3
    in floating point, and rounding errors in financial software are a real bug
    class. Using Decimal here is exactly the kind of detail an interviewer
    likes to hear.
    """

    amount: Decimal
    currency: str = Field(description="ISO 4217 code, e.g. USD, EUR")


class Incoterm(str, Enum):
    """Standard international shipping terms (who pays freight/insurance)."""

    FOB = "FOB"   # Free On Board
    CIF = "CIF"   # Cost, Insurance and Freight
    CFR = "CFR"   # Cost and Freight
    EXW = "EXW"   # Ex Works


# ---------------------------------------------------------------------------
# The Letter of Credit — the "contract" every other document is checked against
# ---------------------------------------------------------------------------
class LetterOfCredit(BaseModel):
    lc_number: str
    issue_date: date
    expiry_date: date = Field(description="Docs presented after this are stale")
    latest_shipment_date: date = Field(description="Goods must ship on/before this")

    applicant: Party = Field(description="The buyer, who asked the bank to open the LC")
    beneficiary: Party = Field(description="The seller, who gets paid")
    issuing_bank: Party

    amount: Money
    # Tolerance: the LC amount may be exceeded/undershot by this percentage.
    # e.g. tolerance_pct=5 means an invoice up to 5% over the LC amount is OK.
    tolerance_pct: Decimal = Field(default=Decimal("0"))

    goods_description: str
    port_of_loading: str
    port_of_discharge: str
    incoterm: Incoterm

    partial_shipment_allowed: bool
    transshipment_allowed: bool


# ---------------------------------------------------------------------------
# The Commercial Invoice — issued by the seller
# ---------------------------------------------------------------------------
class CommercialInvoice(BaseModel):
    invoice_number: str
    invoice_date: date
    lc_number: str = Field(description="Which LC this invoice is presented under")

    seller: Party
    buyer: Party

    goods_description: str
    quantity: int
    unit_price: Money
    total_amount: Money
    incoterm: Incoterm


# ---------------------------------------------------------------------------
# The Bill of Lading — issued by the carrier
# ---------------------------------------------------------------------------
class BillOfLading(BaseModel):
    bl_number: str
    shipment_date: date = Field(description="Date goods were loaded / 'on board'")

    shipper: Party
    consignee: Party

    port_of_loading: str
    port_of_discharge: str
    goods_description: str
    number_of_packages: int
    clean_on_board: bool = Field(description="True = no damage noted at loading")
    freight_prepaid: bool


# ---------------------------------------------------------------------------
# A full case: one LC + the documents presented against it.
# ---------------------------------------------------------------------------
class ShipmentCase(BaseModel):
    """Bundles a single trade transaction and its ground-truth labels.

    `injected_discrepancies` records the discrepancy codes we deliberately
    planted (empty = a fully compliant case). The compliance engine never sees
    this field; we only use it in evaluation (Module 8) to score the system:
    'of the discrepancies we planted, how many did it catch?'.
    """

    case_id: str
    letter_of_credit: LetterOfCredit
    commercial_invoice: CommercialInvoice
    bill_of_lading: BillOfLading
    injected_discrepancies: list[str] = Field(default_factory=list)
