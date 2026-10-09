"""Fail-closed realtime WebSocket handshake, with independent identity checks.

Browser bearer tokens must be sent via a same-origin authenticated bootstrap in
a future release; URLs and query parameters never carry access tokens.
No business events are broadcast in this phase.
"""
import os
from uuid import UUID
import psycopg
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from psycopg.rows import dict_row
from api.main import config, validate_company
from api.sessions import check_same_origin
from api.session_store import resolve
from api.login_db import LoginDatabaseSettings, authentication_connection
from api.realtime_subscription_policy import SubscriberIdentity, authorize_subscription

router=APIRouter()

@router.websocket("/api/v1/companies/{company_id}/realtime/ws")
async def company_websocket(ws:WebSocket,company_id:UUID):
    expected=os.environ.get("CB_PUBLIC_ORIGIN","")
    if not expected or not check_same_origin(ws.headers.get("origin"),expected):
        await ws.close(code=1008)
        return
    # A real server-managed signed-in session is required; never trust a user_id header.
    cookie=ws.cookies.get("cb_session")
    if not cookie:
        await ws.close(code=1008)
        return
    try:
        settings=LoginDatabaseSettings.from_environment()
        with authentication_connection(settings.sessions,purpose="sessions") as auth_db:
            subject=resolve(auth_db,cookie)
        if not isinstance(subject,UUID):
            await ws.close(code=1008)
            return
        _,_,_,dsn=config()
        with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
            with db.transaction():
                validate_company(company_id,subject,db)
                authorize_subscription(SubscriberIdentity(subject,company_id,True,True),company_id)
    except (HTTPException,ValueError,RuntimeError,psycopg.Error):
        await ws.close(code=1008)
        return
    await ws.accept()
    # No events are sent. The connection is closed immediately until a secure
    # active subscription lifecycle and delivery broker are implemented.
    await ws.close(code=1000)
