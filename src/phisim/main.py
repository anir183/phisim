from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from phisim.analysis.routes import router as analysis_router
from phisim.console.routes import router as console_router
from phisim.infra.sqlite.connection import initialize_database
from phisim.scenarios.routes import router as scenario_router
from phisim.sessions.routes import router as session_router
from phisim.simulation.control import router as control_router
from phisim.simulation.routes import router as simulation_router
from phisim.telemetry.routes import router as telemetry_router
from phisim.utils.paths import STATIC_DIR


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="PhiSim",
    version="0.0.0",
    lifespan=lifespan,
)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _request: Request,
    _exception: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request payload."},
    )


app.include_router(scenario_router)
app.include_router(session_router)
app.include_router(analysis_router)
app.include_router(control_router)
app.include_router(simulation_router)
app.include_router(telemetry_router)
app.include_router(console_router)
