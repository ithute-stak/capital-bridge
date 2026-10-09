"""Insert versioned domain events inside the caller's existing PostgreSQL transaction.

No network publish occurs here. Rollback of the business write also rolls back the event.
"""
from uuid import UUID, uuid4
from psycopg.types.json import Jsonb

_ALLOWED={"invoice.issued","payment.posted","payment.allocated","bank.matched"}

def enqueue_finance_event(db, *, company_id:UUID, event_type:str, aggregate_id:UUID, payload:dict|None=None)->UUID:
    if event_type not in _ALLOWED:
        raise ValueError("Unsupported finance event type")
    if not isinstance(company_id,UUID) or not isinstance(aggregate_id,UUID):
        raise ValueError("Event company and aggregate must be UUIDs")
    if payload is None:
        payload={}
    if not isinstance(payload,dict):
        raise ValueError("Outbox payload must be an object")
    event_id=uuid4()
    db.execute("""INSERT INTO cb.finance_outbox
        (id,company_id,event_type,aggregate_id,schema_version,payload)
        VALUES (%s,%s,%s,%s,1,%s)""",
        (event_id,company_id,event_type,aggregate_id,Jsonb(payload)))
    return event_id
