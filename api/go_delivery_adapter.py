"""Signed internal POST adapter for finance outbox delivery.

Transport must be HTTPS; Go response 202 means durable acceptance and 200
means the event was already durably accepted (idempotent replay).
"""
import hashlib
import hmac
import time
from urllib.parse import urlparse
import httpx
from api.go_delivery_auth import canonical_delivery

def send_to_go(event:dict, *, url:str, key:bytes, client:httpx.Client, clock=time.time)->bool:
    target=urlparse(url)
    if target.scheme!="https" or not target.hostname or target.username or target.password:
        raise ValueError("Internal delivery requires trusted HTTPS target")
    if not isinstance(key,bytes) or len(key)<32:
        raise ValueError("Strong internal delivery key required")
    body=canonical_delivery(event)
    timestamp=str(int(clock()))
    signature=hmac.new(key,timestamp.encode()+b"."+body,hashlib.sha256).hexdigest()
    response=client.post(url,content=body,headers={
        "Content-Type":"application/json","X-CB-Timestamp":timestamp,
        "X-CB-Signature":signature},timeout=5.0)
    return response.status_code in (200,202)
