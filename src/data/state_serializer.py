"""Phase 2 - Save runtime state to data/state.json.

No business logic here: this module only reads public attributes from
FleetManager and writes them as JSON according to the schema defined in
docs/DECISIONS.md (state.json Schema section).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.ride import Ride
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


# ---------------------------------------------------------------------------
# Internal helpers – pure data extraction, no domain decisions
# ---------------------------------------------------------------------------

def _build_state(fm: FleetManager) -> dict:
    all_ride_ids = (
        list(fm.active_rides.rides.keys()) + list(fm.completed_rides.keys())
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "saved_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "next_user_id": max(fm.users.keys(), default=0) + 1,
        "next_ride_id": max(all_ride_ids, default=0) + 1,
        "users": _serialize_users(fm),
        "active_rides": _serialize_active_rides(fm),
        "completed_rides": _serialize_completed_rides(fm),
        "vehicles": _serialize_vehicles(fm),
        "degraded_repo": sorted(fm.degraded_repo.get_vehicle_ids()),
    }


def _serialize_users(fm: FleetManager) -> list:
    return [
        {"user_id": u.user_id, "payment_token": u.payment_token}
        for u in sorted(fm.users.values(), key=lambda u: u.user_id)
    ]


def _serialize_ride(ride: Ride) -> dict:
    return {
        "ride_id": ride.ride_id,
        "user_id": ride.user_id,
        "vehicle_id": ride.vehicle_id,
        "start_time": ride.start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_station_id": ride.start_station_id,
        "end_time": (
            ride.end_time.strftime("%Y-%m-%dT%H:%M:%SZ") if ride.end_time else None
        ),
        "end_station_id": ride.end_station_id,
        "reported_degraded": ride.reported_degraded,
        "price": ride.price,
    }


def _serialize_active_rides(fm: FleetManager) -> list:
    return [
        _serialize_ride(r)
        for r in sorted(fm.active_rides.rides.values(), key=lambda r: r.ride_id)
    ]


def _serialize_completed_rides(fm: FleetManager) -> list:
    return [
        _serialize_ride(r)
        for r in sorted(fm.completed_rides.values(), key=lambda r: r.ride_id)
    ]


def _serialize_vehicles(fm: FleetManager) -> list:
    result = []
    for v in sorted(fm.vehicles.values(), key=lambda v: v.vehicle_id):
        entry: dict = {
            "vehicle_id": v.vehicle_id,
            "type": v.VEHICLE_TYPE,
            "status": v.status.value,
            "rides_since_last_treated": v.rides_since_last_treated,
            "last_treated_date": v.last_treated_date.isoformat(),
            "station_id": v.station_id,
            "active_ride_id": v.active_ride_id,
        }
        charge_pct = getattr(v, "charge_pct", None)
        if charge_pct is not None:
            entry["charge_pct"] = charge_pct
        result.append(entry)
    return result
