"""Company-scoped WebSocket notifications, with revalidation before every send.

This process-local fanout is NOT connected to the authenticated Go delivery
ingress or a durable cross-instance event broker. No external publish route.
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
from api.realtime_fanout import RealtimeFanout
from api.realtime_durable_reader import read_company_notifications

router=APIRouter()
fanout=RealtimeFanout(queue_size=32)

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

async def revalidate(cookie:str,company_id:UUID,subject:UUID)->bool:
    try:
        return await asyncio.to_thread(check_subscription,cookie,company_id)==subject
    except (HTTPException,ValueError,RuntimeError,PermissionError,psycopg.Error):
        return False

def fetch_durable(cookie:str,company_id:UUID,subject:UUID,cursor):
    settings=LoginDatabaseSettings.from_environment()
    with authentication_connection(settings.sessions,purpose="sessions") as auth_db:
        current=resolve(auth_db,cookie)
    if current != subject:
        raise PermissionError("Session invalidated")
    _,_,_,dsn=config()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=False) as db:
        with db.transaction():
            validate_company(company_id,subject,db)
            return read_company_notifications(db,company_id=company_id,cursor=cursor)

async def websocket_session(ws:WebSocket,*,cookie:str,company_id:UUID,subject:UUID,
                            bus:RealtimeFanout=fanout)->None:
    queue=bus.subscribe(company_id)
    cursor=None
    try:
        for _ in range(12):
            try:
                notification=await asyncio.wait_for(queue.get(),timeout=5)
            except asyncio.TimeoutError:
                notification={"type":"heartbeat","company_id":str(company_id)}
            if not await revalidate(cookie,company_id,subject):
                await ws.close(code=1008)
                return
            try:
                durable,cursor=await asyncio.to_thread(fetch_durable,cookie,company_id,subject,cursor)
            except (HTTPException,ValueError,RuntimeError,PermissionError,psycopg.Error):
                await ws.close(code=1008)
                return
            for event in durable:
                if not await revalidate(cookie,company_id,subject):
                    await ws.close(code=1008)
                    return
                await ws.send_json(event)
            if notification.get("type") in ("heartbeat", "finance.changed"):
                await ws.send_json(notification)
    finally:
        bus.unsubscribe(company_id,queue)
    await ws.close(code=1000)

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
    await websocket_session(ws,cookie=cookie,company_id=company_id,subject=subject)
