class VehicleContainer:
    """
    Generic container for grouping vehicles by ID.

    This class does NOT store Vehicle objects directly.
    It stores vehicle IDs (str) to avoid cross-layer coupling
    and to keep the Domain layer lightweight.

    Used as a base abstraction for:
    - Station
    - DegradedRepo

    Responsibilities:
    - Maintain a unique collection of vehicle IDs
    - Provide basic add/remove/query operations

    Does NOT enforce business rules (e.g., capacity limits).
    """

    def __init__(
        self,
        container_id: int,
        _vehicle_ids: set[str],
        name: str
    ):
        """
        Initialize container with:
        - Unique identifier
        - Initial set of vehicle IDs
        - Human-readable name

        Invariant:
        - _vehicle_ids must remain a set (no duplicates).
        """
        self.container_id = container_id
        self._vehicle_ids = _vehicle_ids
        self.name = name

    def add_vehicle(self, vehicle_id: str) -> None:
        """
        Add a vehicle ID to the container.

        Since underlying structure is a set:
        - Duplicate IDs are automatically ignored.
        """
        self._vehicle_ids.add(vehicle_id)

    def remove_vehicle(self, vehicle_id: str) -> None:
        """
        Remove a vehicle ID from the container.

        Raises KeyError if vehicle_id is not present.
        Service layer should ensure validity before calling.
        """
        self._vehicle_ids.remove(vehicle_id)

    def contains_vehicle(self, vehicle_id: str) -> bool:
        """
        Check whether a vehicle ID exists in this container.
        """
        return vehicle_id in self._vehicle_ids

    def get_vehicle_ids(self) -> set[str]:
        """
        Return the set of vehicle IDs.

        NOTE:
        This returns the internal set directly.
        If immutability is desired, return a copy instead.
        """
        return self._vehicle_ids

    def count(self) -> int:
        """
        Return number of vehicles currently in the container.
        """
        return len(self._vehicle_ids)


class Station(VehicleContainer):
    """
    Represents a physical docking station.

    Extends VehicleContainer with:
    - Geographic location (lat, lon)
    - Maximum capacity constraint

    Business rules such as:
    - Nearest station calculation
    - Docking validation
    Are handled in the Service layer.
    """

    def __init__(
        self,
        container_id: int,
        _vehicle_ids: set[str],
        name: str,
        lat: float,
        lon: float,
        max_capacity: int
    ):
        """
        Initialize station with:
        - Coordinates for distance calculation
        - Capacity limit
        """
        super().__init__(container_id, _vehicle_ids, name)
        self.lat = lat
        self.lon = lon
        self.max_capacity = max_capacity

    def has_free_slot(self) -> bool:
        """
        Determine whether the station can accept another vehicle.

        Used by Service layer during ride end logic.
        """
        return self.count() < self.max_capacity


class DegradedRepo(VehicleContainer):
    """
    Repository for degraded vehicles.

    Acts as a holding area for vehicles that:
    - Have status DEGRADED
    - Are awaiting treatment

    This class does not enforce degradation logic.
    The Service layer decides when vehicles are moved here.
    """

    def __init__(
        self,
        container_id: int,
        _vehicle_ids: set[str],
        name: str
    ):
        super().__init__(container_id, _vehicle_ids, name)
