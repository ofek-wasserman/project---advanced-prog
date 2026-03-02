from typing import Optional

from src.domain.user import User
from src.domain.Vehicle import Vehicle
from src.domain.VehicleContainer import DegradedRepo, Station
from src.services.active_rides import ActiveRidesRegistry
from src.services.billing import BillingService


class FleetManager:
    def __init__(self,
                 stations: dict[int, Station],
                 vehicles: dict[int, Vehicle],
                active_rides: Optional[ActiveRidesRegistry] = None,
                degraded_repo: Optional[DegradedRepo] = None,
                billing_service: Optional[BillingService] = None,
                 ):

        self.users:dict[int,User] = {}
        self.stations = stations
        self.vehicles = vehicles
        self.active_rides = active_rides or ActiveRidesRegistry()
        self.degraded_repo = degraded_repo or DegradedRepo(
            container_id=-1, _vehicle_ids=set(), name="Degraded Repo"
        )
        self.billing_service = billing_service or BillingService()

<<<<<<< KAN-22-register-user-method
        # helper data structure to track registered payment tokens for quick validation
        self._registered_tokens: set[str] = set()


    def register_user(self, payment_token: str) -> int:
=======

    def register_user(self, payment_token: str) -> User:
>>>>>>> main
        """
        Registers a new user and generates a unique user_id.
        Args:
            payment_token (str): The payment token for the user.
        Returns:
<<<<<<< KAN-22-register-user-method
            int: The newly created user_id.
        Raises:
            ValueError: If the payment token is invalid or already exists.
        """
        if not isinstance(payment_token, str) or not payment_token.strip():
            raise ValueError("Invalid payment token provided.")

        if payment_token in self._registered_tokens:
            raise ValueError("Payment token already registered.")

        new_user_id = max(self.users.keys(), default=0) + 1
        new_user = User(user_id=new_user_id, payment_token=payment_token)
        # Update both data structures to maintain state consistency
        self.users[new_user_id] = new_user
        self._registered_tokens.add(payment_token)
        return new_user_id
=======
            User: The newly created User object.
        Raises:
            ValueError: If the payment token is invalid or already exists.
        """
        NotImplementedError("KAN-21: Implement FleetManager Class")
>>>>>>> main

    def start_ride(self, user_id: int, location:tuple[float, float]) -> dict[str, any]:
        """
        Start a ride for a user with a specific vehicle.
        Args:
            user_id (int): The unique identifier for the user.
            location (tuple[float, float]): The (latitude, longitude) of the user.
        returns:
            Ride: The newly started Ride object.
            location: The (lat, lon) of the station where the ride started.
        TODO:
            - check user existence
            - check user has no active ride
            - find nearest station with available vehicle
            - assign vehicle to user and remove from station inventory
            - store ride information in active rides registry
            - return ride object
        """
        NotImplementedError("KAN-21: Implement FleetManager Class")

    def end_ride(self, ride_id: int, location:tuple[float, float]) -> dict[str, any]:
        """
        End a ride for a user with a specific vehicle.
        Args:
            ride_id (int): The unique identifier for the ride.
            location (tuple[float, float]): The (latitude, longitude) where the ride ended.
        returns:
            location (tuple[float, float]): The (latitude, longitude) where the ride ended.
            payment_info (dict): Information about the payment for the ride.
        TODO:
             - check if user has an active ride
             - find nearest station with free slot
             - update ride information in active rides registry
             - end ride and calculate cost using billing service
             - increase ride_since_last_treated for the vehicle
             - if ride_since_last_treated > threshold, move vehicle to degraded repo
             - return location of the station where the ride ended
        """
        NotImplementedError("KAN-21: Implement FleetManager Class")

    # -----------------------------
    # Helper Functions
    # -----------------------------
    def _generate_ride_id(self) -> int:
        """
        Generates a new unique ride ID. In a real implementation, this could be more robust.
        """
        NotImplementedError("KAN-21: Implement FleetManager Class")

    def _nearest_station_with_free_slot(self,
                                        location:tuple[float, float],
                                        ) -> Optional[Station]:
        """
        Find the nearest station with a free slot for parking.
        Args:
            location (tuple[float, float]): The (latitude, longitude) of the user.
        Returns:
            Station: The nearest station with a free slot.
        """
        NotImplementedError("KAN-21: Implement FleetManager Class")

    def _nearest_station_with_available_vehicle(self,
                                                location:tuple[float, float],
                                                ) -> Optional[Station]:
        """
        Find the nearest station with at least one available vehicle.
        Args:
            location (tuple[float, float]): The (latitude, longitude) of the user.
        Returns:
            Station: The nearest station with an available vehicle.
        """
        NotImplementedError("KAN-21: Implement FleetManager Class")



