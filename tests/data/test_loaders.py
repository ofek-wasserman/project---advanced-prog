import csv
from datetime import date
from pathlib import Path

import pytest

from src.data.loaders import StationDataLoader, VehicleDataLoader

# ── helpers ──────────────────────────────────────────────────────────────────

def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


STATION_ROWS = [
    {"station_id": "1", "name": "Dizengoff Sq", "lat": "32.0796", "lon": "34.7739", "max_capacity": "10"},
    {"station_id": "2", "name": "Central Bus Station", "lat": "32.0577", "lon": "34.7799", "max_capacity": "15"},
]

VEHICLE_ROWS = [
    {"vehicle_id": "V001", "type": "BICYCLE", "status": "AVAILABLE",
     "rides_since_last_treated": "2", "last_treated_date": "2026-02-01",
     "station_id": "1", "charge_pct": ""},
    {"vehicle_id": "V006", "type": "E_BIKE", "status": "AVAILABLE",
     "rides_since_last_treated": "1", "last_treated_date": "2026-02-18",
     "station_id": "1", "charge_pct": "85"},
]


# ── StationDataLoader ─────────────────────────────────────────────────────────

class TestStationDataLoader:

    def test_loads_correct_number_of_stations(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        write_csv(csv_file, STATION_ROWS)
        result = StationDataLoader(csv_file).create_objects()
        assert len(result) == 2

    def test_keys_are_ints(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        write_csv(csv_file, STATION_ROWS)
        result = StationDataLoader(csv_file).create_objects()
        assert all(isinstance(k, int) for k in result)

    def test_lat_lon_are_floats(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        write_csv(csv_file, STATION_ROWS)
        station = StationDataLoader(csv_file).create_objects()[1]
        assert isinstance(station["lat"], float)
        assert isinstance(station["lon"], float)

    def test_max_capacity_is_int(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        write_csv(csv_file, STATION_ROWS)
        station = StationDataLoader(csv_file).create_objects()[1]
        assert isinstance(station["max_capacity"], int)
        assert station["max_capacity"] == 10

    def test_name_is_stripped(self, tmp_path):
        rows = [{"station_id": "1", "name": "  Central  ", "lat": "32.0", "lon": "34.0", "max_capacity": "5"}]
        csv_file = tmp_path / "stations.csv"
        write_csv(csv_file, rows)
        station = StationDataLoader(csv_file).create_objects()[1]
        assert station["name"] == "Central"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            StationDataLoader(tmp_path / "nonexistent.csv").create_objects()


# ── VehicleDataLoader ─────────────────────────────────────────────────────────

class TestVehicleDataLoader:

    def test_loads_correct_number_of_vehicles(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        write_csv(csv_file, VEHICLE_ROWS)
        result = VehicleDataLoader(csv_file).create_objects()
        assert len(result) == 2

    def test_keys_are_strings(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        write_csv(csv_file, VEHICLE_ROWS)
        result = VehicleDataLoader(csv_file).create_objects()
        assert all(isinstance(k, str) for k in result)

    def test_bicycle_charge_pct_is_none(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        write_csv(csv_file, VEHICLE_ROWS)
        bicycle = VehicleDataLoader(csv_file).create_objects()["V001"]
        assert bicycle["charge_pct"] is None

    def test_ebike_charge_pct_is_int(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        write_csv(csv_file, VEHICLE_ROWS)
        ebike = VehicleDataLoader(csv_file).create_objects()["V006"]
        assert ebike["charge_pct"] == 85

    def test_last_treated_date_is_date_object(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        write_csv(csv_file, VEHICLE_ROWS)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V001"]
        assert isinstance(vehicle["last_treated_date"], date)
        assert vehicle["last_treated_date"] == date(2026, 2, 1)

    def test_rides_since_last_treated_is_int(self, tmp_path):
        csv_file = tmp_path / "vehicles.csv"
        write_csv(csv_file, VEHICLE_ROWS)
        vehicle = VehicleDataLoader(csv_file).create_objects()["V001"]
        assert isinstance(vehicle["rides_since_last_treated"], int)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VehicleDataLoader(tmp_path / "nonexistent.csv").create_objects()
