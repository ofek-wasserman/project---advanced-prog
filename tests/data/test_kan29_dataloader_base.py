"""Unit tests for KAN-29 — DataLoader abstract base class."""
import csv
from pathlib import Path

import pytest

from src.data.loaders import DataLoader

# ── minimal concrete subclass ────────────────────────────────────────────────

class _IntLoader(DataLoader):
    """Toy loader: CSV must have columns 'id' and 'val'."""

    def _parse_row(self, row: dict[str, str]) -> tuple[int, str]:
        return int(row["id"]), row["val"]


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ── tests ────────────────────────────────────────────────────────────────────

class TestDataLoaderBase:

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            DataLoader("any.csv")  # type: ignore[abstract]

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _IntLoader(tmp_path / "missing.csv").create_objects()

    def test_returns_dict(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        _write_csv(csv_file, [{"id": "1", "val": "hello"}, {"id": "2", "val": "world"}])
        result = _IntLoader(csv_file).create_objects()
        assert isinstance(result, dict)

    def test_keys_from_parse_row(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        _write_csv(csv_file, [{"id": "10", "val": "a"}])
        result = _IntLoader(csv_file).create_objects()
        assert 10 in result
        assert result[10] == "a"

    def test_all_rows_loaded(self, tmp_path):
        rows = [{"id": str(i), "val": f"v{i}"} for i in range(5)]
        csv_file = tmp_path / "data.csv"
        _write_csv(csv_file, rows)
        result = _IntLoader(csv_file).create_objects()
        assert len(result) == 5
