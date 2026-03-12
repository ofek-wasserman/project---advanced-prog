"""Phase 2 - Save runtime state to data/state.json.

No business logic here: this module only reads public attributes from
FleetManager and writes them as JSON according to the schema defined in
docs/DECISIONS.md (state.json Schema section).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

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


# ---------------------------------------------------------------------------
# Internal helpers – pure data extraction, no domain decisions
# ---------------------------------------------------------------------------

def _build_state(fm: FleetManager) -> dict:
    all_ride_ids = (
        list(fm.active_rides.rides.keys()) + list(fm.completed_rides.keys())
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "saved_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "next_user_id": max(fm.users.keys(), default=0) + 1,
        "next_ride_id": max(all_ride_ids, default=0) + 1,
        "users": _serialize_users(fm),
        "active_rides": _serialize_active_rides(fm),
        "completed_rides": _serialize_completed_rides(fm),
        "vehicles": _serialize_vehicles(fm),
        "degraded_repo": sorted(fm.degraded_repo.get_vehicle_ids()),
    }


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
