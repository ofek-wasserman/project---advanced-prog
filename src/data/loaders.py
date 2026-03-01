from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.domain.VehicleContainer import Station


class DataLoader(ABC):
    """Abstract base for CSV loaders"""

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
        pass


class StationDataLoader(DataLoader):
    """Loads stations.csv -> dict[int, Station]"""

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
