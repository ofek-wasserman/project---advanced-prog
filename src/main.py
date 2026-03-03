from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.router import api_router
from src.data.loaders import StationDataLoader, VehicleDataLoader
from src.services.fleet_manager import FleetManager


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vehicle Sharing API",
        description="API for managing vehicle sharing services",
        version="1.0.0",
    )

    # -----------------------------
    # Bootstrap: load initial state
    # -----------------------------
    stations_path = Path("data/stations.csv")
    vehicles_path = Path("data/vehicles.csv")

    stations = StationDataLoader(stations_path).create_objects()
    vehicles = VehicleDataLoader(vehicles_path).create_objects()

    # Single FleetManager instance for the whole app lifetime
    app.state.fleet_manager = FleetManager(stations=stations, vehicles=vehicles)

    # Routes
    app.include_router(api_router)

    # Map FastAPI validation errors (default 422) to 400
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    return app


app = create_app()