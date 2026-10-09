"""Authenticated internal finance delivery payload signing (no secret in browser)."""
import hashlib
import hmac
import json

def canonical_delivery(event:dict)->bytes:
    required={"version","event_id","company_id","event_type","aggregate_id"}
    if set(event)!=required or event["version"]!=1:
        raise ValueError("Unsupported delivery envelope")
    if not all(isinstance(event[k],str) and event[k].strip() for k in required-{"version"}):
        raise ValueError("Event identifiers required")
    return json.dumps(event,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def sign_delivery(event:dict,*,key:bytes)->tuple[bytes,str]:
    if not isinstance(key,bytes) or len(key)<32:
        raise ValueError("Strong internal delivery key required")
    body=canonical_delivery(event)
    return body,hmac.new(key,body,hashlib.sha256).hexdigest()
