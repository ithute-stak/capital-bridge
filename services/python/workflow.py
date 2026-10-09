"""Python coordination boundary: validation only; no subprocess or finance writes."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FinanceEvent:
    company_id: str
    event_type: str
    aggregate_id: str

    def as_envelope(self) -> dict:
        if not all((self.company_id, self.event_type, self.aggregate_id)):
            raise ValueError("Complete event identity is required")
        return {"version": 1, "company_id": self.company_id,
                "event_type": self.event_type, "aggregate_id": self.aggregate_id}
