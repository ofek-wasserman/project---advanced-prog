from __future__ import annotations

from pathlib import Path

from src.data.loaders import StationDataLoader, VehicleDataLoader
from src.domain.Vehicle import Vehicle
from src.domain.VehicleContainer import Station


class FleetManager:
    """
    Central registry that owns all stations and vehicles.

    Bootstrapped at startup from two CSV files via :meth:`from_csv`.
    After construction every station's ``_vehicle_ids`` set already
    contains the IDs of its initially docked vehicles.
    """

    def __init__(
        self,
        stations: dict[int, Station],
        vehicles: dict[str, Vehicle],
    ) -> None:
        self.stations = stations
        self.vehicles = vehicles
        self._link_vehicles_to_stations()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_csv(
        cls,
        stations_csv: str | Path,
        vehicles_csv: str | Path,
    ) -> "FleetManager":
        """Bootstrap a FleetManager by loading both CSV files.

        Args:
            stations_csv: Path to ``stations.csv``.
            vehicles_csv: Path to ``vehicles.csv``.

        Returns:
            A fully initialised :class:`FleetManager` with vehicles
            already linked to their docking stations.
        """
        stations: dict[int, Station] = StationDataLoader(stations_csv).create_objects()
        vehicles: dict[str, Vehicle] = VehicleDataLoader(vehicles_csv).create_objects()
        return cls(stations=stations, vehicles=vehicles)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_station(self, station_id: int) -> Station | None:
        """Return the station with *station_id*, or ``None`` if absent."""
        return self.stations.get(station_id)

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        """Return the vehicle with *vehicle_id*, or ``None`` if absent."""
        return self.vehicles.get(vehicle_id)

    def vehicles_at_station(self, station_id: int) -> list[Vehicle]:
        """Return all vehicle objects currently docked at *station_id*."""
        station = self.stations.get(station_id)
        if station is None:
            return []
        return [
            self.vehicles[vid]
            for vid in station.get_vehicle_ids()
            if vid in self.vehicles
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _link_vehicles_to_stations(self) -> None:
        """Populate each station's vehicle-ID set from the loaded vehicles."""
        for vehicle in self.vehicles.values():
            sid = vehicle.station_id
            if sid is not None and sid in self.stations:
                self.stations[sid].add_vehicle(vehicle.vehicle_id)
