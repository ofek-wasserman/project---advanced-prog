from abc import ABC, abstractmethod
from datetime import date

import src.domain.enums as ve
from src.domain.exceptions import ConflictError


class Vehicle(ABC):
    """
    Abstract base class representing a vehicle in the system.

    This class contains shared state and behavior for all vehicle types.
    Concrete subclasses (e.g., Bike, Scooter) must implement type-specific
    eligibility and treatment logic.

    Domain layer:
    - Contains no I/O
    - Encapsulates state transitions
    - Enforces domain rules
    """

    def __init__(
        self,
        vehicle_id: str,
        status: 've.VehicleStatus',
        rides_since_last_treated: int,
        last_treated_date: date,
        station_id: int | None,
        active_ride_id: int | None
    ):
        """
        Initialize a vehicle with its persistent state.

        location is derived (not passed) based on whether the vehicle
        is currently assigned to a station.

        Invariant:
        - If station_id is not None → vehicle is docked
        - Otherwise → vehicle is in repository (maintenance/storage)
        """
        self.vehicle_id = vehicle_id
        self.status = status
        self.rides_since_last_treated = rides_since_last_treated
        self.last_treated_date = last_treated_date
        self.station_id = station_id
        self.active_ride_id = active_ride_id

        # Derived state based on docking
        self.location = (
            ve.VehicleLocation.DOCKED
            if station_id is not None
            else ve.VehicleLocation.IN_REPO
        )

    @abstractmethod
    def is_eligible(self) -> bool:
        """
        Determines whether the vehicle can be used to start a ride.

        Must be implemented by subclasses.
        Logic may depend on:
        - Vehicle type
        - Current status
        - Treatment rules

        Used by Service layer during deterministic vehicle selection.
        """
        raise NotImplementedError

    @abstractmethod
    def can_initiate_treatment(self) -> bool:
        """
        Determines whether the vehicle qualifies for maintenance/treatment.

        Subclasses define treatment policy (e.g., after X rides).
        """
        raise NotImplementedError

    def mark_degraded(self) -> None:
        """
        Mark the vehicle as degraded.

        Used when business logic determines the vehicle
        is no longer fit for rides.

        Raises:
            ConflictError: If the vehicle is already degraded.
        """
        if self.status == ve.VehicleStatus.DEGRADED:
            raise ConflictError("Vehicle is already degraded.")
        self.status = ve.VehicleStatus.DEGRADED

    def apply_treatment(self, today: date) -> None:
        """
        Apply maintenance treatment to the vehicle.

        Effects:
        - Status becomes AVAILABLE
        - Ride counter resets
        - Treatment date updated

        """
        if self.can_initiate_treatment():
            self.status = ve.VehicleStatus.AVAILABLE
            self.rides_since_last_treated = 0
            self.last_treated_date = today
        else:
            raise Exception("Vehicle does not qualify for treatment.")

    def add_ride_count(self) -> None:
        """
        Increment ride counter after a completed ride.

        Called by Service layer when a ride ends.
        """
        self.rides_since_last_treated += 1

    def dock_to_station(self, station_id: int) -> None:
        """
        Dock the vehicle at a station.

        Effects:
        - Assigns station_id
        - Clears active ride
        - Sets location to DOCKED
        """
        self.station_id = station_id
        self.active_ride_id = None
        self.location = ve.VehicleLocation.DOCKED

    def checkout_to_ride(self, ride_id: int) -> None:
        """
        Assign vehicle to an active ride.

        Effects:
        - Removes station assignment
        - Sets active ride ID
        - Sets location to IN_RIDE
        """
        self.station_id = None
        self.active_ride_id = ride_id
        self.location = ve.VehicleLocation.IN_RIDE

    def move_to_repo(self) -> None:
        """
        Move vehicle to repository (maintenance/storage).

        Effects:
        - Clears station
        - Clears active ride
        - Sets location to IN_REPO
        """
        self.station_id = None
        self.active_ride_id = None
        self.location = ve.VehicleLocation.IN_REPO

class Bicycle(Vehicle):
    """
    Concrete implementation of a mechanical bicycle.

    Domain rules:
    - Max 10 rides before becoming ineligible
    - Treatment can start after 7 rides or if degraded
    """

    def __init__(
        self,
        vehicle_id: str,
        status: 've.VehicleStatus',
        rides_since_last_treated: int,
        last_treated_date: date,
        station_id: int | None,
        active_ride_id: int | None
    ):
        """
        Initialize a Bicycle instance.

        Delegates shared initialization to Vehicle base class.
        """
        super().__init__(
            vehicle_id,
            status,
            rides_since_last_treated,
            last_treated_date,
            station_id,
            active_ride_id
        )

    def is_eligible(self) -> bool:
        """
        A bicycle is eligible for a ride if:
        - Status is AVAILABLE
        - It has not exceeded 10 rides since last treatment

        Used by Service layer during deterministic vehicle selection.
        """
        return (
            self.status == ve.VehicleStatus.AVAILABLE
            and self.rides_since_last_treated <= 10
            and self.active_ride_id is None
        )

    def can_initiate_treatment(self) -> bool:
        """
        A bicycle can initiate treatment if:
        - It has at least 7 rides since last treatment
        OR
        - It is marked as DEGRADED
        """
        return (
            self.rides_since_last_treated >= 7
            or self.status == ve.VehicleStatus.DEGRADED
        )


class ElectricVehicle(Vehicle):
    """
    Abstract representation of electric-powered vehicles.

    Adds battery state and charge-related behavior
    on top of base Vehicle functionality.

    Shared by:
    - EBike
    - Scooter
    """

    def __init__(
        self,
        vehicle_id: str,
        status: 've.VehicleStatus',
        rides_since_last_treated: int,
        last_treated_date: date,
        station_id: int | None,
        active_ride_id: int | None,
        charge_pct: int
    ):
        """
        Initialize electric vehicle state.

        charge_pct represents battery percentage (0–100).
        """
        super().__init__(
            vehicle_id,
            status,
            rides_since_last_treated,
            last_treated_date,
            station_id,
            active_ride_id
        )
        self.charge_pct = charge_pct

    def is_eligible(self) -> bool:
        raise NotImplementedError

    def can_initiate_treatment(self) -> bool:
        raise NotImplementedError

    def is_charged_enough(self) -> bool:
        """
        Battery eligibility threshold.

        Minimum required charge to start a ride: 20%.
        """
        return self.charge_pct >= 20

    def consume_charge(self, distance: float) -> None:
        """
        Reduce battery charge based on ride distance.

        Simplified model:
        - 1% battery per kilometer
        - Battery never drops below 0%

        Should be called by Service layer when ride ends.
        """
        self.charge_pct = max(0, self.charge_pct - int(distance))

    def recharge(self) -> None:
        """
        Fully recharge battery to 100%.

        Likely used during treatment workflow.
        """
        self.charge_pct = 100


class EBike(ElectricVehicle):
    """
    Electric Bicycle.

    Currently inherits all behavior from ElectricVehicle
    without additional domain rules.

    Exists for type distinction and future extensibility.
    """

    def __init__(
        self,
        vehicle_id: str,
        status: 've.VehicleStatus',
        rides_since_last_treated: int,
        last_treated_date: date,
        station_id: int | None,
        active_ride_id: int | None,
        charge_pct: int
    ):
        super().__init__(
            vehicle_id,
            status,
            rides_since_last_treated,
            last_treated_date,
            station_id,
            active_ride_id,
            charge_pct
        )

    def is_eligible(self) -> bool:
        """
        An E-Bike is eligible if:
        - Status is AVAILABLE
        - It has not exceeded 10 rides since last treatment
        - It is not currently assigned to an active ride

        Battery is currently not part of the active eligibility rules.
        """
        return (
            self.status == ve.VehicleStatus.AVAILABLE
            and self.rides_since_last_treated <= 10
            and self.active_ride_id is None
        )

    def can_initiate_treatment(self) -> bool:
        """
        Electric vehicle treatment rule:
        Same threshold as Bicycle (7 rides) OR if degraded.
        """
        return (
            self.rides_since_last_treated >= 7
            or self.status == ve.VehicleStatus.DEGRADED
        )



class Scooter(ElectricVehicle):
    """
    Electric Scooter.

    Inherits all electric vehicle rules.
    Defined separately for domain clarity and
    potential future rule differentiation.
    """

    def __init__(
        self,
        vehicle_id: str,
        status: 've.VehicleStatus',
        rides_since_last_treated: int,
        last_treated_date: date,
        station_id: int | None,
        active_ride_id: int | None,
        charge_pct: int
    ):
        super().__init__(
            vehicle_id,
            status,
            rides_since_last_treated,
            last_treated_date,
            station_id,
            active_ride_id,
            charge_pct
        )

    def is_eligible(self) -> bool:
        """
        A scooter is eligible if:
        - Status is AVAILABLE
        - It has not exceeded 10 rides since last treatment
        - It is not currently assigned to an active ride

        Battery is currently not part of the active eligibility rules.
        """
        return (
            self.status == ve.VehicleStatus.AVAILABLE
            and self.rides_since_last_treated <= 10
            and self.active_ride_id is None
        )

    def can_initiate_treatment(self) -> bool:
        """
        Electric vehicle treatment rule:
        Same threshold as Bicycle (7 rides) OR if degraded.
        """
        return (
            self.rides_since_last_treated >= 7
            or self.status == ve.VehicleStatus.DEGRADED
        )
