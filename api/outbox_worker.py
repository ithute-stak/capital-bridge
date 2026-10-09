"""Finance outbox delivery runner.

The worker requires an authenticated downstream delivery adapter supplied by
deployment wiring. No endpoint, transport secret, or subscriber credentials
are hard-coded into this module. Outbox DB access requires a reviewed dedicated
least-privilege role with explicit access to the queued companies.
"""
from __future__ import annotations

import logging
from collections.abc import Callable

from api.outbox_delivery_leases import claim_events, acknowledge_event, retry_event

log = logging.getLogger(__name__)


def deliver_batch(connection_factory: Callable, deliver: Callable[[dict], bool],
                  *, limit: int = 50) -> dict[str, int]:
    """Claim in a committed transaction, deliver, then acknowledge or retry.

    A successful downstream response MUST mean durable, idempotent acceptance,
    not merely TCP connection success. At-least-once delivery is expected.
    """
    if not 1 <= limit <= 200:
        raise ValueError("Invalid delivery batch size")
    with connection_factory() as db:
        with db.transaction():
            rows = claim_events(db, limit=limit)
    outcome = {"claimed": len(rows), "acknowledged": 0, "retried": 0, "lost_lease": 0}
    for row in rows:
        event = {
            "version": row["schema_version"],
            "event_id": str(row["id"]),
            "company_id": str(row["company_id"]),
            "event_type": row["event_type"],
            "aggregate_id": str(row["aggregate_id"]),
        }
        error = ""
        try:
            if deliver(event) is not True:
                error = "Downstream did not acknowledge"
        except Exception as exc:
            # Do not include exception detail; it might contain tokens or private data.
            log.warning("Event delivery failed for event %s: %s", event["event_id"], type(exc).__name__)
            error = "Downstream delivery raised an error"
        with connection_factory() as db:
            with db.transaction():
                if not error:
                    updated = acknowledge_event(db, event_id=row["id"], claim_token=row["claim_token"])
                    name = "acknowledged" if updated else "lost_lease"
                else:
                    updated = retry_event(db, event_id=row["id"], claim_token=row["claim_token"],
                                          attempts=row["attempts"], error=error)
                    name = "retried" if updated else "lost_lease"
        outcome[name] += 1
    return outcome
