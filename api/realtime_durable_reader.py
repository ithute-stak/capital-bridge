"""Tenant-validated durable notification cursor reader for websocket invalidations.

Reads only after the caller has revalidated session and current membership
using the existing check_subscription security boundary.
"""
from uuid import UUID

def read_company_notifications(db, *, company_id:UUID, cursor:tuple|None=None, limit:int=50):
    if not isinstance(company_id,UUID) or not 1<=limit<=100:
        raise ValueError("Invalid notification company or page limit")
    if cursor is None:
        # Initial connection establishes a high-watermark: no historical
        # notification backlog leaks into a newly opened browser session.
        last=db.execute("""
            SELECT received_at,id FROM cb.realtime_notifications
            WHERE company_id=%s ORDER BY received_at DESC,id DESC LIMIT 1
        """,(company_id,)).fetchone()
        return [], (last["received_at"],last["id"]) if last else None
    rows=db.execute("""
        SELECT id,event_type,aggregate_id,received_at
        FROM cb.realtime_notifications
        WHERE company_id=%s AND (received_at,id)>(%s,%s)
        ORDER BY received_at,id LIMIT %s
    """,(company_id,cursor[0],cursor[1],limit)).fetchall()
    events=[{"version":1,"type":"finance.changed","company_id":str(company_id),
             "event_id":str(row["id"]),"event_type":row["event_type"],
             "aggregate_id":str(row["aggregate_id"])} for row in rows]
    next_cursor=(rows[-1]["received_at"],rows[-1]["id"]) if rows else cursor
    return events,next_cursor
