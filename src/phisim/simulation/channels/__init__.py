from phisim.simulation.channels.email import router as email_router
from phisim.simulation.channels.index import router as index_router
from phisim.simulation.channels.mfa import router as mfa_router
from phisim.simulation.channels.qr import router as qr_router
from phisim.simulation.channels.sms import router as sms_router
from phisim.simulation.channels.website import router as website_router

__all__ = [
    "email_router",
    "index_router",
    "mfa_router",
    "qr_router",
    "sms_router",
    "website_router",
]
