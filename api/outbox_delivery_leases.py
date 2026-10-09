"""Lease committed outbox events; acknowledge only after explicit downstream success.

This repository layer never grants permissions to an event subscriber.
"""
from datetime import timedelta
from uuid import UUID,uuid4

def claim_events(db, *, limit:int=50, lease_seconds:int=60):
    if not 1<=limit<=200 or not 5<=lease_seconds<=600:
        raise ValueError("Invalid claim parameters")
    token=uuid4()
    rows=db.execute("""
       WITH due AS (
         SELECT id FROM cb.finance_outbox
         WHERE delivered_at IS NULL AND next_attempt_at<=now()
           AND (claimed_until IS NULL OR claimed_until<now())
         ORDER BY next_attempt_at,created_at,id
         FOR UPDATE SKIP LOCKED LIMIT %s
       )
       UPDATE cb.finance_outbox e
       SET claim_token=%s,claimed_until=now()+(%s * interval '1 second'),
           attempts=e.attempts+1
       FROM due WHERE e.id=due.id
       RETURNING e.id,e.company_id,e.event_type,e.aggregate_id,e.schema_version,e.payload,
                 e.attempts,e.claim_token
    """,(limit,token,lease_seconds)).fetchall()
    return rows

def acknowledge_event(db, *, event_id:UUID, claim_token:UUID)->bool:
    result=db.execute("""
       UPDATE cb.finance_outbox SET delivered_at=now(),claim_token=NULL,
            claimed_until=NULL,last_error=NULL
       WHERE id=%s AND claim_token=%s AND delivered_at IS NULL
         AND claimed_until>now() RETURNING id
    """,(event_id,claim_token)).fetchone()
    return result is not None

def retry_event(db, *, event_id:UUID,claim_token:UUID,attempts:int,error:str)->bool:
    if attempts<1 or len(error)>500:
        raise ValueError("Invalid retry evidence")
    delay_seconds=min(3600,5*(2**min(attempts-1,10)))
    return db.execute("""
       UPDATE cb.finance_outbox SET next_attempt_at=now()+(%s * interval '1 second'),
          claim_token=NULL,claimed_until=NULL,last_error=%s
       WHERE id=%s AND claim_token=%s AND delivered_at IS NULL
         AND claimed_until>now() RETURNING id
    """,(delay_seconds,error[:500],event_id,claim_token)).fetchone() is not None
