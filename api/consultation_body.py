"""Bounded byte-stream reader for a future consultation intake handler.

Never call request.body() before these bounds. Use the ASGI receive stream,
and refuse both oversized chunks and incomplete declared payloads.
"""
from __future__ import annotations

from collections.abc import AsyncIterable

from api.consultation_abuse_guard import MAX_BODY_BYTES


class IntakeBodyError(ValueError):
    pass


async def read_bounded_intake_body(
    chunks: AsyncIterable[bytes], *, declared_length: int | None = None
) -> bytes:
    if declared_length is not None and (
        isinstance(declared_length, bool) or not isinstance(declared_length, int)
        or declared_length < 0 or declared_length > MAX_BODY_BYTES
    ):
        raise IntakeBodyError("Invalid or excessive declared payload length")
    body = bytearray()
    async for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise IntakeBodyError("Invalid request chunk type")
        if len(chunk) > MAX_BODY_BYTES - len(body):
            raise IntakeBodyError("Consultation payload exceeds allowed size")
        body.extend(chunk)
    if declared_length is not None and len(body) != declared_length:
        raise IntakeBodyError("Request length mismatch")
    if not body:
        raise IntakeBodyError("Consultation body is empty")
    return bytes(body)
