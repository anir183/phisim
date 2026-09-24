from contextlib import asynccontextmanager

from fastapi import FastAPI

from phisim.console.routes import router as console_router
from phisim.infra.sqlite.connection import initialize_database
from phisim.scenarios.routes import router as scenario_router
from phisim.sessions.routes import router as session_router
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

app.include_router(scenario_router)
app.include_router(session_router)
app.include_router(telemetry_router)
app.include_router(console_router)
