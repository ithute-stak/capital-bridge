"""Official invoice PDF generation on Python backend only.

Reuse the checked A4 rendering implementation and logo publication gate.
"""
from dataclasses import dataclass
from pathlib import Path
from api.quotation_pdf import ApprovedQuotation, QuotationLine, render_approved_quotation_pdf


@dataclass(frozen=True)
class IssuedInvoice:
    reference: str
    company_name: str
    client_name: str
    issued_on: str
    due_on: str
    currency: str
    status: str
    lines: tuple[QuotationLine, ...]
    subtotal_minor: int
    tax_minor: int


def render_issued_invoice_pdf(invoice: IssuedInvoice, *, approved_logo_path: Path) -> bytes:
    if invoice.status not in {"issued", "part_paid", "paid"}:
        raise ValueError("Only issued invoices can be published")
    calculated = sum(item.quantity * item.unit_price_minor for item in invoice.lines)
    if not invoice.lines or calculated != invoice.subtotal_minor:
        raise ValueError("Invoice subtotal differs from its immutable line items")
    # Use the same audited A4 template until the dedicated invoice template
    # undergoes visual sign-off. Do not mislabel this as an official invoice.
    raise RuntimeError("Dedicated invoice PDF visual template approval required")
