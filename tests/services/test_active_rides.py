"""Tests for active rides registry."""

import datetime

import pytest

from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.ride import Ride
from src.services.active_rides import ActiveRidesRegistry


class TestActiveRidesRegistry:
    def test_add_stores_ride_and_indexes(self):
        reg = ActiveRidesRegistry()
        ride = Ride(
            ride_id=1,
            user_id=10,
            vehicle_id="V001",
            start_time=datetime.datetime(2026, 1, 1, 10, 0, 0),
            start_station_id=7,
        )

        reg.add(ride)

        assert reg.get(1) is ride
        assert reg.has_active_ride_for_user(10) is True
        assert reg.is_vehicle_in_ride("V001") is True
        assert reg.get_active_ride_for_user(10) is ride
        assert 10 in reg.active_user_ids()
        assert 1 in reg.active_ride_ids()
        assert isinstance(reg.active_user_ids(), set)
        assert isinstance(reg.active_ride_ids(), set)

    def test_add_rejects_duplicate_ride_id(self):
        reg = ActiveRidesRegistry()
        t = datetime.datetime(2026, 1, 1, 10, 0, 0)

        ride1 = Ride(ride_id=1, user_id=10, vehicle_id="V001", start_time=t, start_station_id=7)
        ride2 = Ride(ride_id=1, user_id=11, vehicle_id="V002", start_time=t, start_station_id=7)

        reg.add(ride1)
        with pytest.raises(ConflictError, match="Ride ID 1 already exists"):
            reg.add(ride2)

    def test_add_rejects_user_with_existing_active_ride(self):
        reg = ActiveRidesRegistry()
        t = datetime.datetime(2026, 1, 1, 10, 0, 0)

        ride1 = Ride(ride_id=1, user_id=10, vehicle_id="V001", start_time=t, start_station_id=7)
        ride2 = Ride(ride_id=2, user_id=10, vehicle_id="V002", start_time=t, start_station_id=7)

        reg.add(ride1)
        with pytest.raises(ConflictError, match="User ID 10 already has an active ride"):
            reg.add(ride2)

    def test_add_rejects_vehicle_already_in_active_ride(self):
        reg = ActiveRidesRegistry()
        t = datetime.datetime(2026, 1, 1, 10, 0, 0)

        ride1 = Ride(ride_id=1, user_id=10, vehicle_id="V001", start_time=t, start_station_id=7)
        ride2 = Ride(ride_id=2, user_id=11, vehicle_id="V001", start_time=t, start_station_id=7)

        reg.add(ride1)
        with pytest.raises(ConflictError, match="Vehicle ID V001 is already in an active ride"):
            reg.add(ride2)

    def test_remove_deletes_ride_and_clears_indexes(self):
        reg = ActiveRidesRegistry()
        ride = Ride(
            ride_id=1,
            user_id=10,
            vehicle_id="V001",
            start_time=datetime.datetime(2026, 1, 1, 10, 0, 0),
            start_station_id=7,
        )
        reg.add(ride)

        removed = reg.remove(1)

        assert removed is ride
        assert reg.has_active_ride_for_user(10) is False
        assert reg.is_vehicle_in_ride("V001") is False
        assert reg.get_active_ride_for_user(10) is None
        assert 10 not in reg.active_user_ids()
        assert 1 not in reg.active_ride_ids()

        with pytest.raises(NotFoundError, match="Ride ID 1 not found"):
            reg.get(1)

    def test_get_missing_raises_NotFoundError(self):
        reg = ActiveRidesRegistry()
        with pytest.raises(NotFoundError, match="Ride ID 999 not found"):
            reg.get(999)

    def test_remove_missing_raises_NotFoundError(self):
        reg = ActiveRidesRegistry()
        with pytest.raises(NotFoundError, match="Ride ID 999 not found"):
            reg.remove(999)

    def test_get_active_ride_for_user_returns_none_when_missing(self):
        reg = ActiveRidesRegistry()
        assert reg.get_active_ride_for_user(123) is None
