"""Tests for FleetManager (orchestration skeleton + DI + in-memory state)."""

import datetime
from unittest.mock import MagicMock

import pytest

from src.domain.exceptions import ConflictError, InvalidInputError, NotFoundError
from src.domain.VehicleContainer import DegradedRepo
from src.services.active_rides import ActiveRidesRegistry
from src.services.billing import BillingService
from src.services.fleet_manager import FleetManager


class TestFleetManager:
    #-----------------------------
    # Initialization Tests
    #-----------------------------
    def test_initial_state(self):
        stations = {1: MagicMock(), 2: MagicMock()}
        vehicles = {}

        fm = FleetManager(stations=stations, vehicles=vehicles)

        assert fm.stations is stations
        assert fm.vehicles is vehicles
        assert fm.users == {}

    def test_initialize_state_eligible_vehicle_stays_in_station(self):
        station = MagicMock()
        station.remove_vehicle = MagicMock()

        stations = {1: station}

        vehicle = MagicMock()
        vehicle.is_eligible.return_value = True
        vehicle.station_id = 1
        vehicle.active_ride_id = None
        vehicle.mark_degraded = MagicMock()

        vehicles = {"V101": vehicle}

        degraded_repo = MagicMock()
        degraded_repo.add_vehicle = MagicMock()

        FleetManager(stations=stations, vehicles=vehicles, degraded_repo=degraded_repo)

        degraded_repo.add_vehicle.assert_not_called()
        vehicle.mark_degraded.assert_not_called()
        station.remove_vehicle.assert_not_called()
        station.add_vehicle.assert_called_once_with("V101")

    def test_initialize_state_ineligible_vehicle_moved_and_removed(self):
        station = MagicMock()
        station.remove_vehicle = MagicMock()

        stations = {1: station}

        vehicle = MagicMock()
        vehicle.is_eligible.return_value = False
        vehicle.station_id = 1
        vehicle.active_ride_id = None
        vehicle.mark_degraded = MagicMock()

        vehicles = {"V202": vehicle}

        degraded_repo = MagicMock()
        degraded_repo.add_vehicle = MagicMock()

        FleetManager(stations=stations, vehicles=vehicles, degraded_repo=degraded_repo)

        degraded_repo.add_vehicle.assert_called_once_with("V202")
        vehicle.mark_degraded.assert_called_once()

    def test_initialize_state_ineligible_vehicle_missing_station(self):
        # station_id points to a station that doesn't exist -> should not crash
        stations = {}

        vehicle = MagicMock()
        vehicle.is_eligible.return_value = False
        vehicle.station_id = 99
        vehicle.active_ride_id = None
        vehicle.mark_degraded = MagicMock()

        vehicles = {"V303": vehicle}

        degraded_repo = MagicMock()
        degraded_repo.add_vehicle = MagicMock()

        FleetManager(stations=stations, vehicles=vehicles, degraded_repo=degraded_repo)

        degraded_repo.add_vehicle.assert_called_once_with("V303")
        vehicle.mark_degraded.assert_called_once()

    def test_uses_injected_dependencies(self):
        stations = {1: MagicMock()}
        vehicles = {}

        active = ActiveRidesRegistry()
        repo = DegradedRepo(container_id=-1, _vehicle_ids=set(), name="Degraded Repo")
        billing = BillingService()

        fm = FleetManager(
            stations=stations,
            vehicles=vehicles,
            active_rides=active,
            degraded_repo=repo,
            billing_service=billing,
        )

        assert fm.active_rides is active
        assert fm.degraded_repo is repo
        assert fm.billing_service is billing

    def test_default_dependencies_are_not_shared_between_instances(self):
        stations = {1: MagicMock()}
        vehicles = {}

        fm1 = FleetManager(stations=stations, vehicles=vehicles)
        fm2 = FleetManager(stations=stations, vehicles=vehicles)

        # Proves you avoided the "mutable default args" trap
        assert fm1.active_rides is not fm2.active_rides
        assert fm1.degraded_repo is not fm2.degraded_repo
        assert fm1.billing_service is not fm2.billing_service

    def test_initialize_state_raises_if_vehicle_has_active_ride_at_bootstrap(self):
        vehicle = MagicMock()
        vehicle.active_ride_id = 999
        vehicle.is_eligible.return_value = False
        vehicle.station_id = 1
        vehicle.mark_degraded = MagicMock()

        station = MagicMock()
        stations = {1: station}
        vehicles = {"V105": vehicle}

        with pytest.raises(InvalidInputError):
            FleetManager(stations=stations, vehicles=vehicles)

    # -----------------------------
    # User Registration Tests
    # -----------------------------
    def test_register_user_creates_and_stores_user_and_returns_id(self):
        fm = FleetManager(stations={}, vehicles={})

        user_id = fm.register_user("tok_test")

        assert isinstance(user_id, int)
        assert user_id in fm.users
        assert fm.users[user_id].user_id == user_id
        assert fm.users[user_id].payment_token == "tok_test"

    def test_register_user_rejects_blank_token(self):
        fm = FleetManager(stations={}, vehicles={})

        with pytest.raises(InvalidInputError):
            fm.register_user("")

        with pytest.raises(InvalidInputError):
            fm.register_user("   ")

    def test_register_user_rejects_non_string_token(self):
        fm = FleetManager(stations={}, vehicles={})

        with pytest.raises(InvalidInputError):
            fm.register_user(None)

    def test_register_user_rejects_exact_duplicate_token(self):
        fm = FleetManager(stations={}, vehicles={})

        fm.register_user("tok_test")

        with pytest.raises(ConflictError):
            fm.register_user("tok_test")

    def test_register_user_rejects_whitespace_variant_duplicate(self):
        fm = FleetManager(stations={}, vehicles={})

        fm.register_user("tok")

        with pytest.raises(ConflictError):
            fm.register_user(" tok ")

    def test_register_user_stores_normalized_token(self):
        fm = FleetManager(stations={}, vehicles={})

        user_id = fm.register_user(" tok_test ")

        assert fm.users[user_id].payment_token == "tok_test"

    #-----------------------------
    # Nearest Station Tests
    #-----------------------------
    def test_find_nearest_station_with_available_vehicle(self):
        stations = {
            1: MagicMock(lat=0.0, lon=0.0, has_available_vehicle=MagicMock(return_value=True), container_id=1),
            2: MagicMock(lat=10.0, lon=10.0, has_available_vehicle=MagicMock(return_value=True), container_id=2),
            3: MagicMock(lat=20.0, lon=20.0, has_available_vehicle=MagicMock(return_value=False), container_id=3),
        }
        fm = FleetManager(stations=stations, vehicles={})

        nearest = fm.nearest_station_with_available_vehicle((1.0, 1.0))
        assert nearest is stations[1]  # Station 1 is closer than Station 2

        nearest = fm.nearest_station_with_available_vehicle((15.0, 15.0))
        assert nearest is stations[2]  # Station 2 is closer than Station 1

        nearest = fm.nearest_station_with_available_vehicle((100.0, 100.0))
        assert nearest is stations[2]  # Station 2 is the only one with available vehicles

    def test_nearest_station_returns_none_when_no_available(self):
        stations = {
            1: MagicMock(lat=0.0, lon=0.0, has_available_vehicle=MagicMock(return_value=False), container_id=1),
            2: MagicMock(lat=1.0, lon=1.0, has_available_vehicle=MagicMock(return_value=False), container_id=2),
        }
        fm = FleetManager(stations=stations, vehicles={})

        assert fm.nearest_station_with_available_vehicle((0.0, 0.0)) is None

    #--------------------
    # end ride tests
    #--------------------
    def test_end_ride_invalid_location_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        with pytest.raises(InvalidInputError):
            fm.end_ride(ride_id=1, location="bad")

        with pytest.raises(InvalidInputError):
            fm.end_ride(ride_id=1, location=(1.0,))

    def test_end_ride_ride_not_found_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        fm.active_rides = MagicMock()
        fm.active_rides.get.side_effect = KeyError("missing")

        with pytest.raises(NotFoundError, match="Ride does not exist"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_no_free_slots_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id="V10", start_time=datetime.datetime(2026, 1, 1, 10, 0))
        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride

        fm._nearest_station_with_free_slot = MagicMock(return_value=None)

        with pytest.raises(NotFoundError, match="No free slots"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_user_missing_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id="V10", start_time=datetime.datetime(2026, 1, 1, 10, 0))
        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride

        station = MagicMock(container_id=7, lat=1.0, lon=2.0)
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        fm.users = {}  # user missing

        with pytest.raises(NotFoundError, match="User for this ride does not exist"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_payment_failed_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id="V10", start_time=datetime.datetime(2026, 1, 1, 10, 0))
        ride.end = MagicMock()

        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride

        station = MagicMock(container_id=7, lat=1.0, lon=2.0)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        user = MagicMock(payment_token="tok_test")
        fm.users = {1: user}

        fm.billing_service = MagicMock()
        fm.billing_service.calculate_price.return_value = 15.0
        fm.billing_service.process_payment.return_value = False  # payment fails

        with pytest.raises(ConflictError, match="Payment failed"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

        # Should not end ride / remove if payment fails
        ride.end.assert_not_called()
        fm.active_rides.remove.assert_not_called()

    def test_end_ride_happy_path_docks_vehicle_and_returns_station_id_and_price(self):
        fm = FleetManager(stations={}, vehicles={})

        ride = MagicMock(
            user_id=1,
            vehicle_id="V010",
            start_time=datetime.datetime(2026, 1, 1, 10, 0),
        )
        ride.end = MagicMock()

        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride
        fm.active_rides.remove = MagicMock()

        station = MagicMock(container_id=7, lat=1.0, lon=2.0)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        user = MagicMock(payment_token="tok_test")
        fm.users = {1: user}

        fm.billing_service = MagicMock()
        fm.billing_service.calculate_price.return_value = 15.0
        fm.billing_service.process_payment.return_value = True

        vehicle = MagicMock(vehicle_id="V010")
        vehicle.add_ride_count = MagicMock()
        vehicle.is_eligible.return_value = True
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        vehicle.dock_to_station = MagicMock()

        # Avoid bootstrap coupling: set vehicles after init
        fm.vehicles = {"V010": vehicle}

        station_id, price = fm.end_ride(ride_id=99, location=(9.0, 9.0))

        ride.end.assert_called_once()
        fm.active_rides.remove.assert_called_once_with(99)

        vehicle.add_ride_count.assert_called_once()
        vehicle.move_to_repo.assert_not_called()
        vehicle.mark_degraded.assert_not_called()

        station.add_vehicle.assert_called_once_with("V010")
        vehicle.dock_to_station.assert_called_once_with(7)

        assert station_id == 7
        assert price == 15.0

    def test_end_ride_ineligible_vehicle_moves_to_degraded_and_still_docks(self):
        fm = FleetManager(stations={}, vehicles={})

        ride = MagicMock(
            user_id=1,
            vehicle_id="V010",
            start_time=datetime.datetime(2026, 1, 1, 10, 0),
        )
        ride.end = MagicMock()

        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride
        fm.active_rides.remove = MagicMock()

        station = MagicMock(container_id=7, lat=1.0, lon=2.0)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        user = MagicMock(payment_token="tok_test")
        fm.users = {1: user}

        fm.billing_service = MagicMock()
        fm.billing_service.calculate_price.return_value = 15.0
        fm.billing_service.process_payment.return_value = True

        fm.degraded_repo = MagicMock()
        fm.degraded_repo.add_vehicle = MagicMock()

        vehicle = MagicMock(vehicle_id="V010")
        vehicle.add_ride_count = MagicMock()
        vehicle.is_eligible.return_value = False  # becomes ineligible
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        vehicle.dock_to_station = MagicMock()

        fm.vehicles = {"V010": vehicle}

        station_id, price = fm.end_ride(ride_id=99, location=(9.0, 9.0))

        fm.degraded_repo.add_vehicle.assert_called_once_with(vehicle_id="V010")
        vehicle.move_to_repo.assert_called_once()
        vehicle.mark_degraded.assert_called_once()

        station.add_vehicle.assert_called_once_with("V010")
        vehicle.dock_to_station.assert_called_once_with(7)

        assert station_id == 7
        assert price == 15.0
