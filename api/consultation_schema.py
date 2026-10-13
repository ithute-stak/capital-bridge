"""Validated public consultation intake contract.

No unauthenticated submission route is enabled here. Production must provide
rate limiting, bot resistance, explicit tenant assignment and restricted database
privileges before public ingestion is activated.
"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ConsultationService(str, Enum):
    MANAGEMENT = "Management & Business Consultancy"
    TECHNOLOGY = "Information Technology"
    ENGINEERING = "Engineering & Technical Advisory"
    TRAINING = "Training & Capacity Building"
    SUPPORT = "Business Support & Events"
    MOBILITY = "Immigration & Global Mobility"


class ConsultationEnquiry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    service: ConsultationService
    message: str = Field(min_length=10, max_length=2000)
    consent: bool

    @field_validator("consent")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Enquiry consent required")
        return value

    @field_validator("message")
    @classmethod
    def avoid_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 and char not in "\n\t\r" for char in value):
            raise ValueError("Unexpected control character")
        return value
