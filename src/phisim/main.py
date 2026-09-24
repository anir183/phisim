from contextlib import asynccontextmanager

from fastapi import FastAPI

from phisim.infra.sqlite.connection import initialize_database
from phisim.telemetry.routes import router as telemetry_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="PhiSim",
    version="0.0.0",
    lifespan=lifespan,
)

app.include_router(telemetry_router)
