"""Tests for KAN-87 – state_serializer.save_state."""

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from src.data.state_serializer import SCHEMA_VERSION, save_state
from src.domain.Vehicle import Bicycle, EBike, Scooter
from src.domain.VehicleContainer import DegradedRepo, Station
from src.domain.enums import VehicleStatus
from src.domain.ride import Ride
from src.domain.user import User
from src.services.active_rides import ActiveRidesRegistry
from src.services.fleet_manager import FleetManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_station(station_id: int, capacity: int = 10) -> Station:
    return Station(
        container_id=station_id,
        _vehicle_ids=set(),
        name=f"Station {station_id}",
        lat=32.0,
        lon=34.7,
        max_capacity=capacity,
    )


def _make_bicycle(
    vehicle_id: str,
    station_id: int | None = 1,
    rides: int = 0,
    status: VehicleStatus = VehicleStatus.AVAILABLE,
    active_ride_id: int | None = None,
) -> Bicycle:
    return Bicycle(
        vehicle_id=vehicle_id,
        status=status,
        rides_since_last_treated=rides,
        last_treated_date=date(2026, 1, 1),
        station_id=station_id,
        active_ride_id=active_ride_id,
    )


def _make_scooter(
    vehicle_id: str,
    station_id: int | None = 1,
    charge_pct: int = 100,
) -> Scooter:
    return Scooter(
        vehicle_id=vehicle_id,
        status=VehicleStatus.AVAILABLE,
        rides_since_last_treated=0,
        last_treated_date=date(2026, 1, 1),
        station_id=station_id,
        active_ride_id=None,
        charge_pct=charge_pct,
    )


def _minimal_fleet_manager() -> FleetManager:
    """FleetManager with one station, one bicycle, no users, no rides."""
    station = _make_station(1)
    bike = _make_bicycle("V-001", station_id=1)
    return FleetManager(stations={1: station}, vehicles={"V-001": bike})


# ---------------------------------------------------------------------------
# Schema structure tests
# ---------------------------------------------------------------------------

class TestSaveStateStructure:
    def test_creates_file_if_missing(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        assert not out.exists()
        save_state(fm, out)
        assert out.exists()

    def test_creates_parent_dirs_if_missing(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "nested" / "deep" / "state.json"
        save_state(fm, out)
        assert out.exists()

    def test_output_is_valid_json(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_all_top_level_keys_present(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        expected_keys = {
            "schema_version", "saved_at", "next_user_id", "next_ride_id",
            "users", "active_rides", "completed_rides", "vehicles", "degraded_repo",
        }
        assert expected_keys == set(data.keys())

    def test_schema_version_is_correct(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["schema_version"] == SCHEMA_VERSION

    def test_saved_at_is_iso_utc_string(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        saved_at = data["saved_at"]
        assert isinstance(saved_at, str)
        assert saved_at.endswith("Z")
        # Must parse without error
        datetime.strptime(saved_at, "%Y-%m-%dT%H:%M:%SZ")

    def test_overwrite_on_second_call(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        first = json.loads(out.read_text())
        fm.register_user("tok_new")
        save_state(fm, out)
        second = json.loads(out.read_text())
        assert len(second["users"]) == 1
        assert len(first["users"]) == 0


# ---------------------------------------------------------------------------
# next_user_id / next_ride_id counter tests
# ---------------------------------------------------------------------------

class TestCounters:
    def test_next_user_id_is_one_when_no_users(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["next_user_id"] == 1

    def test_next_user_id_exceeds_max_user(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        fm.register_user("tok_a")
        fm.register_user("tok_b")
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["next_user_id"] == 3

    def test_next_ride_id_is_one_when_no_rides(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["next_ride_id"] == 1

    def test_next_ride_id_exceeds_max_ride_id(self, tmp_path: Path):
        """Inject a completed ride directly and verify next_ride_id = max + 1."""
        fm = _minimal_fleet_manager()
        ride = Ride(
            ride_id=5,
            user_id=1,
            vehicle_id="V-001",
            start_time=datetime(2026, 3, 1, 10, 0, 0),
            start_station_id=1,
            end_time=datetime(2026, 3, 1, 10, 15, 0),
            end_station_id=1,
            price=15.0,
        )
        fm.completed_rides[5] = ride
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["next_ride_id"] == 6


# ---------------------------------------------------------------------------
# Users serialization tests
# ---------------------------------------------------------------------------

class TestUsersSerialisation:
    def test_empty_users(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["users"] == []

    def test_user_fields(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        fm.register_user("tok_xyz")
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["users"] == [{"user_id": 1, "payment_token": "tok_xyz"}]

    def test_users_sorted_by_user_id(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        fm.register_user("tok_a")
        fm.register_user("tok_b")
        fm.register_user("tok_c")
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        ids = [u["user_id"] for u in data["users"]]
        assert ids == sorted(ids)


# ---------------------------------------------------------------------------
# Active rides serialization tests
# ---------------------------------------------------------------------------

class TestActiveRidesSerialisation:
    def test_empty_active_rides(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["active_rides"] == []

    def test_active_ride_fields(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        ride = Ride(
            ride_id=1,
            user_id=1,
            vehicle_id="V-001",
            start_time=datetime(2026, 3, 10, 14, 20, 0),
            start_station_id=1,
        )
        fm.active_rides.add(ride)
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        r = data["active_rides"][0]
        assert r["ride_id"] == 1
        assert r["user_id"] == 1
        assert r["vehicle_id"] == "V-001"
        assert r["start_time"] == "2026-03-10T14:20:00Z"
        assert r["end_time"] is None
        assert r["end_station_id"] is None
        assert r["reported_degraded"] is False
        assert r["price"] is None

    def test_active_rides_sorted_by_ride_id(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        for i in [3, 1, 2]:
            fm.active_rides.add(Ride(
                ride_id=i,
                user_id=i,
                vehicle_id=f"V-00{i}",
                start_time=datetime(2026, 3, 10, 14, 0, 0),
                start_station_id=1,
            ))
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        ids = [r["ride_id"] for r in data["active_rides"]]
        assert ids == sorted(ids)


# ---------------------------------------------------------------------------
# Completed rides serialization tests
# ---------------------------------------------------------------------------

class TestCompletedRidesSerialisation:
    def test_empty_completed_rides(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["completed_rides"] == []

    def test_completed_ride_fields(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        ride = Ride(
            ride_id=7,
            user_id=1,
            vehicle_id="V-001",
            start_time=datetime(2026, 3, 10, 13, 0, 0),
            start_station_id=2,
            end_time=datetime(2026, 3, 10, 13, 18, 0),
            end_station_id=3,
            price=15.0,
        )
        fm.completed_rides[7] = ride
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        r = data["completed_rides"][0]
        assert r["ride_id"] == 7
        assert r["end_time"] == "2026-03-10T13:18:00Z"
        assert r["end_station_id"] == 3
        assert r["price"] == 15.0

    def test_degraded_ride_price_is_zero(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        ride = Ride(
            ride_id=2,
            user_id=1,
            vehicle_id="V-001",
            start_time=datetime(2026, 3, 10, 13, 0, 0),
            start_station_id=1,
            end_time=datetime(2026, 3, 10, 13, 10, 0),
            end_station_id=1,
            reported_degraded=True,
            price=0.0,
        )
        fm.completed_rides[2] = ride
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["completed_rides"][0]["price"] == 0.0


# ---------------------------------------------------------------------------
# Vehicles serialization tests
# ---------------------------------------------------------------------------

class TestVehiclesSerialisation:
    def test_bicycle_type_field(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["vehicles"][0]["type"] == "bicycle"

    def test_ebike_type_field(self, tmp_path: Path):
        ebike = EBike(
            vehicle_id="E-001",
            status=VehicleStatus.AVAILABLE,
            rides_since_last_treated=0,
            last_treated_date=date(2026, 1, 1),
            station_id=1,
            active_ride_id=None,
            charge_pct=80,
        )
        station = _make_station(1)
        fm = FleetManager(stations={1: station}, vehicles={"E-001": ebike})
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        v = data["vehicles"][0]
        assert v["type"] == "electric_bicycle"
        assert v["charge_pct"] == 80

    def test_scooter_type_and_charge(self, tmp_path: Path):
        scooter = _make_scooter("S-001", station_id=1, charge_pct=55)
        station = _make_station(1)
        fm = FleetManager(stations={1: station}, vehicles={"S-001": scooter})
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        v = data["vehicles"][0]
        assert v["type"] == "scooter"
        assert v["charge_pct"] == 55

    def test_bicycle_has_no_charge_pct(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert "charge_pct" not in data["vehicles"][0]

    def test_vehicle_fields(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        v = data["vehicles"][0]
        assert v["vehicle_id"] == "V-001"
        assert v["status"] == "available"
        assert v["rides_since_last_treated"] == 0
        assert v["last_treated_date"] == "2026-01-01"
        assert v["station_id"] == 1
        assert v["active_ride_id"] is None

    def test_in_ride_vehicle_has_null_station_id(self, tmp_path: Path):
        bike = _make_bicycle("V-001", station_id=None, active_ride_id=3)
        station = _make_station(1)
        fm = FleetManager.__new__(FleetManager)
        fm.users = {}
        fm.stations = {1: station}
        fm.vehicles = {"V-001": bike}
        fm.active_rides = ActiveRidesRegistry()
        fm.completed_rides = {}
        fm.degraded_repo = DegradedRepo(container_id=-1, _vehicle_ids=set(), name="Degraded Repo")
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["vehicles"][0]["station_id"] is None
        assert data["vehicles"][0]["active_ride_id"] == 3

    def test_vehicles_sorted_by_vehicle_id(self, tmp_path: Path):
        station = _make_station(1)
        vehicles = {
            "V-003": _make_bicycle("V-003"),
            "V-001": _make_bicycle("V-001"),
            "V-002": _make_bicycle("V-002"),
        }
        fm = FleetManager(stations={1: station}, vehicles=vehicles)
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        ids = [v["vehicle_id"] for v in data["vehicles"]]
        assert ids == sorted(ids)


# ---------------------------------------------------------------------------
# Degraded repo serialization tests
# ---------------------------------------------------------------------------

class TestDegradedRepoSerialisation:
    def test_empty_degraded_repo(self, tmp_path: Path):
        fm = _minimal_fleet_manager()
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["degraded_repo"] == []

    def test_degraded_repo_contains_degraded_vehicle_ids(self, tmp_path: Path):
        bike = _make_bicycle("V-001", station_id=None, status=VehicleStatus.DEGRADED, rides=11)
        station = _make_station(1)
        degraded = DegradedRepo(container_id=-1, _vehicle_ids={"V-001"}, name="Degraded Repo")
        fm = FleetManager(
            stations={1: station},
            vehicles={"V-001": bike},
            degraded_repo=degraded,
        )
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["degraded_repo"] == ["V-001"]

    def test_degraded_repo_is_sorted(self, tmp_path: Path):
        station = _make_station(1)
        degraded = DegradedRepo(
            container_id=-1,
            _vehicle_ids={"V-003", "V-001", "V-002"},
            name="Degraded Repo",
        )
        bikes = {
            vid: _make_bicycle(vid, station_id=None, status=VehicleStatus.DEGRADED, rides=11)
            for vid in ["V-001", "V-002", "V-003"]
        }
        fm = FleetManager(
            stations={1: station},
            vehicles=bikes,
            degraded_repo=degraded,
        )
        out = tmp_path / "state.json"
        save_state(fm, out)
        data = json.loads(out.read_text())
        assert data["degraded_repo"] == sorted(data["degraded_repo"])
