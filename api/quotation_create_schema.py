"""Validated, overflow-safe quotation creation payloads."""
from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_MINOR = 9_223_372_036_854_775_807

class QuotationItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(ge=1, le=100000)
    unit_price_minor: int = Field(ge=0, le=10**12)

class QuotationCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: UUID
    quotation_number: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=1, max_length=250)
    issued_on: date
    valid_until: date
    lines: list[QuotationItemInput] = Field(min_length=1, max_length=100)
    @model_validator(mode="after")
    def validate_amounts(self):
        if self.valid_until < self.issued_on:
            raise ValueError("Quotation expiry cannot predate issue")
        if not self.quotation_number.strip() or not self.title.strip():
            raise ValueError("Quotation identity fields are mandatory")
        if any(not line.description.strip() for line in self.lines):
            raise ValueError("Quotation items require descriptions")
        if sum(item.quantity * item.unit_price_minor for item in self.lines) > MAX_MINOR:
            raise ValueError("Total exceeds supported integer precision")
        return self
    @property
    def subtotal_minor(self) -> int:
        return sum(line.quantity * line.unit_price_minor for line in self.lines)
