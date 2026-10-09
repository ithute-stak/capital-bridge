"""Server-side quotation state machine; frontend cannot approve quotations.

This module only validates decisions. The API must separately verify a user
membership and persist the state change atomically before issuing documents.
"""
from __future__ import annotations
from dataclasses import dataclass

TRANSITIONS = {
    "draft": frozenset({"approved"}),
    "approved": frozenset({"sent"}),
    "sent": frozenset({"accepted", "rejected", "expired"}),
    "accepted": frozenset(),
    "rejected": frozenset(),
    "expired": frozenset(),
}
APPROVERS = frozenset({"director", "accountant"})
DISPATCHERS = frozenset({"director", "accountant", "finance_clerk"})


class QuotationTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class QuotationDecision:
    previous_status: str
    new_status: str
    actor_role: str


def validate_transition(previous: str, target: str, role: str, *, line_count: int,
                        subtotal_minor: int, calculated_minor: int,
                        issued_on_present: bool, valid_until_present: bool) -> QuotationDecision:
    if target not in TRANSITIONS.get(previous, ()):
        raise QuotationTransitionError("Quotation status transition not allowed")
    if target == "approved" and role not in APPROVERS:
        raise QuotationTransitionError("Only authorised approvers may approve quotations")
    if target == "sent" and role not in DISPATCHERS:
        raise QuotationTransitionError("Quotation dispatch not permitted")
    if target in {"accepted", "rejected", "expired"} and role not in APPROVERS:
        raise QuotationTransitionError("Decision requires an authorised approver")
    if line_count <= 0 or subtotal_minor < 0 or subtotal_minor != calculated_minor:
        raise QuotationTransitionError("Quotation financial amounts are not reconciled")
    if not issued_on_present or not valid_until_present:
        raise QuotationTransitionError("Quotation document dates are required")
    return QuotationDecision(previous, target, role)
