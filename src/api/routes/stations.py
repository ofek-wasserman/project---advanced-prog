from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.stations import NearestStationResponse

router = APIRouter()

@router.get("/stations/nearest", response_model=NearestStationResponse)
async def nearest_station(
    lon: float = Query(...),
    lat: float = Query(...)
) -> NearestStationResponse:
    raise HTTPException(status_code=501, detail="Not implemented yet")
