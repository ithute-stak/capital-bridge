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
    return render_approved_quotation_pdf(
        ApprovedQuotation(reference=invoice.reference, company_name=invoice.company_name,
            client_name=invoice.client_name, issued_on=invoice.issued_on,
            valid_until=invoice.due_on, currency=invoice.currency, lines=invoice.lines,
            tax_minor=invoice.tax_minor, status="approved"),
        approved_logo_path=approved_logo_path, document_kind="INVOICE",
    )
