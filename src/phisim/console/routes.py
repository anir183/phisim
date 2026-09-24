from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from phisim.utils.paths import TEMPLATES_DIR

templates = Jinja2Templates(
    directory=TEMPLATES_DIR,
)


router = APIRouter(
    prefix="/console",
    tags=["console"],
)


@router.get("", response_class=HTMLResponse)
async def console(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="console.html",
    )
