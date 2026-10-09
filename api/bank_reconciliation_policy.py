"""Conservative bank reconciliation eligibility. Never auto-match ambiguous records."""
from dataclasses import dataclass
from datetime import date

class BankMatchError(ValueError):
    pass

@dataclass(frozen=True)
class BankMatchEvidence:
    bank_amount_minor: int
    payment_amount_minor: int
    payment_status: str
    bank_currency: str
    payment_currency: str
    company_matches: bool
    payment_reference: str
    bank_description: str
    bank_date: date
    payment_date: date
    actor_role: str

def validate_bank_payment_match(data: BankMatchEvidence) -> None:
    if data.actor_role not in {"director", "accountant"}:
        raise BankMatchError("Only authorised finance staff may reconcile payments")
    if not data.company_matches:
        raise BankMatchError("Bank transaction and payment company mismatch")
    if data.payment_status != "verified":
        raise BankMatchError("Verified payment required")
    if data.bank_currency != "LSL" or data.payment_currency != "LSL":
        raise BankMatchError("Currency mismatch")
    if (type(data.bank_amount_minor) is not int or
        type(data.payment_amount_minor) is not int or
        data.bank_amount_minor <= 0 or
        data.bank_amount_minor != data.payment_amount_minor):
        raise BankMatchError("Bank amount does not equal payment amount")
    if not data.payment_reference.strip() or data.payment_reference.lower() not in data.bank_description.lower():
        raise BankMatchError("Bank evidence does not identify payment reference")
    if abs((data.bank_date - data.payment_date).days) > 14:
        raise BankMatchError("Bank and payment dates require manual investigation")
