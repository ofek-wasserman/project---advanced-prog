from typing import Optional

from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.ride import Ride


class ActiveRidesRegistry:
    """Tracks active rides and prevents conflicts (one active ride per user/vehicle)."""

    def __init__(self) -> None:
        self.rides: dict[int, Ride] = {}
        self.rides_by_user: dict[int, int] = {}
        self.rides_by_vehicle: dict[str, int] = {}

    def add(self, ride: Ride) -> None:
        """
        Add a ride to the registry.
        arg: ride (Ride): The ride to add.
        returns: None
        """
        if ride.ride_id in self.rides:
            raise ConflictError(f"Ride ID {ride.ride_id} already exists in registry.")
        if ride.user_id in self.rides_by_user:
            raise ConflictError(f"User ID {ride.user_id} already has an active ride.")
        if ride.vehicle_id in self.rides_by_vehicle:
            raise ConflictError(f"Vehicle ID {ride.vehicle_id} is already in an active ride.")

        self.rides[ride.ride_id] = ride
        self.rides_by_user[ride.user_id] = ride.ride_id
        self.rides_by_vehicle[ride.vehicle_id] = ride.ride_id

    def remove(self, ride_id: int) -> Ride:
        """
        Remove a ride from the registry.
        arg: ride_id (int): The ID of the ride to remove.
        returns: Ride: The removed ride.
        """
        if ride_id not in self.rides:
            raise NotFoundError(f"Ride ID {ride_id} not found in registry.")

        ride = self.rides.pop(ride_id)
        self.rides_by_user.pop(ride.user_id, None)
        self.rides_by_vehicle.pop(ride.vehicle_id, None)
        return ride

    def get(self, ride_id: int) -> Ride:
        """
        Get a ride by its ID.
        arg: ride_id (int): The ID of the ride to retrieve.
        returns: Ride: The retrieved ride.
        """
        if ride_id not in self.rides:
            raise NotFoundError(f"Ride ID {ride_id} not found in registry.")
        return self.rides[ride_id]

    def has_active_ride_for_user(self, user_id: int) -> bool:
        """
        Check if a user has an active ride.
        arg: user_id (int): The ID of the user to check.
        """
        return user_id in self.rides_by_user

    def get_active_ride_for_user(self, user_id: int) -> Optional[Ride]:
        """
        Get the active ride for a user.
        arg: user_id (int): The ID of the user to retrieve the ride for.
        returns: Ride: The active ride for the user, or None if no active ride exists.
        """
        ride_id = self.rides_by_user.get(user_id)
        if ride_id is None:
            return None
        return self.rides.get(ride_id)

    def is_vehicle_in_ride(self, vehicle_id: str) -> bool:
        """
        Check if a vehicle is in an active ride.
        arg: vehicle_id (str): The ID of the vehicle to check.
        returns: bool: True if the vehicle is in an active ride, False otherwise.
        """
        return vehicle_id in self.rides_by_vehicle

    def active_user_ids(self) -> set[int]:
        """
        Get a set of all active user IDs.
        returns: set[int]: A list of all active user IDs.
        """
        return set(self.rides_by_user.keys())

    def active_ride_ids(self) -> set[int]:
        """
        Get a set of all active ride IDs.
        returns: set[int]: A list of all active ride IDs.
        """
        return set(self.rides.keys())
