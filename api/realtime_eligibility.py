"""Read-only subscription eligibility inspection using verified Ithute identity.

This route does not open a WebSocket or mint a reusable subscription ticket.
The eventual WebSocket handshake must revalidate the current membership itself.
"""
from uuid import UUID
import psycopg
from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

from api.main import authenticate, config, validate_company
from api.realtime_subscription_policy import SubscriberIdentity, authorize_subscription

router = APIRouter(prefix="/api/v1/companies/{company_id}/realtime",tags=["realtime"])

@router.get("/eligibility")
def subscription_eligibility(company_id:UUID,user_id:UUID=Depends(authenticate)):
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,user_id,db)
            authorize_subscription(
                SubscriberIdentity(user_id=user_id,company_id=company_id,
                                   token_active=True,membership_active=True),
                company_id)
    return {"company_id":str(company_id),"eligible":True,"websocket_enabled":False}
