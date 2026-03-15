"""Phase 2 - Save runtime state to data/state.json.

No business logic here: this module only reads public attributes from
FleetManager and writes them as JSON according to the schema defined in
docs/DECISIONS.md (state.json Schema section).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.domain.enums import VehicleLocation, VehicleStatus
from src.domain.ride import Ride
from src.domain.user import User
from src.domain.VehicleContainer import DegradedRepo
from src.services.active_rides import ActiveRidesRegistry

if TYPE_CHECKING:
    from src.services.fleet_manager import FleetManager

SCHEMA_VERSION = 1


def save_state(fleet_manager: FleetManager, path: Path | str) -> None:
    """Serialize all runtime state to *path* as JSON.

    The parent directory is created automatically if it does not exist.
    The file is created if missing and overwritten on every call.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    state = _build_state(fleet_manager)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


def load_state(fleet_manager: FleetManager, path: Path | str) -> bool:
    """Load persisted runtime state from *path* and apply it to *fleet_manager*.

    Returns True when a snapshot was loaded, and False when the file does not
    exist (CSV-only bootstrap mode).
    """
    path = Path(path)
    if not path.exists():
        return False

    with path.open("r", encoding="utf-8") as fh:
        state = json.load(fh)

    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported state schema_version")

    _apply_state(fleet_manager, state)
    return True


# ---------------------------------------------------------------------------
# Internal helpers – pure data extraction, no domain decisions
# ---------------------------------------------------------------------------

def _build_state(fm: FleetManager) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "saved_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "next_user_id": _resolve_next_user_id(fm),
        "next_ride_id": _resolve_next_ride_id(fm),
        "users": _serialize_users(fm),
        "active_rides": _serialize_active_rides(fm),
        "completed_rides": _serialize_completed_rides(fm),
        "vehicles": _serialize_vehicles(fm),
        "degraded_repo": sorted(fm.degraded_repo.get_vehicle_ids()),
    }


def _resolve_next_user_id(fm: FleetManager) -> int:
    fallback = max(fm.users.keys(), default=0) + 1
    try:
        return max(fm.next_user_id, fallback)
    except AttributeError:
        return fallback


def _resolve_next_ride_id(fm: FleetManager) -> int:
    all_ride_ids = list(fm.active_rides.rides.keys()) + list(fm.completed_rides.keys())
    fallback = max(all_ride_ids, default=0) + 1
    try:
        return max(fm.next_ride_id, fallback)
    except AttributeError:
        return fallback


def _serialize_users(fm: FleetManager) -> dict:
    return {
        str(u.user_id): {"user_id": u.user_id, "payment_token": u.payment_token}
        for u in sorted(fm.users.values(), key=lambda u: u.user_id)
    }


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _serialize_active_rides(fm: FleetManager) -> dict:
    result = {}
    for ride in sorted(fm.active_rides.rides.values(), key=lambda r: r.ride_id):
        result[str(ride.ride_id)] = {
            "ride_id": ride.ride_id,
            "user_id": ride.user_id,
            "vehicle_id": ride.vehicle_id,
            "start_time": _fmt_dt(ride.start_time),
            "start_station_id": ride.start_station_id,
            "reported_degraded": ride.reported_degraded,
        }
    return result


def _serialize_completed_rides(fm: FleetManager) -> list:
    return [
        {
            "ride_id": r.ride_id,
            "user_id": r.user_id,
            "vehicle_id": r.vehicle_id,
            "start_time": _fmt_dt(r.start_time),
            "start_station_id": r.start_station_id,
            "end_time": _fmt_dt(r.end_time) if r.end_time else None,
            "end_station_id": r.end_station_id,
            "reported_degraded": r.reported_degraded,
            "price": r.price,
        }
        for r in sorted(fm.completed_rides.values(), key=lambda r: r.ride_id)
    ]


def _serialize_vehicles(fm: FleetManager) -> dict:
    return {
        v.vehicle_id: {
            "status": v.status.value,
            "rides_since_last_treated": v.rides_since_last_treated,
            "last_treated_date": v.last_treated_date.isoformat(),
            "station_id": v.station_id,
        }
        for v in sorted(fm.vehicles.values(), key=lambda v: v.vehicle_id)
    }


def _parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


def _apply_state(fm: FleetManager, state: dict) -> None:
    _apply_vehicle_overrides(fm, state.get("vehicles", {}))
    _restore_users(fm, state.get("users", {}))
    _restore_active_rides(fm, state.get("active_rides", {}))
    _restore_completed_rides(fm, state.get("completed_rides", []))
    _restore_degraded_repo(fm, state.get("degraded_repo", []))
    _rebuild_station_inventories(fm)

    fm.configure_id_counters(
        next_user_id=int(state.get("next_user_id", 1)),
        next_ride_id=int(state.get("next_ride_id", 1)),
    )


def _apply_vehicle_overrides(fm: FleetManager, vehicles_state: dict) -> None:
    for vehicle_id, mutable_fields in vehicles_state.items():
        vehicle = fm.vehicles.get(vehicle_id)
        if vehicle is None:
            raise ValueError(f"Unknown vehicle in state: {vehicle_id}")

        vehicle.status = VehicleStatus(mutable_fields["status"])
        vehicle.rides_since_last_treated = int(mutable_fields["rides_since_last_treated"])
        vehicle.last_treated_date = date.fromisoformat(mutable_fields["last_treated_date"])
        vehicle.station_id = mutable_fields["station_id"]
        vehicle.active_ride_id = None
        vehicle.location = (
            VehicleLocation.DOCKED
            if vehicle.station_id is not None
            else VehicleLocation.IN_REPO
        )


def _restore_users(fm: FleetManager, users_state: dict) -> None:
    fm.users = {}
    fm._registered_tokens = set()

    for user_data in users_state.values():
        user_id = int(user_data["user_id"])
        token = str(user_data["payment_token"])
        fm.users[user_id] = User(user_id=user_id, payment_token=token)
        fm._registered_tokens.add(token)


def _restore_active_rides(fm: FleetManager, active_rides_state: dict) -> None:
    registry = ActiveRidesRegistry()
    for ride_data in active_rides_state.values():
        ride = Ride(
            ride_id=int(ride_data["ride_id"]),
            user_id=int(ride_data["user_id"]),
            vehicle_id=str(ride_data["vehicle_id"]),
            start_time=_parse_dt(ride_data["start_time"]),
            start_station_id=int(ride_data["start_station_id"]),
            reported_degraded=bool(ride_data.get("reported_degraded", False)),
        )
        registry.add(ride)

        vehicle = fm.vehicles.get(ride.vehicle_id)
        if vehicle is None:
            raise ValueError(f"Unknown vehicle referenced by active ride: {ride.vehicle_id}")

        vehicle.active_ride_id = ride.ride_id
        vehicle.station_id = None
        vehicle.location = VehicleLocation.IN_RIDE

    fm.active_rides = registry


def _restore_completed_rides(fm: FleetManager, completed_rides_state: list) -> None:
    fm.completed_rides = {}
    for ride_data in completed_rides_state:
        ride = Ride(
            ride_id=int(ride_data["ride_id"]),
            user_id=int(ride_data["user_id"]),
            vehicle_id=str(ride_data["vehicle_id"]),
            start_time=_parse_dt(ride_data["start_time"]),
            start_station_id=int(ride_data["start_station_id"]),
            end_time=_parse_dt(ride_data["end_time"]) if ride_data.get("end_time") else None,
            end_station_id=ride_data.get("end_station_id"),
            reported_degraded=bool(ride_data.get("reported_degraded", False)),
            price=ride_data.get("price"),
        )
        fm.completed_rides[ride.ride_id] = ride


def _restore_degraded_repo(fm: FleetManager, degraded_repo_state: list[str]) -> None:
    for vehicle_id in degraded_repo_state:
        if vehicle_id not in fm.vehicles:
            raise ValueError(f"Unknown vehicle in degraded_repo: {vehicle_id}")

    fm.degraded_repo = DegradedRepo(
        container_id=-1,
        _vehicle_ids=set(degraded_repo_state),
        name="Degraded Repo",
    )

    for vehicle_id in fm.degraded_repo.get_vehicle_ids():
        vehicle = fm.vehicles[vehicle_id]
        vehicle.station_id = None
        vehicle.active_ride_id = None
        vehicle.location = VehicleLocation.IN_REPO


def _rebuild_station_inventories(fm: FleetManager) -> None:
    for station in fm.stations.values():
        station.get_vehicle_ids().clear()

    active_vehicle_ids = {ride.vehicle_id for ride in fm.active_rides.rides.values()}
    degraded_vehicle_ids = set(fm.degraded_repo.get_vehicle_ids())

    for vehicle_id, vehicle in fm.vehicles.items():
        if vehicle_id in active_vehicle_ids or vehicle_id in degraded_vehicle_ids:
            continue

        station_id = vehicle.station_id
        if station_id is None:
            continue

        station = fm.stations.get(station_id)
        if station is None:
            raise ValueError(
                f"Vehicle {vehicle_id} references unknown station_id={station_id}"
            )

        station.add_vehicle(vehicle_id)
        vehicle.location = VehicleLocation.DOCKED
