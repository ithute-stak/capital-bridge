"""Fail-closed public consultation edge policy helpers.

These checks are designed for a future trusted gateway. They do not enable
anonymous POST requests or replace distributed edge rate limiting.
"""
from __future__ import annotations

from urllib.parse import urlsplit

MAX_BODY_BYTES = 8192
ALLOWED_ORIGIN = "https://capitalbridge.co.ls"
ALLOWED_CONTENT_TYPE = "application/json"


def validate_public_intake_headers(*, origin: str | None, content_type: str | None,
                                   content_length: int | None) -> None:
    """Reject missing/spoofable browser origin, unsupported type and oversized body.

    Only usable behind a trusted gateway that strips/rewrites incoming forwarded
    headers and applies its own per-IP and global budgets.
    """
    if origin != ALLOWED_ORIGIN:
        raise ValueError("Unapproved consultation origin")
    if not content_type or content_type.split(";", 1)[0].strip().lower() != ALLOWED_CONTENT_TYPE:
        raise ValueError("Unsupported consultation content type")
    if content_length is None or isinstance(content_length, bool) or not isinstance(content_length, int):
        raise ValueError("Content length required")
    if content_length < 1 or content_length > MAX_BODY_BYTES:
        raise ValueError("Consultation body is outside limits")
