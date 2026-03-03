from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.data.loaders import StationDataLoader, VehicleDataLoader
from src.domain.user import User
from src.domain.Vehicle import Vehicle
from src.domain.VehicleContainer import DegradedRepo, Station
from src.services.active_rides import ActiveRidesRegistry
from src.services.billing import BillingService


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
        active_rides: Optional[ActiveRidesRegistry] = None,
        degraded_repo: Optional[DegradedRepo] = None,
        billing_service: Optional[BillingService] = None,
    ) -> None:
        self.users: dict[int, User] = {}
        self.stations = stations
        self.vehicles = vehicles
        self.active_rides = active_rides or ActiveRidesRegistry()
        self.degraded_repo = degraded_repo or DegradedRepo(
            container_id=-1, _vehicle_ids=set(), name="Degraded Repo"
        )
        self.billing_service = billing_service or BillingService()
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

    # ------------------------------------------------------------------
    # Business methods (stubs — implemented in later tickets)
    # ------------------------------------------------------------------

    def register_user(self, payment_token: str) -> User:
        """
        Registers a new user and generates a unique user_id.

        Args:
            payment_token: The payment token for the user.

        Returns:
            The newly created User object.
        """
        raise NotImplementedError("KAN-21: Implement FleetManager Class")

    def start_ride(self, user_id: int, location: tuple[float, float]) -> dict:
        """
        Start a ride for a user with a specific vehicle.

        Args:
            user_id: The unique identifier for the user.
            location: The (latitude, longitude) of the user.

        Returns:
            Ride info dict plus (lat, lon) of the start station.
        """
        raise NotImplementedError("KAN-21: Implement FleetManager Class")

    def end_ride(self, ride_id: int, location: tuple[float, float]) -> dict:
        """
        End a ride for a user with a specific vehicle.

        Args:
            ride_id: The unique identifier for the ride.
            location: The (latitude, longitude) where the ride ended.

        Returns:
            End-station location and payment info.
        """
        raise NotImplementedError("KAN-21: Implement FleetManager Class")

    def _generate_ride_id(self) -> int:
        """Generates a new unique ride ID."""
        raise NotImplementedError("KAN-21: Implement FleetManager Class")

    def _nearest_station_with_free_slot(
        self, location: tuple[float, float]
    ) -> Optional[Station]:
        """Find the nearest station with a free slot for parking."""
        raise NotImplementedError("KAN-21: Implement FleetManager Class")

    def _nearest_station_with_available_vehicle(
        self, location: tuple[float, float]
    ) -> Optional[Station]:
        """Find the nearest station with at least one available vehicle."""
        raise NotImplementedError("KAN-21: Implement FleetManager Class")
