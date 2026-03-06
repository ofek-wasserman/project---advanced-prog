from fastapi import APIRouter, Depends

from src.api.dependencies import get_fleet_manager
from src.api.schemas.stations import NearestStationResponse
from src.domain.exceptions import NotFoundError
from src.services.fleet_manager import FleetManager

router = APIRouter()


@router.get("/stations/nearest", response_model=NearestStationResponse)
async def nearest_station(
    lat: float,
    lon: float,
    fleet_manager: FleetManager = Depends(get_fleet_manager),
) -> NearestStationResponse:
    station = fleet_manager.nearest_station_with_available_vehicle((lat, lon))

    if station is None:
        raise NotFoundError("No station with available vehicle found.")

    return NearestStationResponse(
        station_id=station.container_id,
        lat=station.lat,
        lon=station.lon,
    )
