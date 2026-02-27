from src.domain.enums import VehicleLocation, VehicleStatus


def test_vehicle_location_docked():
    assert VehicleLocation.DOCKED.value == "docked"


def test_vehicle_location_in_ride():
    assert VehicleLocation.IN_RIDE.value == "in_ride"


def test_vehicle_location_in_repo():
    assert VehicleLocation.IN_REPO.value == "in_repo"


def test_vehicle_status_available():
    assert VehicleStatus.AVAILABLE.value == "available"


def test_vehicle_status_degraded():
    assert VehicleStatus.DEGRADED.value == "degraded"
