from fastapi import APIRouter

from phisim.simulation.capture_routes import router as capture_router
from phisim.simulation.channels import (
    email_router,
    index_router,
    mfa_router,
    qr_router,
    sms_router,
    victim_router,
    website_router,
)

router = APIRouter(tags=["simulation"])
router.include_router(index_router)
router.include_router(website_router)
router.include_router(email_router)
router.include_router(sms_router)
router.include_router(qr_router)
router.include_router(mfa_router)
router.include_router(victim_router)
router.include_router(capture_router)
