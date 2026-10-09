"""Constrained client edits; immutable company ID and client code."""
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ClientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    legal_name: str = Field(min_length=1, max_length=250)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    status: str = Field(default="active", pattern=r"^(active|inactive)$")

    @field_validator("legal_name")
    @classmethod
    def name_required(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(ch) < 32 for ch in value):
            raise ValueError("Client name is required")
        return value

    @field_validator("email", "phone")
    @classmethod
    def clean_contact(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if any(ord(ch) < 32 for ch in value):
            raise ValueError("Control characters are not permitted")
        return value or None
