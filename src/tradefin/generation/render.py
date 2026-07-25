"""
Render ShipmentCase objects to realistic PDF documents using ReportLab.

We render three separate PDFs per case (LC, Invoice, BoL) plus a
`ground_truth.json` holding the exact structured data and the list of injected
discrepancies. Downstream modules read the PDFs; evaluation reads the JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from tradefin.schemas import BillOfLading, CommercialInvoice, LetterOfCredit, ShipmentCase

_STYLES = getSampleStyleSheet()


def _title(text: str) -> Paragraph:
    return Paragraph(f"<b>{text}</b>", _STYLES["Title"])


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    """A two-column key/value table styled like a form."""
    data = [[Paragraph(f"<b>{k}</b>", _STYLES["Normal"]), Paragraph(v, _STYLES["Normal"])]
            for k, v in rows]
    table = Table(data, colWidths=[55 * mm, 110 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f3f7")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _party_str(p) -> str:
    return f"{p.name}<br/>{p.address}<br/>{p.country}"


def _build(path: Path, title: str, rows: list[tuple[str, str]]) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    story = [_title(title), Spacer(1, 8 * mm), _kv_table(rows)]
    doc.build(story)


def render_letter_of_credit(lc: LetterOfCredit, path: Path) -> None:
    rows = [
        ("Documentary Credit No.", lc.lc_number),
        ("Date of Issue", lc.issue_date.isoformat()),
        ("Date of Expiry", lc.expiry_date.isoformat()),
        ("Latest Date of Shipment", lc.latest_shipment_date.isoformat()),
        ("Applicant (Buyer)", _party_str(lc.applicant)),
        ("Beneficiary (Seller)", _party_str(lc.beneficiary)),
        ("Issuing Bank", _party_str(lc.issuing_bank)),
        ("Credit Amount", f"{lc.amount.currency} {lc.amount.amount:,.2f}"),
        ("Tolerance", f"+/- {lc.tolerance_pct}%"),
        ("Description of Goods", lc.goods_description),
        ("Port of Loading", lc.port_of_loading),
        ("Port of Discharge", lc.port_of_discharge),
        ("Incoterm", lc.incoterm.value),
        ("Partial Shipment", "ALLOWED" if lc.partial_shipment_allowed else "NOT ALLOWED"),
        ("Transshipment", "ALLOWED" if lc.transshipment_allowed else "NOT ALLOWED"),
    ]
    _build(path, "IRREVOCABLE DOCUMENTARY CREDIT", rows)


def render_commercial_invoice(inv: CommercialInvoice, path: Path) -> None:
    rows = [
        ("Invoice No.", inv.invoice_number),
        ("Invoice Date", inv.invoice_date.isoformat()),
        ("LC Reference", inv.lc_number),
        ("Seller", _party_str(inv.seller)),
        ("Buyer", _party_str(inv.buyer)),
        ("Description of Goods", inv.goods_description),
        ("Quantity", str(inv.quantity)),
        ("Unit Price", f"{inv.unit_price.currency} {inv.unit_price.amount:,.2f}"),
        ("Total Amount", f"{inv.total_amount.currency} {inv.total_amount.amount:,.2f}"),
        ("Incoterm", inv.incoterm.value),
    ]
    _build(path, "COMMERCIAL INVOICE", rows)


def render_bill_of_lading(bol: BillOfLading, path: Path) -> None:
    rows = [
        ("B/L No.", bol.bl_number),
        ("Shipment (On Board) Date", bol.shipment_date.isoformat()),
        ("Shipper", _party_str(bol.shipper)),
        ("Consignee", _party_str(bol.consignee)),
        ("Port of Loading", bol.port_of_loading),
        ("Port of Discharge", bol.port_of_discharge),
        ("Description of Goods", bol.goods_description),
        ("No. of Packages", str(bol.number_of_packages)),
        ("Shipped Clean On Board", "YES" if bol.clean_on_board else "NO"),
        ("Freight", "PREPAID" if bol.freight_prepaid else "COLLECT"),
    ]
    _build(path, "BILL OF LADING", rows)


def render_case(case: ShipmentCase, out_dir: Path) -> Path:
    """Render all three PDFs + ground_truth.json for one case into out_dir/case_id/."""
    case_dir = out_dir / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    render_letter_of_credit(case.letter_of_credit, case_dir / "letter_of_credit.pdf")
    render_commercial_invoice(case.commercial_invoice, case_dir / "commercial_invoice.pdf")
    render_bill_of_lading(case.bill_of_lading, case_dir / "bill_of_lading.pdf")

    # model_dump(mode="json") turns dates/Decimals into JSON-safe strings.
    (case_dir / "ground_truth.json").write_text(
        json.dumps(case.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return case_dir
