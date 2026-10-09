"""Company-authorised polling of durable finance invalidations.

The journal is not yet populated by Go ingress; the next integration must write
it atomically with the authenticated inbound event receipt.
"""
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter,Depends,HTTPException,Query
from api.main import authenticate,config,validate_company

router=APIRouter(prefix="/api/v1/companies/{company_id}/realtime",tags=["realtime"])

@router.get("/notifications")
def notifications(company_id:UUID,after_id:UUID|None=None,limit:int=Query(50,ge=1,le=100),
                  user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            if after_id is not None:
                cursor=db.execute(
                    "SELECT received_at,id FROM cb.realtime_notifications WHERE company_id=%s AND id=%s",
                    (company_id,after_id)).fetchone()
                if cursor is None:
                    raise HTTPException(400,"Invalid notification cursor")
                rows=db.execute("""
                    SELECT id,event_type,aggregate_id,received_at
                    FROM cb.realtime_notifications
                    WHERE company_id=%s AND (received_at,id)>(%s,%s)
                    ORDER BY received_at,id LIMIT %s
                """,(company_id,cursor["received_at"],cursor["id"],limit)).fetchall()
            else:
                rows=db.execute("""
                    SELECT id,event_type,aggregate_id,received_at
                    FROM cb.realtime_notifications WHERE company_id=%s
                    ORDER BY received_at DESC,id DESC LIMIT %s
                """,(company_id,limit)).fetchall()
                rows=list(reversed(rows))
    return {"company_id":str(company_id),"notifications":[{
        "id":str(x["id"]),"event_type":x["event_type"],
        "aggregate_id":str(x["aggregate_id"]),"received_at":x["received_at"].isoformat()
    } for x in rows],"next_cursor":str(rows[-1]["id"]) if rows else str(after_id) if after_id else None}
