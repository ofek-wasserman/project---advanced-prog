from src.domain.enums import VehicleLocation, VehicleStatus

def test_vehicle_status_enum():
    assert VehicleStatus.AVAILABLE.value == "available"
    assert VehicleStatus.DEGRADED.value == "degraded"

def test_vehicle_location_enum():
    assert VehicleLocation.DOCKED.value == "docked"
    assert VehicleLocation.IN_RIDE.value == "in_ride"
    assert VehicleLocation.IN_REPO.value == "in_repo"