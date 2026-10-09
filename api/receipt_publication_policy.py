"""Official payment receipt publication eligibility, enforced on the backend."""
from dataclasses import dataclass

class ReceiptPublicationError(ValueError):
    pass

@dataclass(frozen=True)
class ReceiptEvidence:
    payment_minor: int
    receipt_minor: int
    payment_status: str
    journal_status: str
    journal_company_matches: bool
    payment_company_matches: bool
    actor_role: str

def validate_receipt_evidence(evidence: ReceiptEvidence) -> None:
    if evidence.actor_role not in {"director", "accountant"}:
        raise ReceiptPublicationError("Receipt issuance requires authorised finance staff")
    if not evidence.payment_company_matches or not evidence.journal_company_matches:
        raise ReceiptPublicationError("Receipt evidence company mismatch")
    if evidence.payment_status != "verified":
        raise ReceiptPublicationError("Only verified payments may be receipted")
    if evidence.journal_status != "posted":
        raise ReceiptPublicationError("Posted financial journal required")
    if (type(evidence.payment_minor) is not int or
        type(evidence.receipt_minor) is not int or
        evidence.payment_minor <= 0 or
        evidence.payment_minor != evidence.receipt_minor):
        raise ReceiptPublicationError("Receipt amount does not match the verified payment")
