"""Best-effort tenant change hints; clients always re-fetch authorised rows."""
from __future__ import annotations
import os
from uuid import UUID
import redis

def consultation_channel(company_id: UUID) -> str:
    return "cb:consultations:" + str(company_id)

def publish_consultation_change(company_id: UUID) -> bool:
    url=os.environ.get("CB_CONSULTATION_REDIS_URL","")
    if not url:
        return False
    try:
        client=redis.Redis.from_url(url,socket_connect_timeout=2,socket_timeout=2)
        try:
            client.publish(consultation_channel(company_id),"changed")
        finally:
            client.close()
        return True
    except (redis.RedisError,ValueError,OSError):
        return False
