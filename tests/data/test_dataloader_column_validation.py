"""Tests for required CSV column validation in DataLoader (KAN-67)"""

import csv
from pathlib import Path

import pytest

from src.data.loaders import StationDataLoader

VALID_COLUMNS = ["station_id", "name", "lat", "lon", "max_capacity"]

VALID_ROW = {
    "station_id": "1",
    "name": "Test Station",
    "lat": "32.08",
    "lon": "34.78",
    "max_capacity": "10",
}


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidCsv:
    def test_all_required_columns_present_loads_successfully(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, VALID_COLUMNS, [VALID_ROW])
        result = StationDataLoader(csv_file).create_objects()
        assert len(result) == 1

    def test_extra_columns_beyond_required_are_allowed(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, VALID_COLUMNS + ["extra_col"], [{**VALID_ROW, "extra_col": "x"}])
        result = StationDataLoader(csv_file).create_objects()
        assert len(result) == 1

    def test_empty_csv_with_valid_headers_returns_empty_dict(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, VALID_COLUMNS, [])
        result = StationDataLoader(csv_file).create_objects()
        assert result == {}


# ---------------------------------------------------------------------------
# Missing columns → ValueError
# ---------------------------------------------------------------------------


class TestMissingColumns:
    @pytest.mark.parametrize("missing_col", VALID_COLUMNS)
    def test_raises_value_error_when_single_column_missing(self, tmp_path, missing_col):
        columns = [c for c in VALID_COLUMNS if c != missing_col]
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, columns, [])
        with pytest.raises(ValueError):
            StationDataLoader(csv_file).create_objects()

    def test_raises_value_error_when_multiple_columns_missing(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, ["station_id"], [])
        with pytest.raises(ValueError):
            StationDataLoader(csv_file).create_objects()

    def test_error_message_names_the_missing_column(self, tmp_path):
        columns = [c for c in VALID_COLUMNS if c != "lat"]
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, columns, [])
        with pytest.raises(ValueError, match="lat"):
            StationDataLoader(csv_file).create_objects()

    def test_error_message_names_all_missing_columns(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        _write_csv(csv_file, ["station_id"], [])
        with pytest.raises(ValueError, match="lat"):
            StationDataLoader(csv_file).create_objects()

    def test_completely_empty_header_raises_value_error(self, tmp_path):
        csv_file = tmp_path / "stations.csv"
        csv_file.write_text("")
        with pytest.raises(ValueError):
            StationDataLoader(csv_file).create_objects()


# ---------------------------------------------------------------------------
# Missing file still raises FileNotFoundError (not affected by this change)
# ---------------------------------------------------------------------------


class TestMissingFile:
    def test_raises_file_not_found_error_when_file_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            StationDataLoader(tmp_path / "nonexistent.csv").create_objects()
