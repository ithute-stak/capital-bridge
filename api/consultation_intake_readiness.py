"""Public intake rollout state, derived only from backend operator configuration."""
from fastapi import APIRouter
from api.consultation_public import intake_enabled, intake_dependencies
from api.consultation_tenant import consultation_company_id

router = APIRouter(tags=["consultation-intake"])

@router.get("/api/v1/consultations/intake/readiness")
def consultation_intake_readiness():
    available = False
    if intake_enabled():
        try:
            intake_dependencies()
            consultation_company_id()
            available = True
        except RuntimeError:
            pass
    return {
        "online_submission_available": available,
        "status": "available" if available else "security_and_delivery_review_required",
        "delivery_method": "online" if available else "user_reviewed_email",
        "message": ("Online consultation submission is configured."
                    if available else
                    "Online consultation submission is not available; use the prepared email form."),
    }
