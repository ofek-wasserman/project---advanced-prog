from src.api.schemas.base import StrictBaseModel

class StartRideRequest(StrictBaseModel):
    user_id: int
    station_id: int
    
class StartRideResponse(StrictBaseModel):
    ride_id: int
    vehicle_id: int
    start_station_id: int
    
class EndRideResponse(StrictBaseModel):
    ride_id: int
    end_station_id: int
    payment_charged_ils: int