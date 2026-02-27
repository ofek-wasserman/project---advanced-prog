from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


class _FleetEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if hasattr(obj, "value"):  # enums
            return obj.value
        return super().default(obj)


def _to_dict(obj: Any) -> dict:
    return obj if isinstance(obj, dict) else vars(obj)


class SnapshotManager:
    """Saves and loads the full fleet state as a JSON file."""

    DEFAULT_PATH = Path("data/snapshot.json")

    def __init__(self, snapshot_path: str | Path | None = None) -> None:
        self.snapshot_path = Path(snapshot_path or self.DEFAULT_PATH)

    def save(self, fleet_manager: Any) -> None:
        snapshot = self._build_snapshot(fleet_manager)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        with self.snapshot_path.open("w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, cls=_FleetEncoder, indent=2)

    def load(self) -> dict | None:
        """Returns None on a fresh start (no snapshot file yet)."""
        if not self.snapshot_path.exists():
            return None
        with self.snapshot_path.open(encoding="utf-8") as fh:
            return self._restore(json.load(fh))

    def exists(self) -> bool:
        return self.snapshot_path.exists()

    def delete(self) -> None:
        if self.snapshot_path.exists():
            self.snapshot_path.unlink()

    def _build_snapshot(self, fleet_manager: Any) -> dict:
        if isinstance(fleet_manager, dict):
            return fleet_manager

        active_rides: dict[str, dict] = {}
        registry = getattr(fleet_manager, "active_rides", None)
        if registry is not None:
            for rid in registry.active_ride_ids():
                active_rides[str(rid)] = _to_dict(registry.get(rid))

        degraded_repo = getattr(fleet_manager, "degraded_repo", None)
        degraded_ids = list(degraded_repo.list_vehicle_ids()) if degraded_repo else []

        return {
            "stations": {str(k): _to_dict(v) for k, v in fleet_manager.stations.items()},
            "vehicles": {str(k): _to_dict(v) for k, v in fleet_manager.vehicles.items()},
            "users": {str(k): _to_dict(v) for k, v in fleet_manager.users.items()},
            "active_rides": active_rides,
            "degraded_repo": degraded_ids,
        }

    def _restore(self, raw: dict) -> dict:
        return {
            "stations": self._restore_stations(raw.get("stations", {})),
            "vehicles": self._restore_vehicles(raw.get("vehicles", {})),
            "users": {int(k): v for k, v in raw.get("users", {}).items()},
            "active_rides": self._restore_rides(raw.get("active_rides", {})),
            "degraded_repo": raw.get("degraded_repo", []),
        }

    def _restore_stations(self, raw: dict) -> dict[int, dict]:
        result = {}
        for k, v in raw.items():
            sid = int(k)
            result[sid] = {**v, "station_id": sid}
            # TODO: result[sid] = Station(**result[sid])  once models are ready
        return result

    def _restore_vehicles(self, raw: dict) -> dict[str, dict]:
        result = {}
        for k, v in raw.items():
            parsed = {**v}
            if isinstance(parsed.get("last_treated_date"), str):
                parsed["last_treated_date"] = date.fromisoformat(parsed["last_treated_date"])
            result[k] = parsed
            # TODO: result[k] = <Vehicle subclass>(**parsed)  once models are ready
        return result

    def _restore_rides(self, raw: dict) -> dict[int, dict]:
        result = {}
        for k, v in raw.items():
            parsed = {**v}
            for field in ("start_time", "end_time"):
                if isinstance(parsed.get(field), str):
                    parsed[field] = datetime.fromisoformat(parsed[field])
            result[int(k)] = parsed
            # TODO: result[int(k)] = Ride(**parsed)  once models are ready
        return result
