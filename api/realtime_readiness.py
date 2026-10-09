"""Fail-closed realtime deployment prerequisites; never expose secrets."""
import os
from urllib.parse import urlparse

def readiness(env=None):
    env=os.environ if env is None else env
    missing=[]
    origin=env.get("CB_PUBLIC_ORIGIN","")
    if not origin.startswith("https://") or urlparse(origin).path not in ("","/"):
        missing.append("secure_public_origin")
    if not env.get("CB_DATABASE_URL"):
        missing.append("database_connection")
    if not env.get("CB_SESSION_DATABASE_URL"):
        missing.append("session_database_connection")
    go_url=env.get("CB_GO_DELIVERY_URL","")
    if not go_url.startswith("https://") or not urlparse(go_url).hostname:
        missing.append("secure_go_delivery_endpoint")
    if len(env.get("CB_GO_DELIVERY_HMAC_KEY","").encode())<32:
        missing.append("delivery_hmac_key")
    if env.get("CB_REALTIME_WORKERS_ENABLED")!="true":
        missing.append("delivery_workers_not_enabled")
    if env.get("CB_REALTIME_RUNTIME_VERIFIED")!="true":
        missing.append("end_to_end_runtime_not_verified")
    return {"ready":not missing,"missing":missing}
