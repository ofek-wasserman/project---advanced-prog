from src.api.schemas.base import StrictBaseModel


class StartRideRequest(StrictBaseModel):
    user_id: int
    lon: float
    lat: float


class StartRideResponse(StrictBaseModel):
    ride_id: int
    vehicle_id: str  # IMPORTANT: string per dataset
    vehicle_type: str  # REQUIRED by spec
    start_station_id: int


class EndRideRequest(StrictBaseModel):
    ride_id: int
    lon: float
    lat: float


class EndRideResponse(StrictBaseModel):
    ride_id: int
    end_station_id: int
    payment_charged: int  # rename from payment_charged_ils


class ActiveUsersResponse(StrictBaseModel):
    active_user_ids: list[int]
