import datetime
import math
from typing import Optional

from src.domain.enums import VehicleStatus
from src.domain.exceptions import ConflictError, InvalidInputError, NotFoundError
from src.domain.ride import Ride
from src.domain.user import User
from src.domain.Vehicle import Vehicle
from src.domain.VehicleContainer import DegradedRepo, Station
from src.services.active_rides import ActiveRidesRegistry
from src.services.billing import BillingService


class FleetManager:
    def __init__(self,
                stations: dict[int, Station],
                vehicles: dict[str, Vehicle],
                active_rides: Optional[ActiveRidesRegistry] = None,
                degraded_repo: Optional[DegradedRepo] = None,
                billing_service: Optional[BillingService] = None,
                ):

        self.users:dict[int,User] = {}
        self.stations = stations
        self.vehicles = vehicles
        self.active_rides = active_rides or ActiveRidesRegistry()
        self.completed_rides: dict[int, Ride] = {}
        self.degraded_repo = degraded_repo or DegradedRepo(
            container_id=-1, _vehicle_ids=set(), name="Degraded Repo"
        )
        self.billing_service = billing_service or BillingService()

        # helper data structure to track registered payment tokens for quick validation
        self._registered_tokens: set[str] = set()
        self._initialize_state()

    #-----------------------------
    # initializer vehicle state normalization
    #-----------------------------
    def _initialize_state(self) -> None:
        """Normalize loaded state after CSV bootstrap (Phase 1).

        Assumptions:
        - CSV bootstrap must not contain active rides.
        - Stations are loaded empty (no vehicle inventory).
        - Vehicles contain station_id.

        Goals:
        - Build station inventories from vehicles.
        - Move unrentable vehicles ( >10 rides) to the Degraded Repository.
        """
        for vehicle_id, vehicle in self.vehicles.items():
            # Phase 1 contract: no active rides at bootstrap
            if getattr(vehicle, "active_ride_id", None) is not None:
                raise InvalidInputError(
                    "Invalid bootstrap state: vehicle "
                    f"{vehicle_id} has active_ride_id={vehicle.active_ride_id}"
                )

            # Not eligible -> move to degraded and detach from station
            if not vehicle.is_eligible():
                self.degraded_repo.add_vehicle(vehicle_id)
                if vehicle.status != VehicleStatus.DEGRADED:
                    vehicle.mark_degraded()
                vehicle.station_id = None
                continue

            # Eligible -> must belong to a valid station
            if vehicle.station_id is None:
                raise InvalidInputError(f"Eligible vehicle {vehicle_id} has no station_id")

            station = self.stations.get(vehicle.station_id)
            if station is None:
                raise InvalidInputError(
                    f"Vehicle {vehicle_id} references unknown station_id={vehicle.station_id}"
                )

            station.add_vehicle(vehicle_id)

    #-----------------------------
    # Public API
    #-----------------------------
    def register_user(self, payment_token: str) -> int:
        """
        Registers a new user and generates a unique user_id.
        Raises:
            InvalidInputError: If the payment token is invalid.
            ConflictError: If the payment token already exists.
        """
        if not isinstance(payment_token, str):
            raise InvalidInputError("Invalid payment token provided.")

        token = payment_token.strip()
        if not token:
            raise InvalidInputError("Payment token must be non-empty.")

        if token in self._registered_tokens:
            raise ConflictError("Payment token already registered.")

        new_user_id = max(self.users.keys(), default=0) + 1
        new_user = User(user_id=new_user_id, payment_token=token)

        self.users[new_user_id] = new_user
        self._registered_tokens.add(token)
        return new_user_id

    def start_ride(self, user_id: int, location:tuple[float, float]) -> tuple[Ride, int]:
        """
        Start a ride for a user with a specific vehicle.
        Args:
            user_id (int): The unique identifier for the user.
            location (tuple[float, float]): The (latitude, longitude) of the user.
        returns:
            Ride: The newly started Ride object.
            location: The (lat, lon) of the station where the ride started.
        """
        if user_id not in self.users:
            raise NotFoundError("User does not exist.")

        if self.active_rides.has_active_ride_for_user(user_id):
            raise ConflictError("User already has an active ride.")

        nearest_station = self.nearest_station_with_available_vehicle(location)
        if nearest_station is None:
            raise ConflictError("No eligible vehicles")

        vehicle_ids = nearest_station.get_vehicle_ids()
        #determine which vehicle to assign (the least usage and smallest ID for tie-breaking)
        select_vehicle_id = min(vehicle_ids, key=lambda vid:
                                (self.vehicles[vid].rides_since_last_treated, vid))

        ride_id = self._generate_ride_id()


        # Create the Ride object and add it to the active rides registry
        ride: Ride = Ride(ride_id=ride_id,
                          user_id=user_id,
                          vehicle_id=select_vehicle_id,
                          start_time=datetime.datetime.now(),
                          start_station_id=nearest_station.container_id,
                          )

        try:
            self.active_rides.add(ride)
        except ConflictError as e:
            raise ConflictError(f"Cannot start ride: {e}") from e
        except InvalidInputError as e:
            raise InvalidInputError(f"Cannot start ride: {e}") from e

        nearest_station.remove_vehicle(select_vehicle_id)
        self.vehicles[select_vehicle_id].checkout_to_ride(ride_id=ride_id)

        return ride , ride.start_station_id

    def end_ride(self, ride_id: int, location:tuple[float, float]) -> tuple[int, float]:
        """
        End a ride for a user with a specific vehicle.
        Args:
            ride_id (int): The unique identifier for the ride.
            location (tuple[float, float]): The (latitude, longitude) where the ride ended.
        returns:
            location (tuple[float, float]): The (latitude, longitude) where the ride ended.
            payment_info (dict): Information about the payment for the ride.
        """
        if not isinstance(location, tuple) or len(location) != 2:
            raise InvalidInputError("Invalid location format. Expected Tuple[float, float].")

        ride: Ride = self.active_rides.get(ride_id)

        nearest_station = self._nearest_station_with_free_slot(location)
        if nearest_station is None:
            raise ConflictError("No station with free slot available")

        # define end_time after start_time
        end_time= datetime.datetime.now()

        user = self.users.get(ride.user_id)
        if user is None:
            raise NotFoundError("User for this ride does not exist.")

        #process payment
        price = self.billing_service.calculate_price(start_time=ride.start_time,
                                                            end_time=end_time,
                                                            reported_degraded=ride.reported_degraded
                                                            )
        paid = self.billing_service.process_payment(user.payment_token, float(price))
        if not paid:
            raise ConflictError("Payment failed.")

        #end ride
        ride.end(
            end_station_id=nearest_station.container_id,end_time=end_time)
        ride.price = price
        self.active_rides.remove(ride_id)
        self.completed_rides[ride_id] = ride

        #process vehicle end ride
        vehicle = self.vehicles.get(ride.vehicle_id)
        if vehicle is None:
            raise NotFoundError("Vehicle for this ride does not exist.")

        vehicle.add_ride_count()
        if not vehicle.is_eligible():
            # degraded -> mark degraded
            self.degraded_repo.add_vehicle(vehicle_id=vehicle.vehicle_id)
            vehicle.move_to_repo()
            if vehicle.status != VehicleStatus.DEGRADED:
                vehicle.mark_degraded()
        else:
            # eligible -> doc to station
            nearest_station.add_vehicle(vehicle.vehicle_id)
            vehicle.dock_to_station(nearest_station.container_id)

        # return end ride station and price
        return nearest_station.container_id, price

    def nearest_station_with_available_vehicle(self,
                                                location:tuple[float, float],
                                                ) -> Optional[Station]:
        """
        Find the nearest station with at least one available vehicle.
        Args:
            location (tuple[float, float]): The (latitude, longitude) of the user.
        Returns:
            Station: The nearest station with an available vehicle.
        """
        if not isinstance(location, tuple) or len(location) != 2:
            raise InvalidInputError("Invalid location format. Expected Tuple[float, float].")

        valid_stations = [station for station in self.stations.values() if
                          station.has_available_vehicle()]
        if not valid_stations:
            return None

        nearest = min(valid_stations,
                      key=lambda station:
                      (self._distance(location, (station.lat, station.lon)),
                       station.container_id)
                   )
        return nearest

    def active_user_ids(self) -> list[int]:
        return sorted(self.active_rides.active_user_ids())

    def apply_treatment(self, treatment_location:tuple[float, float]) -> list[str]:
        """
        Run maintenance on all treatable vehicles
        Arg:
            location (tuple[float, float]): The treatment location (latitude, longitude).
        Return:
                vehicle IDs list of treated vehicles
        """
        treated: list[str] = []
        degraded_ids = set(self.degraded_repo.get_vehicle_ids())
        non_degraded_ids = [vid for vid in self.vehicles.keys()
                            if vid not in degraded_ids
                            and self.vehicles[vid].can_initiate_treatment()]

        # for degraded vehicles
        for vehicle_id in degraded_ids:
            nearest_station = self._nearest_station_with_free_slot(location=treatment_location)
            if nearest_station is None:
                raise ConflictError("No station with free slot available")
            degr_vehicle = self.vehicles.get(vehicle_id)
            if degr_vehicle is None:
                raise NotFoundError(f"Vehicle {vehicle_id} not found.")
            degr_vehicle.apply_treatment()
            self.degraded_repo.remove_vehicle(vehicle_id)
            nearest_station.add_vehicle(vehicle_id)
            degr_vehicle.dock_to_station(nearest_station.container_id)
            treated.append(vehicle_id)

        # for eligible vehicles that can have a treatment
        for vehicle_id in non_degraded_ids:
            vehicle = self.vehicles[vehicle_id]
            vehicle.apply_treatment()
            treated.append(vehicle_id)

        return treated
    def report_degraded(self,vehicle_id:str, user_id:int) -> None:
        """
        Report a vehicle as degraded.
        Args:
            vehicle_id (str): The unique identifier for the vehicle.
        """
        # validation
        if user_id not in self.users:
            raise NotFoundError("User does not exist.")
        if vehicle_id not in self.vehicles:
            raise NotFoundError("Vehicle does not exist.")
        if not self.active_rides.is_vehicle_in_ride(vehicle_id):
            raise ConflictError("Vehicle is not in an active ride.")

        ride = self.active_rides.get_active_ride_for_user(user_id)
        if ride is None:
            raise ConflictError("User does not have an active ride.")
        if vehicle_id != ride.vehicle_id:
            raise ConflictError("Vehicle not in user active ride.")

        # degraded
        ride.report_degraded()
        ride.price = 0

        # remove from active rides to compleat rides
        self.active_rides.remove(ride.ride_id)
        self.completed_rides[ride.ride_id] = ride

        vehicle = self.vehicles.get(vehicle_id)
        vehicle.move_to_repo()
        vehicle.mark_degraded()
        self.degraded_repo.add_vehicle(vehicle_id)






    # -----------------------------
    # Helper Functions
    # -----------------------------
    def _distance(self, loc1:tuple[float, float], loc2:tuple[float, float]) -> float:
        """
        Calculate the distance between two locations.
        Args:
            loc1 (tuple[float, float]): The (latitude, longitude) of the first location.
            loc2 (tuple[float, float]): The (latitude, longitude) of the second location.
        Returns:
            float: The distance between the two locations.
        """
        if not isinstance(loc1, tuple) or not isinstance(loc2, tuple):
            raise InvalidInputError("Coordinates must be strictly of type Tuple[float, float].")

        if len(loc1) != 2 or len(loc2) != 2:
            raise InvalidInputError("Coordinates must contain exactly two dimensions (x, y).")

        if math.isnan(loc1[0]) or math.isnan(loc1[1]) or math.isnan(loc2[0]) or math.isnan(loc2[1]):
            raise InvalidInputError("Coordinates cannot contain NaN values.")

        return math.dist(loc1, loc2)

    def _generate_ride_id(self) -> int:
        """
        Generates a new unique ride ID. In a real implementation, this could be more robust.
        """
        return max(self.active_rides.rides.keys(), default=0) + 1

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
        if not isinstance(location, tuple) or len(location) != 2:
            raise InvalidInputError("Invalid location format. Expected Tuple[float, float].")

        valid_stations = [station for station in self.stations.values() if
                          station.has_free_slot()]
        if not valid_stations:
            return None

        nearest = min(valid_stations,
                      key=lambda station:
                      (self._distance(location, (station.lat, station.lon)),
                       station.container_id)
                   )
        return nearest




