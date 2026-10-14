"""Atomic Redis-backed sliding window limiter for future public consultation intake.

Must run behind a trusted edge that provides a validated client IP. No public
submission route uses this yet. Redis unavailability fails closed.
"""
from __future__ import annotations

import hashlib
import ipaddress
import os

WINDOW_SECONDS = 600
MAX_REQUESTS = 5
# Redis transaction atomicity prevents parallel workers exceeding the budget.
LUA_LIMIT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


class IntakeRateLimitError(Exception):
    """Unable to establish a safe rate-limit decision."""


def private_ip_key(ip_text: str, *, secret: str) -> str:
    """Hash only a validated IP; never expose raw addresses in Redis keys."""
    if not secret or len(secret) < 32:
        raise IntakeRateLimitError("Rate limit secret is not configured")
    try:
        address = ipaddress.ip_address(ip_text)
    except ValueError as exc:
        raise IntakeRateLimitError("Trusted client IP is invalid") from exc
    digest = hashlib.sha256((secret + ":" + address.compressed).encode()).hexdigest()
    return "cb:intake:rl:v1:" + digest


def allow_intake_request(redis_client, *, trusted_client_ip: str, secret: str) -> bool:
    """Consume one quota atomically; on Redis error deny, never bypass limiter."""
    key = private_ip_key(trusted_client_ip, secret=secret)
    try:
        count = redis_client.eval(LUA_LIMIT, 1, key, WINDOW_SECONDS)
        count = int(count)
    except (Exception,) as exc:
        raise IntakeRateLimitError("Consultation rate limiter unavailable") from exc
    if count < 1:
        raise IntakeRateLimitError("Invalid limiter response")
    return count <= MAX_REQUESTS
