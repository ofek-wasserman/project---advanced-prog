"""Tests for FleetManager (orchestration skeleton + DI + in-memory state)."""

import datetime
from unittest.mock import MagicMock

import pytest

from src.domain.enums import VehicleStatus
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

    def test_initialize_state_already_degraded_vehicle_skips_mark_degraded(self):
        """Regression: bootstrap must not call mark_degraded() on a vehicle
        that is already DEGRADED."""
        stations = {1: MagicMock()}

        vehicle = MagicMock()
        vehicle.is_eligible.return_value = False
        vehicle.status = VehicleStatus.DEGRADED
        vehicle.station_id = 1
        vehicle.active_ride_id = None
        vehicle.mark_degraded = MagicMock()

        degraded_repo = MagicMock()
        FleetManager(stations=stations, vehicles={"V999": vehicle}, degraded_repo=degraded_repo)

        vehicle.mark_degraded.assert_not_called()
        degraded_repo.add_vehicle.assert_called_once_with("V999")

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

    def test_start_ride_no_station_available_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        fm.nearest_station_with_available_vehicle = MagicMock(return_value=None)

        with pytest.raises(ConflictError, match="No eligible vehicles"):
            fm.start_ride(user_id=1, location=(0.0, 0.0))

    def test_start_ride_happy_path_registers_ride_and_mutates_station_vehicle(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        station = MagicMock()
        station.lat = 10.0
        station.lon = 20.0
        station.container_id = 7
        station.get_vehicle_ids.return_value = {"V010", "V011"}
        station.remove_vehicle = MagicMock()

        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)

        v010 = MagicMock(rides_since_last_treated=5)
        v010.checkout_to_ride = MagicMock()
        v011 = MagicMock(rides_since_last_treated=1)
        v011.checkout_to_ride = MagicMock()
        fm.vehicles = {"V010": v010, "V011": v011}

        fm._generate_ride_id = MagicMock(return_value=123)

        ride, start_station_id = fm.start_ride(user_id=1, location=(0.0, 0.0))

        assert start_station_id == 7
        assert ride.ride_id == 123
        assert ride.user_id == 1
        assert ride.vehicle_id == "V011"
        assert ride.start_station_id == 7
        assert isinstance(ride.start_time, datetime.datetime)

        station.remove_vehicle.assert_called_once_with("V011")
        v011.checkout_to_ride.assert_called_once_with(ride_id=123)
        v010.checkout_to_ride.assert_not_called()

        assert fm.active_rides.get(123) is ride
        assert fm.active_rides.has_active_ride_for_user(1) is True

    def test_start_ride_when_registry_rejects_ride_raises_conflict_error(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}

        station = MagicMock()
        station.lat = 0.0
        station.lon = 0.0
        station.container_id = 1
        station.get_vehicle_ids.return_value = {"V010"}
        station.remove_vehicle = MagicMock()
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)

        v010 = MagicMock(rides_since_last_treated=0)
        v010.checkout_to_ride = MagicMock()
        fm.vehicles = {"V010": v010}

        fm._generate_ride_id = MagicMock(return_value=999)

        # force registry conflict on ride_id
        fm.active_rides.rides[999] = MagicMock()

        with pytest.raises(ConflictError, match="Cannot start ride:"):
            fm.start_ride(user_id=1, location=(0.0, 0.0))

        # Since add() happens before removal/checkout, state should NOT mutate on failure
        station.remove_vehicle.assert_not_called()
        v010.checkout_to_ride.assert_not_called()

    def test_start_ride_deterministic_vehicle_selection_tie_breaks_by_smallest_vehicle_id(self):
        station = MagicMock()
        station.container_id = 1
        station.lat = 0.0
        station.lon = 0.0
        station.get_vehicle_ids.return_value = {"V010", "V011", "V012"}
        station.remove_vehicle = MagicMock()
        station.add_vehicle = MagicMock()  # for _initialize_state if needed

        v010 = MagicMock(rides_since_last_treated=1, station_id=1, active_ride_id=None)
        v010.is_eligible.return_value = True
        v010.checkout_to_ride = MagicMock()

        v011 = MagicMock(rides_since_last_treated=1, station_id=1, active_ride_id=None)
        v011.is_eligible.return_value = True
        v011.checkout_to_ride = MagicMock()

        v012 = MagicMock(rides_since_last_treated=5, station_id=1, active_ride_id=None)
        v012.is_eligible.return_value = True
        v012.checkout_to_ride = MagicMock()

        vehicles = {"V010": v010, "V011": v011, "V012": v012}
        stations = {1: station}

        fm = FleetManager(stations=stations, vehicles=vehicles, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)
        fm._generate_ride_id = MagicMock(return_value=99)

        ride, start_station_id = fm.start_ride(user_id=1, location=(0.0, 0.0))

        assert start_station_id == 1
        assert ride.vehicle_id == "V010"  # tie on rides_since_last_treated -> smallest ID wins

        station.remove_vehicle.assert_called_once_with("V010")
        v010.checkout_to_ride.assert_called_once_with(ride_id=99)
        v011.checkout_to_ride.assert_not_called()
        v012.checkout_to_ride.assert_not_called()

    def test_start_ride_updates_station_inventory_removes_selected_vehicle_only(self):
        inventory = {"V010", "V011", "V012"}

        station = MagicMock()
        station.container_id = 1
        station.lat = 0.0
        station.lon = 0.0
        station.get_vehicle_ids.side_effect = lambda: set(inventory)
        station.add_vehicle = MagicMock()  # for _initialize_state if needed

        def remove_vehicle(vid):
            inventory.remove(vid)

        station.remove_vehicle.side_effect = remove_vehicle

        v010 = MagicMock(rides_since_last_treated=3, station_id=1, active_ride_id=None)
        v010.is_eligible.return_value = True
        v010.checkout_to_ride = MagicMock()

        v011 = MagicMock(rides_since_last_treated=0, station_id=1, active_ride_id=None)
        v011.is_eligible.return_value = True
        v011.checkout_to_ride = MagicMock()

        v012 = MagicMock(rides_since_last_treated=2, station_id=1, active_ride_id=None)
        v012.is_eligible.return_value = True
        v012.checkout_to_ride = MagicMock()

        vehicles = {"V010": v010, "V011": v011, "V012": v012}
        stations = {1: station}

        fm = FleetManager(stations=stations, vehicles=vehicles, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)
        fm._generate_ride_id = MagicMock(return_value=100)

        ride, _ = fm.start_ride(user_id=1, location=(0.0, 0.0))

        assert ride.vehicle_id == "V011"
        assert inventory == {"V010", "V012"}

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
        fm.active_rides.get.side_effect = NotFoundError("Ride does not exist")

        with pytest.raises(NotFoundError, match="Ride does not exist"):
            fm.end_ride(ride_id=1, location=(0.0, 0.0))

    def test_end_ride_no_free_slots_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={})
        ride = MagicMock(user_id=1, vehicle_id="V10", start_time=datetime.datetime(2026, 1, 1, 10, 0))
        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride

        fm._nearest_station_with_free_slot = MagicMock(return_value=None)

        with pytest.raises(ConflictError, match="No station with free slot available"):
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

    def test_end_ride_ineligible_vehicle_moves_to_degraded_and_not_docked(self):
        fm = FleetManager(stations={}, vehicles={})

        ride = MagicMock(
            user_id=1,
            vehicle_id="V010",
            start_time=datetime.datetime(2026, 1, 1, 10, 0),
        )
        ride.reported_degraded = False
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
        vehicle.status = "OK"  # not already degraded, so mark_degraded should be called
        vehicle.add_ride_count = MagicMock()
        vehicle.is_eligible.return_value = False
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        vehicle.dock_to_station = MagicMock()

        fm.vehicles = {"V010": vehicle}

        station_id, price = fm.end_ride(ride_id=99, location=(9.0, 9.0))

        fm.degraded_repo.add_vehicle.assert_called_once_with(vehicle_id="V010")
        vehicle.move_to_repo.assert_called_once()
        vehicle.mark_degraded.assert_called_once()

        # Ineligible vehicle is NOT docked and NOT added to station inventory
        station.add_vehicle.assert_not_called()
        vehicle.dock_to_station.assert_not_called()

        # New behavior: returns nearest station id even when moved to degraded repo
        assert station_id == 7
        assert price == 15.0

    def test_end_ride_already_degraded_vehicle_skips_mark_degraded(self):
        """Regression: end_ride must not call mark_degraded() on a vehicle
        that is already DEGRADED."""
        fm = FleetManager(stations={}, vehicles={})

        ride = MagicMock(user_id=1, vehicle_id="V011", start_time=datetime.datetime(2026, 1, 1, 10, 0))
        ride.end = MagicMock()

        fm.active_rides = MagicMock()
        fm.active_rides.get.return_value = ride
        fm.active_rides.remove = MagicMock()

        station = MagicMock(container_id=8, lat=1.0, lon=2.0)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        fm.users = {1: MagicMock(payment_token="tok_test")}
        fm.billing_service = MagicMock()
        fm.billing_service.calculate_price.return_value = 15.0
        fm.billing_service.process_payment.return_value = True

        fm.degraded_repo = MagicMock()

        vehicle = MagicMock(vehicle_id="V011")
        vehicle.status = VehicleStatus.DEGRADED  # already degraded
        vehicle.is_eligible.return_value = False
        vehicle.add_ride_count = MagicMock()
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        vehicle.dock_to_station = MagicMock()
        fm.vehicles = {"V011": vehicle}

        fm.end_ride(ride_id=99, location=(9.0, 9.0))

        vehicle.mark_degraded.assert_not_called()
        fm.degraded_repo.add_vehicle.assert_called_once_with(vehicle_id="V011")

    # -----------------------------
    # Active Users Wrapper Tests
    # -----------------------------
    def test_active_user_ids_returns_sorted_active_users(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())

        fm.active_rides.rides_by_user = {5: 100, 2: 101, 9: 102}

        assert fm.active_user_ids() == [2, 5, 9]



    #-----------------------------
    # Full Ride Lifecycle Tests
    #-----------------------------
    def test_full_ride_lifecycle_register_start_end(self):
        # --- Setup station inventory with real mutation ---
        inventory = {"V010"}

        station = MagicMock()
        station.container_id = 7
        station.lat = 1.0
        station.lon = 2.0

        # For start_ride
        station.get_vehicle_ids.side_effect = lambda: set(inventory)
        station.remove_vehicle.side_effect = lambda vid: inventory.remove(vid)

        # For end_ride docking
        station.add_vehicle.side_effect = lambda vid: inventory.add(vid)
        station.has_free_slot.return_value = True

        # --- Setup vehicles ---
        v010 = MagicMock(vehicle_id="V010", rides_since_last_treated=0)
        v010.checkout_to_ride = MagicMock()
        v010.add_ride_count = MagicMock()
        v010.is_eligible.return_value = True
        v010.dock_to_station = MagicMock()
        v010.move_to_repo = MagicMock()
        v010.mark_degraded = MagicMock()

        # --- FleetManager (avoid bootstrap coupling) ---
        fm = FleetManager(stations={7: station}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.vehicles = {"V010": v010}

        # Register user
        user_id = fm.register_user("tok_test")

        # Start ride
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)
        fm._generate_ride_id = MagicMock(return_value=123)

        ride, start_station_id = fm.start_ride(user_id=user_id, location=(0.0, 0.0))

        assert start_station_id == 7
        assert ride.ride_id == 123
        assert ride.vehicle_id == "V010"
        assert "V010" not in inventory  # removed from station
        assert fm.active_rides.has_active_ride_for_user(user_id) is True

        # End ride
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)
        fm.billing_service = MagicMock()
        fm.billing_service.calculate_price.return_value = 15.0
        fm.billing_service.process_payment.return_value = True

        end_station_id, price = fm.end_ride(ride_id=ride.ride_id, location=(9.0, 9.0))

        assert end_station_id == 7
        assert price == 15.0
        assert "V010" in inventory  # returned to station
        assert fm.active_rides.has_active_ride_for_user(user_id) is False

        # Vehicle docked back
        v010.add_ride_count.assert_called_once()
        v010.dock_to_station.assert_called_once_with(7)

    def test_initialize_state_does_not_add_ineligible_vehicle_to_station_inventory(self):
        station = MagicMock()
        station.add_vehicle = MagicMock()

        eligible = MagicMock()
        eligible.is_eligible.return_value = True
        eligible.station_id = 1
        eligible.active_ride_id = None

        ineligible = MagicMock()
        ineligible.is_eligible.return_value = False
        ineligible.station_id = 1
        ineligible.active_ride_id = None
        ineligible.mark_degraded = MagicMock()

        degraded_repo = MagicMock()
        degraded_repo.add_vehicle = MagicMock()

        FleetManager(
            stations={1: station},
            vehicles={"V_OK": eligible, "V_BAD": ineligible},
            degraded_repo=degraded_repo,
        )

        station.add_vehicle.assert_called_once_with("V_OK")
        degraded_repo.add_vehicle.assert_called_once_with("V_BAD")
        ineligible.mark_degraded.assert_called_once()

    def test_multiple_ride_lifecycles_do_not_reuse_ride_ids(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())

        # user exists
        user_id = fm.register_user("tok_test")

        # station with mutable inventory
        inventory = {"V010"}

        station = MagicMock()
        station.container_id = 7
        station.lat = 1.0
        station.lon = 2.0
        station.get_vehicle_ids.side_effect = lambda: set(inventory)
        station.remove_vehicle.side_effect = lambda vid: inventory.remove(vid)
        station.add_vehicle.side_effect = lambda vid: inventory.add(vid)
        station.has_free_slot.return_value = True

        # always pick this station for start/end
        fm.nearest_station_with_available_vehicle = MagicMock(return_value=station)
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        # vehicle
        vehicle = MagicMock(vehicle_id="V010", rides_since_last_treated=0)
        vehicle.checkout_to_ride = MagicMock()
        vehicle.add_ride_count = MagicMock()
        vehicle.is_eligible.return_value = True
        vehicle.dock_to_station = MagicMock()
        fm.vehicles = {"V010": vehicle}

        # billing success
        fm.billing_service = MagicMock()
        fm.billing_service.calculate_price.return_value = 15.0
        fm.billing_service.process_payment.return_value = True

        # ---- lifecycle #1 ----
        ride1, _ = fm.start_ride(user_id=user_id, location=(0.0, 0.0))
        assert ride1.ride_id == 1

        fm.end_ride(ride_id=ride1.ride_id, location=(9.0, 9.0))
        assert ride1.ride_id in fm.completed_rides  # completion persisted

        # ---- lifecycle #2 ----
        ride2, _ = fm.start_ride(user_id=user_id, location=(0.0, 0.0))
        assert ride2.ride_id == 2  # must not reuse 1
        assert ride2.ride_id != ride1.ride_id
    # -----------------------------
    # apply_treatment tests (Phase 2 /vehicle/treat)
    # -----------------------------

    def test_apply_treatment_treats_only_threshold_eligible_vehicles(self):
        fm = FleetManager(stations={}, vehicles={})

        v1 = MagicMock()
        v1.can_initiate_treatment.return_value = True
        v1.apply_treatment = MagicMock()

        v2 = MagicMock()
        v2.can_initiate_treatment.return_value = False
        v2.apply_treatment = MagicMock()

        fm.vehicles = {"V010": v1, "V011": v2}

        fm.degraded_repo = MagicMock()
        fm.degraded_repo.get_vehicle_ids.return_value = set()

        treated = fm.apply_treatment(treatment_location=(0.0, 0.0))

        assert treated == ["V010"]
        v1.apply_treatment.assert_called_once()
        v2.apply_treatment.assert_not_called()


    def test_apply_treatment_degraded_vehicle_removed_from_repo_and_docked_to_station(self):
        fm = FleetManager(stations={}, vehicles={})

        # No threshold-eligible vehicles
        v_ok = MagicMock()
        v_ok.can_initiate_treatment.return_value = False
        fm.vehicles = {"V010": v_ok}

        # Degraded vehicle
        v_deg = MagicMock()
        v_deg.can_initiate_treatment.return_value = False
        v_deg.apply_treatment = MagicMock()
        v_deg.dock_to_station = MagicMock()
        fm.vehicles["V999"] = v_deg

        # Degraded repo contains V999
        fm.degraded_repo = MagicMock()
        fm.degraded_repo.get_vehicle_ids.return_value = {"V999"}
        fm.degraded_repo.remove_vehicle = MagicMock()

        # Nearest station with free slot
        station = MagicMock(container_id=7, lat=1.0, lon=2.0)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        treated = fm.apply_treatment(treatment_location=(9.0, 9.0))

        assert "V999" in treated

        # Order invariant: remove from repo before station add
        calls = []
        fm.degraded_repo.remove_vehicle.side_effect = lambda vid: calls.append(("repo_remove", vid))
        station.add_vehicle.side_effect = lambda vid: calls.append(("station_add", vid))

        fm.apply_treatment(treatment_location=(9.0, 9.0))

        assert calls[0] == ("repo_remove", "V999")
        assert calls[1] == ("station_add", "V999")

        v_deg.dock_to_station.assert_called_with(7)


    def test_apply_treatment_degraded_vehicle_no_station_free_slot_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={})

        v_deg = MagicMock()
        v_deg.can_initiate_treatment.return_value = False
        v_deg.apply_treatment = MagicMock()
        v_deg.dock_to_station = MagicMock()
        fm.vehicles = {"V999": v_deg}

        fm.degraded_repo = MagicMock()
        fm.degraded_repo.get_vehicle_ids.return_value = {"V999"}
        fm.degraded_repo.remove_vehicle = MagicMock()

        fm._nearest_station_with_free_slot = MagicMock(return_value=None)

        with pytest.raises(ConflictError, match="No station with free slot available"):
            fm.apply_treatment(treatment_location=(0.0, 0.0))

        fm.degraded_repo.remove_vehicle.assert_not_called()
        v_deg.dock_to_station.assert_not_called()


    def test_apply_treatment_does_not_leave_degraded_vehicle_in_repo_and_station(self):
        """
        Invariant: after treatment, treated degraded vehicle is not in degraded repo and is docked to a station.
        """
        fm = FleetManager(stations={}, vehicles={})

        repo_ids = {"V999"}

        def get_ids():
            return set(repo_ids)

        def remove_vid(vid):
            repo_ids.remove(vid)

        fm.degraded_repo = MagicMock()
        fm.degraded_repo.get_vehicle_ids.side_effect = get_ids
        fm.degraded_repo.remove_vehicle.side_effect = remove_vid

        v_deg = MagicMock()
        v_deg.can_initiate_treatment.return_value = False
        v_deg.apply_treatment = MagicMock()
        v_deg.dock_to_station = MagicMock()
        fm.vehicles = {"V999": v_deg}

        station = MagicMock(container_id=3)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        fm.apply_treatment(treatment_location=(0.0, 0.0))

        assert "V999" not in repo_ids
        station.add_vehicle.assert_called_once_with("V999")
        v_deg.dock_to_station.assert_called_once_with(3)


    def test_apply_treatment_degraded_vehicle_not_treated_twice_and_not_duplicated(self):
        """
        Regression: degraded vehicle must be treated only once and appear only once in the returned list,
        even if its can_initiate_treatment() would otherwise be True.
        """
        fm = FleetManager(stations={}, vehicles={})

        fm.degraded_repo = MagicMock()
        fm.degraded_repo.get_vehicle_ids.return_value = {"V999"}
        fm.degraded_repo.remove_vehicle = MagicMock()

        station = MagicMock(container_id=7)
        station.add_vehicle = MagicMock()
        fm._nearest_station_with_free_slot = MagicMock(return_value=station)

        v999 = MagicMock(vehicle_id="V999")
        v999.apply_treatment = MagicMock()
        v999.dock_to_station = MagicMock()
        # simulate worst-case: after treatment, it would qualify for second loop
        v999.can_initiate_treatment.return_value = True

        fm.vehicles = {"V999": v999}

        treated = fm.apply_treatment(treatment_location=(0.0, 0.0))

        assert treated.count("V999") == 1
        v999.apply_treatment.assert_called_once()


    # -----------------------------
    # report_degraded_during_ride tests
    # -----------------------------

    def test_report_degraded_success_moves_vehicle_removes_active_ride_and_stores_completed(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock(payment_token="tok_test")}
        fm.completed_rides = {}

        vehicle = MagicMock(vehicle_id="V010")
        vehicle.move_to_repo = MagicMock()
        vehicle.mark_degraded = MagicMock()
        fm.vehicles = {"V010": vehicle}

        fm.degraded_repo = MagicMock()
        fm.degraded_repo.add_vehicle = MagicMock()

        ride = MagicMock(ride_id=123, user_id=1, vehicle_id="V010", price=15.0)
        ride.report_degraded = MagicMock()
        fm.active_rides.add(ride)

        fm.report_degraded(vehicle_id="V010", user_id=1)

        # Ride is marked degraded and free
        ride.report_degraded.assert_called_once()
        assert ride.price == 0

        # Ride removed from active and stored in completed
        with pytest.raises(NotFoundError):
            fm.active_rides.get(123)
        assert fm.completed_rides[123] is ride

        # Vehicle moved + marked degraded + added to repo
        vehicle.move_to_repo.assert_called_once()
        vehicle.mark_degraded.assert_called_once()
        fm.degraded_repo.add_vehicle.assert_called_once_with("V010")


    def test_report_degraded_user_missing_raises_not_found(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {}
        fm.vehicles = {"V010": MagicMock()}

        with pytest.raises(NotFoundError, match="User does not exist"):
            fm.report_degraded(vehicle_id="V010", user_id=1)


    def test_report_degraded_vehicle_missing_raises_not_found(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.vehicles = {}

        with pytest.raises(NotFoundError, match="Vehicle does not exist"):
            fm.report_degraded(vehicle_id="V010", user_id=1)


    def test_report_degraded_vehicle_not_in_any_active_ride_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.vehicles = {"V010": MagicMock()}

        # No rides in registry => vehicle not in active ride
        with pytest.raises(ConflictError, match="Vehicle is not in an active ride"):
            fm.report_degraded(vehicle_id="V010", user_id=1)


    def test_report_degraded_user_has_no_active_ride_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.vehicles = {"V010": MagicMock()}

        # Vehicle is in some active ride, but not for this user
        other_ride = MagicMock(ride_id=1, user_id=999, vehicle_id="V010")
        fm.active_rides.add(other_ride)

        with pytest.raises(ConflictError, match="User does not have an active ride"):
            fm.report_degraded(vehicle_id="V010", user_id=1)


    def test_report_degraded_vehicle_not_in_user_active_ride_raises_conflict(self):
        fm = FleetManager(stations={}, vehicles={}, active_rides=ActiveRidesRegistry())
        fm.users = {1: MagicMock()}
        fm.vehicles = {"V010": MagicMock(), "V999": MagicMock()}

        # User has active ride, but with different vehicle
        ride = MagicMock(ride_id=2, user_id=1, vehicle_id="V999")
        ride.report_degraded = MagicMock()
        fm.active_rides.add(ride)

        # Ensure V010 is not in any active ride too (or error would be earlier)
        with pytest.raises(ConflictError, match="Vehicle is not in an active ride"):
            fm.report_degraded(vehicle_id="V010", user_id=1)

        # Now put V010 into a different user's ride so it passes is_vehicle_in_ride,
        # but still fails "vehicle not in user active ride"
        ride2 = MagicMock(ride_id=3, user_id=2, vehicle_id="V010")
        fm.active_rides.add(ride2)

        with pytest.raises(ConflictError, match="Vehicle not in user active ride"):
            fm.report_degraded(vehicle_id="V010", user_id=1)
