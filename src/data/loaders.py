from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any


class DataLoader(ABC):
    """Abstract base for CSV loaders. Subclasses implement _parse_row."""

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    def create_objects(self) -> dict[Any, Any]:
        rows = self._load_rows()
        return dict(self._parse_row(row) for row in rows)

    def _load_rows(self) -> list[dict[str, str]]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    @abstractmethod
    def _parse_row(self, row: dict[str, str]) -> tuple[Any, Any]:
        """Return (primary_key, domain_object) for a single CSV row."""


class StationDataLoader(DataLoader):
    """Loads stations.csv → dict[int, dict].

    CSV columns: station_id, name, lat, lon, max_capacity.
    Keys are ``int`` station IDs.
    TODO: return Station domain objects once Role 4 domain layer is ready.
    """

    def _parse_row(self, row: dict[str, str]) -> tuple[int, dict]:
        """Parse one CSV row into (station_id: int, station_data: dict)."""
        station_id = int(row["station_id"])
        data = {
            "station_id": station_id,
            "name": row["name"].strip(),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "max_capacity": int(row["max_capacity"]),
        }
        return station_id, data


class VehicleDataLoader(DataLoader):
    """Loads vehicles.csv → dict[str, Vehicle].

    charge_pct is blank in the CSV for Bicycle rows (non-electric).
    """

    def _parse_row(self, row: dict[str, str]) -> tuple[str, dict]:
        vehicle_id = row["vehicle_id"].strip()
        charge_raw = row.get("charge_pct", "").strip()

        data = {
            "vehicle_id": vehicle_id,
            "type": row["type"].strip(),
            "status": row["status"].strip(),
            "rides_since_last_treated": int(row["rides_since_last_treated"]),
            "last_treated_date": date.fromisoformat(row["last_treated_date"]),
            "station_id": int(row["station_id"]),
            "charge_pct": int(charge_raw) if charge_raw else None,
        }
        # TODO: return vehicle_id, <Vehicle subclass>(**data)  once domain models are ready
        return vehicle_id, data
