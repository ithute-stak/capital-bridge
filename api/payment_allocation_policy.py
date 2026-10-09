"""Backend payment allocation arithmetic: never trust browser invoice balances."""
MAX_MINOR = 9223372036854775807

class AllocationError(ValueError):
    pass

def validate_allocation(*, payment_status: str, payment_minor: int,
                        previously_allocated_minor: int, proposed_minor: int,
                        invoice_status: str, invoice_total_minor: int,
                        invoice_allocated_minor: int, same_company: bool,
                        same_client: bool) -> tuple[int, int]:
    if not same_company or not same_client:
        raise AllocationError("Payment and invoice ownership mismatch")
    if payment_status != "verified":
        raise AllocationError("Only verified payments may be allocated")
    if invoice_status not in {"issued", "part_paid"}:
        raise AllocationError("Invoice is not eligible for allocation")
    values=(payment_minor, previously_allocated_minor, proposed_minor,
            invoice_total_minor, invoice_allocated_minor)
    if any(type(x) is not int or x < 0 or x > MAX_MINOR for x in values) or proposed_minor == 0:
        raise AllocationError("Invalid payment amount")
    remaining_payment = payment_minor - previously_allocated_minor
    remaining_invoice = invoice_total_minor - invoice_allocated_minor
    if remaining_payment < proposed_minor or remaining_invoice < proposed_minor:
        raise AllocationError("Allocation exceeds an available balance")
    return remaining_payment - proposed_minor, remaining_invoice - proposed_minor
