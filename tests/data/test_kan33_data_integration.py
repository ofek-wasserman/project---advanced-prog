"""Tests for KAN-33 data layer."""

from datetime import date

import pytest

from src.data.loaders import DataLoader, StationDataLoader, VehicleDataLoader


class TestRealCSVLoading:

    def test_load_stations(self):
        loader = StationDataLoader("data/stations.csv")
        stations = loader.create_objects()
        assert len(stations) > 0
        assert all(isinstance(k, int) for k in stations.keys())
        first = next(iter(stations.values()))
        assert isinstance(first.lat, float)
        assert isinstance(first.max_capacity, int)

    def test_load_vehicles(self):
        loader = VehicleDataLoader("data/vehicles.csv")
        vehicles = loader.create_objects()
        assert len(vehicles) > 0
        first = next(iter(vehicles.values()))
        assert isinstance(first.last_treated_date, date)

    def test_multiple_vehicle_types(self):
        vehicles = VehicleDataLoader("data/vehicles.csv").create_objects()
        types = set(type(v).__name__ for v in vehicles.values())
        assert len(types) >= 2

    def test_valid_station_refs(self):
        stations = StationDataLoader("data/stations.csv").create_objects()
        vehicles = VehicleDataLoader("data/vehicles.csv").create_objects()
        station_ids = set(stations.keys())
        for v in vehicles.values():
            assert v.station_id in station_ids


class TestErrors:

    def test_missing_file(self, tmp_path):
        loader = StationDataLoader(tmp_path / "nope.csv")
        with pytest.raises(FileNotFoundError):
            loader.create_objects()

    def test_bad_int(self, tmp_path):
        f = tmp_path / "bad.csv"
        f.write_text("station_id,name,lat,lon,max_capacity\nnot_int,x,1.0,2.0,5\n")
        with pytest.raises(ValueError):
            StationDataLoader(f).create_objects()

    def test_bad_date(self, tmp_path):
        f = tmp_path / "bad.csv"
        f.write_text(
            "vehicle_id,vehicle_type,status,rides_since_last_treated,last_treated_date,station_id\n"
            "V1,bicycle,available,1,bad,1\n"
        )
        with pytest.raises(ValueError):
            VehicleDataLoader(f).create_objects()


class TestEdgeCases:

    def test_whitespace_stripped(self, tmp_path):
        f = tmp_path / "s.csv"
        f.write_text("station_id,name,lat,lon,max_capacity\n1,  Test  ,1.0,2.0,5\n")
        result = StationDataLoader(f).create_objects()
        assert result[1].name == "Test"

    def test_empty_csv(self, tmp_path):
        f = tmp_path / "e.csv"
        f.write_text("station_id,name,lat,lon,max_capacity\n")
        assert StationDataLoader(f).create_objects() == {}

    def test_multiple_stations(self, tmp_path):
        f = tmp_path / "s.csv"
        f.write_text(
            "station_id,name,lat,lon,max_capacity\n"
            "1,A,1.0,2.0,5\n"
            "2,B,3.0,4.0,10\n"
        )
        result = StationDataLoader(f).create_objects()
        assert len(result) == 2
        assert result[1].name == "A"
        assert result[2].name == "B"


class TestAbstractLoader:

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            DataLoader("x.csv")

    def test_custom_loader(self, tmp_path):
        class Custom(DataLoader):
            def _parse_row(self, row):
                return int(row["id"]), {"val": row["data"]}

        f = tmp_path / "c.csv"
        f.write_text("id,data\n1,test\n")
        result = Custom(f).create_objects()
        assert result[1] == {"val": "test"}
