class ActiveRidesRegistry:
    """Tracks active rides to prevent conflicts"""

    def __init__(self):
        self._active_rides = {}
        self._user_active_rides = {}
        self._vehicle_active_rides = {}
        self._next_ride_id = 1

    def create_ride(self, user_id: int, vehicle_id: str, start_station_id: int):
        """Create new ride and track it"""
        ride_id = self._next_ride_id
        self._next_ride_id += 1

        ride = {
            "ride_id": ride_id,
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "start_station_id": start_station_id,
            "end_station_id": None,
            "start_time": None,
            "end_time": None,
            "price": None,
            "reported_degraded": False,
        }

        self._active_rides[ride_id] = ride
        self._user_active_rides[user_id] = ride_id
        self._vehicle_active_rides[vehicle_id] = ride_id

        return ride_id

    def get_ride(self, ride_id: int):
        """Get ride by id"""
        return self._active_rides.get(ride_id)

    def end_ride(self, ride_id: int):
        """Remove ride from active tracking"""
        ride = self._active_rides.pop(ride_id, None)
        if ride:
            self._user_active_rides.pop(ride["user_id"], None)
            self._vehicle_active_rides.pop(ride["vehicle_id"], None)
        return ride

    def user_has_active_ride(self, user_id: int) -> bool:
        """Check if user has active ride"""
        return user_id in self._user_active_rides

    def vehicle_in_use(self, vehicle_id: str) -> bool:
        """Check if vehicle is in use"""
        return vehicle_id in self._vehicle_active_rides

    def get_user_active_ride(self, user_id: int):
        """Get user's active ride"""
        ride_id = self._user_active_rides.get(user_id)
        if ride_id:
            return self._active_rides.get(ride_id)
        return None

    def active_ride_ids(self):
        """Get all active ride ids"""
        return list(self._active_rides.keys())
