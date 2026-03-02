"""Tests for KAN-31 Vehicle loader"""

import csv
from datetime import date
from pathlib import Path

import pytest

from src.data.loaders import VehicleDataLoader
from src.domain.enums import VehicleStatus
from src.domain.Vehicle import Bicycle, EBike, Scooter

VEHICLE_ROWS = [
    {
        "vehicle_id": "V001",
        "vehicle_type": "bicycle",
        "status": "available",
        "rides_since_last_treated": "3",
        "last_treated_date": "2025-01-16",
        "station_id": "1",
    },
    {
        "vehicle_id": "V002",
        "vehicle_type": "electric_bicycle",
        "status": "available",
        "rides_since_last_treated": "0",
        "last_treated_date": "2025-03-28",
        "station_id": "1",
    },
]


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


class TestVehicleDataLoader:
    def test_loads_correct_count(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        _write_csv(csv_file, VEHICLE_ROWS)
        result = VehicleDataLoader(csv_file).create_objects()
        assert len(result) == 2

    def test_keys_are_strings(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        _write_csv(csv_file, VEHICLE_ROWS)
        result = VehicleDataLoader(csv_file).create_objects()
        assert all(isinstance(k, str) for k in result)

    def test_bicycle_type(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        _write_csv(csv_file, VEHICLE_ROWS)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V001"]
        assert isinstance(vehicle, Bicycle)

    def test_ebike_type(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        _write_csv(csv_file, VEHICLE_ROWS)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V002"]
        assert isinstance(vehicle, EBike)
        assert vehicle.charge_pct == 100

    def test_status_enum(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        _write_csv(csv_file, VEHICLE_ROWS)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V001"]
        assert vehicle.status == VehicleStatus.AVAILABLE

    def test_date_parsing(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        _write_csv(csv_file, VEHICLE_ROWS)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V001"]
        assert isinstance(vehicle.last_treated_date, date)
        assert vehicle.last_treated_date == date(2025, 1, 16)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VehicleDataLoader(tmp_path / "missing.csv").create_objects()
    def test_scooter_type(self, tmp_path):
        scooter_row = [
            {
                "vehicle_id": "V003",
                "vehicle_type": "scooter",
                "status": "available",
                "rides_since_last_treated": "2",
                "last_treated_date": "2025-06-01",
                "station_id": "2",
            }
        ]
        csv_file = tmp_path / "scooters.csv"
        _write_csv(csv_file, scooter_row)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V003"]
        assert isinstance(vehicle, Scooter)
        assert vehicle.charge_pct == 100

    def test_unknown_vehicle_type_raises(self, tmp_path):
        bad_row = [
            {
                "vehicle_id": "V999",
                "vehicle_type": "hoverboard",
                "status": "available",
                "rides_since_last_treated": "0",
                "last_treated_date": "2025-01-01",
                "station_id": "1",
            }
        ]
        csv_file = tmp_path / "bad.csv"
        _write_csv(csv_file, bad_row)
        with pytest.raises(ValueError, match="Unknown vehicle type"):
            VehicleDataLoader(csv_file).create_objects()
