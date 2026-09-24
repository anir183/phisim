from fastapi import APIRouter, FastAPI

router = APIRouter()


@router.get("/check")
async def check():
    return {"status": "ok"}


app = FastAPI(
    title="PhiSim",
    version="0.0.0",
)

app.include_router(router)
