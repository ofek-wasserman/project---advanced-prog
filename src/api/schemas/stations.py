from src.api.schemas.base import StrictBaseModel


class NearestStationResponse(StrictBaseModel):
    station_id: int
    lat: float
    lon: float


class ActiveUserResponse(StrictBaseModel):
    user_id: list[int]
