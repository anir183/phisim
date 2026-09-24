from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from phisim.infra.sqlite.connection import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


router = APIRouter()


@router.get("/check")
async def check():
    return {"status": "ok"}


app = FastAPI(
    title="PhiSim",
    version="0.0.0",
    lifespan=lifespan,
)

app.include_router(router)
