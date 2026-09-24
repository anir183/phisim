from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["simulation"])


@router.get("/simulation", include_in_schema=False)
async def simulation_index() -> RedirectResponse:
    return RedirectResponse("/lab", status_code=307)
