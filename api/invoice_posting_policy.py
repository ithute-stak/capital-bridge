"""Pure server-side invoice posting preflight, separate from issuance.

The posting service must validate these conditions within the same locked DB
transaction that creates and posts journal lines and marks an invoice issued.
"""
from dataclasses import dataclass

MAX_MINOR = 9223372036854775807

class InvoicePostingError(ValueError):
    pass

@dataclass(frozen=True)
class InvoicePostingDecision:
    amount_minor: int
    receivable_debit_minor: int
    revenue_credit_minor: int
    tax_credit_minor: int

def validate_invoice_posting(*, actor_role: str, invoice_status: str,
                             period_open: bool, date_in_period: bool,
                             line_count: int, subtotal_minor: int,
                             calculated_subtotal_minor: int, tax_minor: int,
                             receivable_account_active: bool,
                             revenue_account_active: bool,
                             tax_account_active: bool) -> InvoicePostingDecision:
    if actor_role not in {"director", "accountant"}:
        raise InvoicePostingError("Invoice issuance requires director or accountant")
    if invoice_status != "draft":
        raise InvoicePostingError("Only a draft invoice can be issued")
    if not period_open or not date_in_period:
        raise InvoicePostingError("Open accounting period required")
    if line_count < 1 or subtotal_minor <= 0 or subtotal_minor != calculated_subtotal_minor:
        raise InvoicePostingError("Invoice line totals must reconcile")
    if tax_minor < 0 or subtotal_minor > MAX_MINOR - tax_minor:
        raise InvoicePostingError("Invoice total is outside valid range")
    if not receivable_account_active or not revenue_account_active:
        raise InvoicePostingError("Active receivable and revenue accounts are required")
    if tax_minor and not tax_account_active:
        raise InvoicePostingError("Active tax liability account required")
    total = subtotal_minor + tax_minor
    if total != subtotal_minor + tax_minor or total <= 0:
        raise InvoicePostingError("Journal amounts must balance")
    return InvoicePostingDecision(
        amount_minor=total, receivable_debit_minor=total,
        revenue_credit_minor=subtotal_minor, tax_credit_minor=tax_minor,
    )
