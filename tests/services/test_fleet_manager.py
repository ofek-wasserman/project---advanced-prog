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

    #-----------------------------
    # Ride start Tests
    #-----------------------------
    def test_start_ride_user_does_not_exist_raises(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {}

        with pytest.raises(NotFoundError, match="User does not exist"):
            fm.start_ride(user_id=1, location=(0.0, 0.0))

    def test_start_ride_user_already_has_active_ride_raises(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        # simulate active ride for user
        fm.active_rides.rides_by_user[1] = 999

        with pytest.raises(ConflictError, match="already has an active ride"):
            fm.start_ride(user_id=1, location=(0.0, 0.0))

    def test_start_ride_no_station_available_returns_none_payload(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        fm.nearest_station_with_available_vehicle = MagicMock(return_value=None)

        result = fm.start_ride(user_id=1, location=(0.0, 0.0))
        assert result is None

    def test_start_ride_happy_path_registers_ride_and_mutates_station_vehicle(self, monkeypatch):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        # Station with vehicles {10, 11}
        station = MagicMock()
        station.lat = 10.0
        station.lon = 20.0
        station.container_id = 7
        station.get_vehicle_ids.return_value = {10, 11}
        station.remove_vehicle = MagicMock()

        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)

        # Vehicles - selection is based on (rides_since_last_treated, vid) in your code
        v10 = MagicMock(rides_since_last_treated=5)
        v10.checkout_to_ride = MagicMock()
        v11 = MagicMock(rides_since_last_treated=1)
        v11.checkout_to_ride = MagicMock()
        fm.vehicles = {10: v10, 11: v11}

        fm._generate_ride_id = MagicMock(return_value=123)

        # IMPORTANT: your implementation must generate ride_id before checkout_to_ride
        # If it's still after, this test will crash with UnboundLocalError.
        ride = fm.start_ride(user_id=1, location=(0.0, 0.0))

        station.remove_vehicle.assert_called_once_with(11)
        v11.checkout_to_ride.assert_called_once_with(ride_id=123)
        v10.checkout_to_ride.assert_not_called()

        assert ride.ride_id == 123
        assert ride.user_id == 1
        assert ride.vehicle_id == 11
        assert ride.start_station_id == 7
        assert isinstance(ride.start_time, datetime.datetime)

        # Confirm registry contains it
        assert fm.active_rides.get(123) is ride
        assert fm.active_rides.has_active_ride_for_user(1) is True

    def test_start_ride_when_registry_rejects_ride_raises_value_error(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        station = MagicMock()
        station.lat = 0.0
        station.lon = 0.0
        station.container_id = 1
        station.get_vehicle_ids.return_value = {10}
        station.remove_vehicle = MagicMock()
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)

        v10 = MagicMock(rides_since_last_treated=0)
        v10.checkout_to_ride = MagicMock()
        fm.vehicles = {10: v10}

        fm._generate_ride_id = MagicMock(return_value=999)

        # Pre-fill registry with ride_id=999 to force add() ValueError
        fm.active_rides.rides[999] = MagicMock()
        fm.active_rides.rides_by_user[123] = 999  # doesn't matter which user

        with pytest.raises(ConflictError, match="Cannot start ride:"):
            fm.start_ride(user_id=1, location=(0.0, 0.0))

    def test_start_ride_deterministic_vehicle_selection_tie_breaks_by_smallest_id(self):
        station = MagicMock()
        station.container_id = 1
        station.lat = 0.0
        station.lon = 0.0
        station.has_available_vehicle.return_value = True
        station.get_vehicle_ids.return_value = {10, 11, 12}
        station.remove_vehicle = MagicMock()
        station.add_vehicle = MagicMock()  # needed for _initialize_state

        # Vehicles (make them bootstrap-valid)
        v10 = MagicMock(rides_since_last_treated=1)
        v10.checkout_to_ride = MagicMock()
        v10.is_eligible.return_value = True
        v10.station_id = 1
        v10.active_ride_id = None

        v11 = MagicMock(rides_since_last_treated=1)
        v11.checkout_to_ride = MagicMock()
        v11.is_eligible.return_value = True
        v11.station_id = 1
        v11.active_ride_id = None

        v12 = MagicMock(rides_since_last_treated=5)
        v12.checkout_to_ride = MagicMock()
        v12.is_eligible.return_value = True
        v12.station_id = 1
        v12.active_ride_id = None

        vehicles = {10: v10, 11: v11, 12: v12}
        stations = {1: station}

        fm = FleetManager(stations=stations, vehicles=vehicles, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)
        fm._generate_ride_id = MagicMock(return_value=99)

        ride = fm.start_ride(user_id=1, location=(0.0, 0.0))

        assert ride is not None
        assert ride.vehicle_id == 10  # tie-break by smallest id

        station.remove_vehicle.assert_called_once_with(10)
        v10.checkout_to_ride.assert_called_once_with(ride_id=99)
        v11.checkout_to_ride.assert_not_called()
        v12.checkout_to_ride.assert_not_called()

    def test_start_ride_updates_station_inventory_removes_selected_vehicle_only(self):
        inventory = {10, 11, 12}

        station = MagicMock()
        station.container_id = 1
        station.lat = 0.0
        station.lon = 0.0
        station.has_available_vehicle.return_value = True
        station.get_vehicle_ids.side_effect = lambda: set(inventory)
        station.add_vehicle = MagicMock()  # needed for _initialize_state

        def remove_vehicle(vid):
            inventory.remove(vid)

        station.remove_vehicle.side_effect = remove_vehicle

        v10 = MagicMock(rides_since_last_treated=3)
        v10.checkout_to_ride = MagicMock()
        v10.is_eligible.return_value = True
        v10.station_id = 1
        v10.active_ride_id = None

        v11 = MagicMock(rides_since_last_treated=0)
        v11.checkout_to_ride = MagicMock()
        v11.is_eligible.return_value = True
        v11.station_id = 1
        v11.active_ride_id = None

        v12 = MagicMock(rides_since_last_treated=2)
        v12.checkout_to_ride = MagicMock()
        v12.is_eligible.return_value = True
        v12.station_id = 1
        v12.active_ride_id = None

        vehicles = {10: v10, 11: v11, 12: v12}
        stations = {1: station}

        fm = FleetManager(stations=stations, vehicles=vehicles, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)
        fm._generate_ride_id = MagicMock(return_value=100)

        ride = fm.start_ride(user_id=1, location=(0.0, 0.0))

        assert ride is not None
        assert ride.vehicle_id == 11
        assert inventory == {10, 12}
    #--------------------
    # end ride tests
    #--------------------
    def test_end_ride_invalid_location_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        with pytest.raises(InvalidInputError):
            fm.end_ride(ride_id=1, location="bad")  # type: ignore

        with pytest.raises(InvalidInputError):
            fm.end_ride(ride_id=1, location=(1.0,))  # wrong length

    def test_end_ride_ride_not_found_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        fm.active_rides = MagicMock()
        fm.active_rides.get.side_effect = KeyError("missing")

        with pytest.raises(NotFoundError, match="Ride does not exist"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_no_free_slots_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id=10, start_time=datetime.datetime(2026, 1, 1, 10, 0))
        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride

        fm._nearest_station_with_free_slot = MagicMock(return_value=None)

        with pytest.raises(NotFoundError, match="No free slots"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_user_missing_raises(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id=10, start_time=datetime.datetime(2026, 1, 1, 10, 0))
        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride

        station = MagicMock(container_id=7, lat=1.0, lon=2.0)
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        fm.users = {}  # user missing

        with pytest.raises(NotFoundError, match="User for this ride does not exist"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_payment_failed_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id=10, start_time=datetime.datetime(2026, 1, 1, 10, 0))
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

    def test_end_ride_happy_path_docks_vehicle_and_returns_station_location(self):
        fm = FleetManager(stations={}, vehicles={})

        ride = MagicMock(
            user_id=1,
            vehicle_id=10,
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

        vehicle = MagicMock(vehicle_id=10)
        vehicle.add_ride_count = MagicMock()
        vehicle.is_eligible.return_value = True
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        vehicle.dock_to_station = MagicMock()
        fm.vehicles = {10: vehicle}

        result = fm.end_ride(ride_id=99, location=(9.0, 9.0))

        # ride ended + removed from registry
        ride.end.assert_called_once()
        fm.active_rides.remove.assert_called_once_with(99)

        # vehicle processing
        vehicle.add_ride_count.assert_called_once()
        vehicle.move_to_repo.assert_not_called()
        vehicle.mark_degraded.assert_not_called()

        # docked back to station
        station.add_vehicle.assert_called_once_with(10)
        vehicle.dock_to_station.assert_called_once_with(7)

        assert result == {"price": 15.0, "location": (1.0, 2.0)}

    def test_end_ride_ineligible_vehicle_moves_to_degraded(self):
        fm = FleetManager(stations={}, vehicles={})

        ride = MagicMock(
            user_id=1,
            vehicle_id=10,
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

        vehicle = MagicMock(vehicle_id=10)
        vehicle.add_ride_count = MagicMock()
        vehicle.is_eligible.return_value = False  # becomes ineligible
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        vehicle.dock_to_station = MagicMock()
        fm.vehicles = {10: vehicle}

        result = fm.end_ride(ride_id=99, location=(9.0, 9.0))

        fm.degraded_repo.add_vehicle.assert_called_once_with(vehicle_id=10)
        vehicle.move_to_repo.assert_called_once()
        vehicle.mark_degraded.assert_called_once()

        # still docks to station (matches your current implementation)
        station.add_vehicle.assert_called_once_with(10)
        vehicle.dock_to_station.assert_called_once_with(7)

        assert result == {"price": 15.0, "location": (1.0, 2.0)}

    def test_nearest_station_with_free_slot_picks_closest(self):
        s1 = MagicMock(container_id=1, lat=0.0, lon=0.0)
        s1.has_free_slot.return_value = True

        s2 = MagicMock(container_id=2, lat=10.0, lon=10.0)
        s2.has_free_slot.return_value = True

        s3 = MagicMock(container_id=3, lat=1.0, lon=1.0)
        s3.has_free_slot.return_value = False  # ignored

        fm = FleetManager(stations={1: s1, 2: s2, 3: s3}, vehicles={})
        nearest = fm._nearest_station_with_free_slot((0.9, 0.9))

        assert nearest is s1  # (0.9,0.9) closer to (0,0) than (10,10)

    def test_nearest_station_with_free_slot_tie_breaks_by_container_id(self):
        # location (0,1) is equally distant from (0,0) and (0,2)
        s10 = MagicMock(container_id=10, lat=0.0, lon=0.0)
        s10.has_free_slot.return_value = True

        s5 = MagicMock(container_id=5, lat=0.0, lon=2.0)
        s5.has_free_slot.return_value = True

        fm = FleetManager(stations={10: s10, 5: s5}, vehicles={})
        nearest = fm._nearest_station_with_free_slot((0.0, 1.0))

        assert nearest is s5  # smaller container_id wins tie

    def test_nearest_station_with_free_slot_returns_none_when_no_valid_stations(self):
        s1 = MagicMock(container_id=1, lat=0.0, lon=0.0)
        s1.has_free_slot.return_value = False

        s2 = MagicMock(container_id=2, lat=10.0, lon=10.0)
        s2.has_free_slot.return_value = False

        fm = FleetManager(stations={1: s1, 2: s2}, vehicles={})
        assert fm._nearest_station_with_free_slot((0.0, 0.0)) is None

    def test_nearest_station_with_free_slot_invalid_location_raises(self):
        fm = FleetManager(stations={}, vehicles={})

        with pytest.raises(InvalidInputError):
            fm._nearest_station_with_free_slot("bad")  # type: ignore

        with pytest.raises(InvalidInputError):
            fm._nearest_station_with_free_slot((1.0,))  # wrong length
