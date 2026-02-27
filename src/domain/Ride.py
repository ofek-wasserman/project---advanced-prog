# domain/ride.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Ride:
    """
    Domain entity representing a ride lifecycle.

    Invariants:
    - ride_id, user_id must be positive
    - vehicle_id must be non-empty
    - start_time is required
    - end_time cannot exist without end_station_id
    - Cannot end an already ended ride
    """

    ride_id: int
    user_id: int
    vehicle_id: str
    start_time: datetime
    start_station_id: int

    end_time: Optional[datetime] = None
    end_station_id: Optional[int] = None
    reported_degraded: bool = False
    price: Optional[int] = None

    def __post_init__(self) -> None:
        if self.ride_id <= 0:
            raise ValueError("ride_id must be positive")

        if self.user_id <= 0:
            raise ValueError("user_id must be positive")

        if not self.vehicle_id:
            raise ValueError("vehicle_id must be non-empty")

        if self.start_station_id <= 0:
            raise ValueError("start_station_id must be positive")

    # -------------------------
    # State Queries
    # -------------------------

    def is_active(self) -> bool:
        """Return True if ride has not ended."""
        return self.end_time is None

    def duration_seconds(self) -> int:
        """Return ride duration in seconds. Only valid if ride ended."""
        if self.is_active():
            raise ValueError("Cannot compute duration of active ride")

        return int((self.end_time - self.start_time).total_seconds())

    # -------------------------
    # State Transitions
    # -------------------------

    def end(self, end_station_id: int, end_time: datetime) -> None:
        """
        End the ride.

        Business rules:
        - Ride must be active
        - end_station_id must be positive
        - end_time must be after start_time
        """

        if not self.is_active():
            raise ValueError("Ride already ended")

        if end_station_id <= 0:
            raise ValueError("end_station_id must be positive")

        if end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

        self.end_station_id = end_station_id
        self.end_time = end_time
    

    def report_degraded(self) -> None:
        """Mark ride as degraded."""
        self.reported_degraded = True
