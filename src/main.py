from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.router import api_router
from src.bootstrap import build_fleet_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.fleet_manager = build_fleet_manager(
        stations_csv=Path("data/stations.csv"),
        vehicles_csv=Path("data/vehicles.csv"),
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vehicle Sharing API",
        description="API for managing vehicle sharing services",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(api_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    return app


app = create_app()
