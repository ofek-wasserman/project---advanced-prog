"""Tests for FleetManager — KAN-52.

Covers:
- Bootstrap via from_csv (station + vehicle counts, types)
- Automatic vehicle → station linking
- get_station / get_vehicle / vehicles_at_station queries
- Orphan vehicle (station_id not in loaded stations)
- Missing CSV raises FileNotFoundError
- Empty CSVs produce empty collections
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.domain.Vehicle import Bicycle, EBike, Scooter
from src.domain.VehicleContainer import Station
from src.services.fleet_manager import FleetManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATIONS_HEADER = "station_id,name,lat,lon,max_capacity\n"
VEHICLES_HEADER = "vehicle_id,station_id,vehicle_type,status,rides_since_last_treated,last_treated_date\n"


def _write_stations(tmp_path: Path, rows: list[str]) -> Path:
    p = tmp_path / "stations.csv"
    p.write_text(STATIONS_HEADER + "".join(rows), encoding="utf-8")
    return p


def _write_vehicles(tmp_path: Path, rows: list[str]) -> Path:
    p = tmp_path / "vehicles.csv"
    p.write_text(VEHICLES_HEADER + "".join(rows), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Group 1 — from_csv basics
# ---------------------------------------------------------------------------

class TestFromCsvBasics:
    def test_loads_correct_station_count(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, [
            "1,Alpha,32.0,34.8,10\n",
            "2,Beta,32.1,34.9,5\n",
        ])
        v = _write_vehicles(tmp_path, [])
        fm = FleetManager.from_csv(s, v)
        assert len(fm.stations) == 2

    def test_loads_correct_vehicle_count(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [
            "V001,1,bicycle,available,3,2025-01-01\n",
            "V002,1,scooter,available,0,2025-02-01\n",
        ])
        fm = FleetManager.from_csv(s, v)
        assert len(fm.vehicles) == 2

    def test_stations_are_station_objects(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [])
        fm = FleetManager.from_csv(s, v)
        assert isinstance(fm.stations[1], Station)

    def test_bicycle_vehicle_type(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, ["V001,1,bicycle,available,3,2025-01-01\n"])
        fm = FleetManager.from_csv(s, v)
        assert isinstance(fm.vehicles["V001"], Bicycle)

    def test_scooter_vehicle_type(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, ["V002,1,scooter,available,0,2025-02-01\n"])
        fm = FleetManager.from_csv(s, v)
        assert isinstance(fm.vehicles["V002"], Scooter)

    def test_ebike_vehicle_type(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [
            "V003,1,electric_bicycle,available,1,2025-03-01\n"
        ])
        fm = FleetManager.from_csv(s, v)
        assert isinstance(fm.vehicles["V003"], EBike)


# ---------------------------------------------------------------------------
# Group 2 — vehicle-station linking
# ---------------------------------------------------------------------------

class TestVehicleStationLinking:
    def test_docked_vehicle_appears_in_station(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, ["V001,1,bicycle,available,0,2025-01-01\n"])
        fm = FleetManager.from_csv(s, v)
        assert fm.stations[1].contains_vehicle("V001")

    def test_station_vehicle_count_matches(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [
            "V001,1,bicycle,available,0,2025-01-01\n",
            "V002,1,scooter,available,0,2025-01-02\n",
        ])
        fm = FleetManager.from_csv(s, v)
        assert fm.stations[1].count() == 2

    def test_vehicles_spread_across_stations(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, [
            "1,Alpha,32.0,34.8,10\n",
            "2,Beta,32.1,34.9,5\n",
        ])
        v = _write_vehicles(tmp_path, [
            "V001,1,bicycle,available,0,2025-01-01\n",
            "V002,2,scooter,available,0,2025-01-02\n",
        ])
        fm = FleetManager.from_csv(s, v)
        assert fm.stations[1].count() == 1
        assert fm.stations[2].count() == 1

    def test_orphan_vehicle_does_not_crash(self, tmp_path: Path) -> None:
        """A vehicle whose station_id is not in the loaded stations is ignored."""
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [
            "V999,999,bicycle,available,0,2025-01-01\n"  # station 999 absent
        ])
        fm = FleetManager.from_csv(s, v)
        assert "V999" in fm.vehicles          # vehicle loaded
        assert fm.stations[1].count() == 0   # station 1 untouched

    def test_empty_station_has_zero_vehicles(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [])
        fm = FleetManager.from_csv(s, v)
        assert fm.stations[1].count() == 0


# ---------------------------------------------------------------------------
# Group 3 — queries
# ---------------------------------------------------------------------------

class TestFleetManagerQueries:
    @pytest.fixture()
    def fm(self, tmp_path: Path) -> FleetManager:
        s = _write_stations(tmp_path, [
            "1,Alpha,32.0,34.8,10\n",
            "2,Beta,32.1,34.9,5\n",
        ])
        v = _write_vehicles(tmp_path, [
            "V001,1,bicycle,available,3,2025-01-01\n",
            "V002,1,scooter,available,0,2025-02-01\n",
            "V003,2,electric_bicycle,available,1,2025-03-01\n",
        ])
        return FleetManager.from_csv(s, v)

    def test_get_station_returns_correct_station(self, fm: FleetManager) -> None:
        station = fm.get_station(1)
        assert station is not None
        assert station.name == "Alpha"

    def test_get_station_missing_returns_none(self, fm: FleetManager) -> None:
        assert fm.get_station(99) is None

    def test_get_vehicle_returns_correct_vehicle(self, fm: FleetManager) -> None:
        vehicle = fm.get_vehicle("V001")
        assert vehicle is not None
        assert vehicle.vehicle_id == "V001"

    def test_get_vehicle_missing_returns_none(self, fm: FleetManager) -> None:
        assert fm.get_vehicle("MISSING") is None

    def test_vehicles_at_station_count(self, fm: FleetManager) -> None:
        assert len(fm.vehicles_at_station(1)) == 2

    def test_vehicles_at_station_correct_objects(self, fm: FleetManager) -> None:
        ids = {v.vehicle_id for v in fm.vehicles_at_station(1)}
        assert ids == {"V001", "V002"}

    def test_vehicles_at_missing_station_returns_empty(self, fm: FleetManager) -> None:
        assert fm.vehicles_at_station(99) == []


# ---------------------------------------------------------------------------
# Group 4 — error handling & edge cases
# ---------------------------------------------------------------------------

class TestFleetManagerEdgeCases:
    def test_missing_stations_csv_raises(self, tmp_path: Path) -> None:
        v = _write_vehicles(tmp_path, [])
        with pytest.raises(FileNotFoundError):
            FleetManager.from_csv(tmp_path / "no_stations.csv", v)

    def test_missing_vehicles_csv_raises(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        with pytest.raises(FileNotFoundError):
            FleetManager.from_csv(s, tmp_path / "no_vehicles.csv")

    def test_empty_csvs_produce_empty_fleet(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, [])
        v = _write_vehicles(tmp_path, [])
        fm = FleetManager.from_csv(s, v)
        assert fm.stations == {}
        assert fm.vehicles == {}

    def test_unknown_vehicle_type_raises(self, tmp_path: Path) -> None:
        s = _write_stations(tmp_path, ["1,Alpha,32.0,34.8,10\n"])
        v = _write_vehicles(tmp_path, [
            "V001,1,hoverboard,available,0,2025-01-01\n"
        ])
        with pytest.raises(ValueError, match="Unknown vehicle type"):
            FleetManager.from_csv(s, v)
"""Tests for FleetManager (orchestration skeleton + DI + in-memory state)."""

from unittest.mock import MagicMock

from src.domain.VehicleContainer import DegradedRepo
from src.services.active_rides import ActiveRidesRegistry
from src.services.billing import BillingService
from src.services.fleet_manager import FleetManager


class TestFleetManager:
    def test_initial_state(self):
        stations = {1: MagicMock(), 2: MagicMock()}
        vehicles = {10: MagicMock(), 11: MagicMock()}

        fm = FleetManager(stations=stations, vehicles=vehicles)

        assert fm.stations is stations
        assert fm.vehicles is vehicles
        assert fm.users == {}

    def test_uses_injected_dependencies(self):
        stations = {1: MagicMock()}
        vehicles = {10: MagicMock()}

        active = ActiveRidesRegistry()
        repo = DegradedRepo(container_id=-1,_vehicle_ids=set(),name="Degraded Repo")
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
        vehicles = {10: MagicMock()}

        fm1 = FleetManager(stations=stations, vehicles=vehicles)
        fm2 = FleetManager(stations=stations, vehicles=vehicles)

        # Proves you avoided the "mutable default args" trap
        assert fm1.active_rides is not fm2.active_rides
        assert fm1.degraded_repo is not fm2.degraded_repo
        assert fm1.billing_service is not fm2.billing_service
