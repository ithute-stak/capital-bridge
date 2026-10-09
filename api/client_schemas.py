"""Validated CRM creation payload. Authorization occurs server-side, not here."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ClientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_code: str = Field(min_length=1, max_length=40)
    legal_name: str = Field(min_length=1, max_length=250)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("client_code", "legal_name")
    @classmethod
    def clean_required(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError("Required client text cannot be empty or contain controls")
        return value

    @field_validator("email", "phone")
    @classmethod
    def clean_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if any(ord(c) < 32 for c in value):
            raise ValueError("Control characters prohibited")
        if value.count("@") != 1 and "@" in value:
            raise ValueError("Invalid email")
        return value
