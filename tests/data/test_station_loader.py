"""Tests for KAN-30 Station loader"""

import csv
from pathlib import Path

import pytest

from src.data.loaders import StationDataLoader
from src.domain.VehicleContainer import Station

STATION_ROWS = [
    {
        "station_id": "1001",
        "name": "Dizengoff Sq",
        "lat": "32.0796",
        "lon": "34.7739",
        "max_capacity": "10",
    },
    {
        "station_id": "1002",
        "name": "  Central Bus Station  ",
        "lat": "32.0577",
        "lon": "34.7799",
        "max_capacity": "15",
    },
]


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


class TestStationDataLoader:
    def test_loads_correct_count(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, STATION_ROWS)
        result = StationDataLoader(csv_file).create_objects()
        assert len(result) == 2

    def test_keys_are_ints(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, STATION_ROWS)
        result = StationDataLoader(csv_file).create_objects()
        assert all(isinstance(k, int) for k in result)

    def test_values_are_station_objects(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, STATION_ROWS)
        result = StationDataLoader(csv_file).create_objects()
        assert all(isinstance(v, Station) for v in result.values())

    def test_lat_lon_are_floats(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, STATION_ROWS)
        station = StationDataLoader(csv_file).create_objects()[1001]
        assert isinstance(station, Station)
        assert isinstance(station.lat, float)
        assert isinstance(station.lon, float)

    def test_max_capacity_is_int(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, STATION_ROWS)
        station = StationDataLoader(csv_file).create_objects()[1001]
        assert isinstance(station, Station)
        assert isinstance(station.max_capacity, int)
        assert station.max_capacity == 10

    def test_name_is_stripped(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, STATION_ROWS)
        station = StationDataLoader(csv_file).create_objects()[1002]
        assert isinstance(station, Station)
        assert station.name == "Central Bus Station"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            StationDataLoader(tmp_path / "missing.csv").create_objects()
