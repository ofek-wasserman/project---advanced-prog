from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any

from src.domain.enums import VehicleStatus
from src.domain.Vehicle import Bicycle, EBike, Scooter, Vehicle
from src.domain.VehicleContainer import Station


class DataLoader(ABC):
    """Abstract base for CSV loaders"""

    REQUIRED_COLUMNS: frozenset[str] = frozenset()

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    def create_objects(self) -> dict[Any, Any]:
        rows = self._load_rows()
        return dict(self._parse_row(row) for row in rows)

    def _load_rows(self) -> list[dict[str, str]]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            self._validate_columns(set(reader.fieldnames or []))
            return rows

    def _validate_columns(self, present: set[str]) -> None:
        missing = self.REQUIRED_COLUMNS - present
        if missing:
            raise ValueError(
                f"{self.__class__.__name__}: missing required columns: {sorted(missing)}"
            )

    @abstractmethod
    def _parse_row(self, row: dict[str, str]) -> tuple[Any, Any]:
        pass


class StationDataLoader(DataLoader):
    """Loads stations.csv -> dict[int, Station]"""

    REQUIRED_COLUMNS = frozenset({"station_id", "name", "lat", "lon", "max_capacity"})

    def _parse_row(self, row: dict[str, str]) -> tuple[int, Station]:
        station_id = int(row["station_id"])
        station = Station(
            container_id=station_id,
            _vehicle_ids=set(),
            name=row["name"].strip(),
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            max_capacity=int(row["max_capacity"]),
        )
        return station_id, station


class VehicleDataLoader(DataLoader):
    """Loads vehicles.csv -> dict[str, Vehicle]"""

    def _parse_row(self, row: dict[str, str]) -> tuple[str, Vehicle]:
        vehicle_id = row["vehicle_id"].strip()
        vehicle_type = row["vehicle_type"].strip()
        status = VehicleStatus(row["status"].strip())
        rides = int(row["rides_since_last_treated"])
        last_treated = date.fromisoformat(row["last_treated_date"])
        station_id = int(row["station_id"])

        if vehicle_type == "bicycle":
            vehicle = Bicycle(
                vehicle_id=vehicle_id,
                status=status,
                rides_since_last_treated=rides,
                last_treated_date=last_treated,
                station_id=station_id,
                active_ride_id=None,
            )
        elif vehicle_type == "electric_bicycle":
            vehicle = EBike(
                vehicle_id=vehicle_id,
                status=status,
                rides_since_last_treated=rides,
                last_treated_date=last_treated,
                station_id=station_id,
                active_ride_id=None,
                charge_pct=100,
            )
        elif vehicle_type == "scooter":
            vehicle = Scooter(
                vehicle_id=vehicle_id,
                status=status,
                rides_since_last_treated=rides,
                last_treated_date=last_treated,
                station_id=station_id,
                active_ride_id=None,
                charge_pct=100,
            )
        else:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")

        return vehicle_id, vehicle
