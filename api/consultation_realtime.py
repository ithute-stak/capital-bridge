"""Cookie-authenticated, tenant-scoped Redis WebSocket change hints.

No record details are sent. Each change causes an authorised re-fetch.
OIDC session issuance and Redis deployment remain independently gated.
"""
from __future__ import annotations

import asyncio
import os
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from redis.exceptions import RedisError

from api.sessions import SESSION_COOKIE, check_same_origin
from api.realtime_websocket import check_subscription
from api.consultation_events import consultation_channel

router=APIRouter()

@router.websocket("/api/v1/staff/consultations/companies/{company_id}/events")
async def staff_consultation_events(ws: WebSocket, company_id: UUID):
    origin=ws.headers.get("origin")
    if (os.environ.get("CB_PUBLIC_ORIGIN")!="https://capitalbridge.co.ls"
        or not check_same_origin(origin,"https://capitalbridge.co.ls")):
        await ws.close(code=1008)
        return
    cookie=ws.cookies.get(SESSION_COOKIE)
    if not cookie:
        await ws.close(code=1008)
        return
    try:
        subject=await asyncio.to_thread(check_subscription,cookie,company_id)
    except Exception:
        await ws.close(code=1008)
        return
    redis_url=os.environ.get("CB_CONSULTATION_REDIS_URL","")
    if not redis_url:
        await ws.close(code=1013)
        return
    client=Redis.from_url(redis_url,socket_connect_timeout=2,socket_timeout=5)
    try:
        async with client.pubsub() as subscription:
            await subscription.subscribe(consultation_channel(company_id))
            await ws.accept()
            while True:
                try:
                    validated=await asyncio.to_thread(check_subscription,cookie,company_id)
                    if validated!=subject:
                        await ws.close(code=1008)
                        break
                    event=await subscription.get_message(ignore_subscribe_messages=True,timeout=10)
                    if event and event.get("data")==b"changed":
                        await ws.send_json({"type":"changed"})
                    else:
                        await ws.send_json({"type":"heartbeat"})
                except WebSocketDisconnect:
                    break
    except (RedisError,RuntimeError,OSError):
        await ws.close(code=1011)
    finally:
        await client.aclose()
