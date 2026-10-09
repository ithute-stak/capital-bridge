"""Guarded WebSocket lifecycle with repeated server-side authorization.

This is a heartbeat-only endpoint: it does not subscribe to or broadcast
finance events. Session and membership are revalidated every heartbeat.
"""
import asyncio
import os
from uuid import UUID
import psycopg
from fastapi import APIRouter, WebSocket, HTTPException
from psycopg.rows import dict_row
from api.main import config, validate_company
from api.sessions import check_same_origin
from api.session_store import resolve
from api.login_db import LoginDatabaseSettings, authentication_connection
from api.realtime_subscription_policy import SubscriberIdentity, authorize_subscription

router=APIRouter()

def check_subscription(cookie:str,company_id:UUID)->UUID:
    settings=LoginDatabaseSettings.from_environment()
    with authentication_connection(settings.sessions,purpose="sessions") as auth_db:
        subject=resolve(auth_db,cookie)
    if not isinstance(subject,UUID):
        raise PermissionError("Session no longer active")
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,subject,db)
            authorize_subscription(SubscriberIdentity(subject,company_id,True,True),company_id)
    return subject

@router.websocket("/api/v1/companies/{company_id}/realtime/ws")
async def company_websocket(ws:WebSocket,company_id:UUID):
    expected=os.environ.get("CB_PUBLIC_ORIGIN","")
    if not expected or not check_same_origin(ws.headers.get("origin"),expected):
        await ws.close(code=1008)
        return
    cookie=ws.cookies.get("cb_session")
    if not cookie:
        await ws.close(code=1008)
        return
    try:
        subject=await asyncio.to_thread(check_subscription,cookie,company_id)
    except (HTTPException,ValueError,RuntimeError,PermissionError,psycopg.Error):
        await ws.close(code=1008)
        return
    await ws.accept()
    # A bounded heartbeat ensures revoked sessions and membership cannot
    # remain authorised indefinitely. No incoming instructions are processed.
    for _ in range(12):
        await asyncio.sleep(5)
        try:
            current=await asyncio.to_thread(check_subscription,cookie,company_id)
            if current!=subject:
                break
        except (HTTPException,ValueError,RuntimeError,PermissionError,psycopg.Error):
            break
        await ws.send_json({"type":"heartbeat","company_id":str(company_id)})
    await ws.close(code=1000)
