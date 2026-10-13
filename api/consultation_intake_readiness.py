"""Public consultation intake rollout status.

The public website currently prepares a mailto: message, not a stored submission.
Never infer readiness from arbitrary env vars or client-controlled flags.
"""
from fastapi import APIRouter

router = APIRouter(tags=["consultation-intake"])


@router.get("/api/v1/consultations/intake/readiness")
def consultation_intake_readiness():
    """Fail closed until anti-abuse and secure tenant-write infrastructure ship."""
    return {
        "online_submission_available": False,
        "status": "security_and_delivery_review_required",
        "delivery_method": "user_reviewed_email",
        "message": "Online consultation submission is not available; use the prepared email form.",
    }
