"""Tests for active rides registry"""

from src.services.active_rides import ActiveRidesRegistry


class TestActiveRides:

    def test_create_ride(self):
        reg = ActiveRidesRegistry()
        ride_id = reg.create_ride(user_id=1, vehicle_id="V001", start_station_id=10)
        assert ride_id == 1
        ride = reg.get_ride(ride_id)
        assert ride["user_id"] == 1
        assert ride["vehicle_id"] == "V001"

    def test_user_has_active_ride(self):
        reg = ActiveRidesRegistry()
        reg.create_ride(user_id=1, vehicle_id="V001", start_station_id=10)
        assert reg.user_has_active_ride(1) is True
        assert reg.user_has_active_ride(2) is False

    def test_vehicle_in_use(self):
        reg = ActiveRidesRegistry()
        reg.create_ride(user_id=1, vehicle_id="V001", start_station_id=10)
        assert reg.vehicle_in_use("V001") is True
        assert reg.vehicle_in_use("V002") is False

    def test_end_ride_removes_tracking(self):
        reg = ActiveRidesRegistry()
        ride_id = reg.create_ride(user_id=1, vehicle_id="V001", start_station_id=10)
        reg.end_ride(ride_id)
        assert reg.user_has_active_ride(1) is False
        assert reg.vehicle_in_use("V001") is False

    def test_get_user_active_ride(self):
        reg = ActiveRidesRegistry()
        ride_id = reg.create_ride(user_id=1, vehicle_id="V001", start_station_id=10)
        ride = reg.get_user_active_ride(1)
        assert ride["ride_id"] == ride_id

    def test_increment_ride_id(self):
        reg = ActiveRidesRegistry()
        id1 = reg.create_ride(user_id=1, vehicle_id="V001", start_station_id=10)
        id2 = reg.create_ride(user_id=2, vehicle_id="V002", start_station_id=10)
        assert id2 == id1 + 1
