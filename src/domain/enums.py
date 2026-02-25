from enum import Enum


class VehicleStatus(Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"




class VehicleLocation(Enum):
    DOCKED = "docked"
    IN_RIDE = "in_ride"
    IN_REPO = "in_repo"
