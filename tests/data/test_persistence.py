"""Tests for SnapshotManager (src/data/persistence.py)"""

from datetime import date, datetime

import pytest

from src.data.persistence import SnapshotManager

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

EMPTY_SNAPSHOT = {
    "stations": {},
    "vehicles": {},
    "users": {},
    "active_rides": {},
    "degraded_repo": [],
}


@pytest.fixture
def sm(tmp_path):
    return SnapshotManager(tmp_path / "snap.json")


# ---------------------------------------------------------------------------
# File lifecycle: exists / save / delete
# ---------------------------------------------------------------------------


class TestFileLifecycle:
    def test_exists_false_before_save(self, sm):
        assert sm.exists() is False

    def test_load_returns_none_before_save(self, sm):
        assert sm.load() is None

    def test_save_creates_file(self, sm):
        sm.save(EMPTY_SNAPSHOT)
        assert sm.exists() is True

    def test_delete_removes_file(self, sm):
        sm.save(EMPTY_SNAPSHOT)
        sm.delete()
        assert sm.exists() is False

    def test_delete_when_no_file_does_not_raise(self, sm):
        sm.delete()  # must not raise


# ---------------------------------------------------------------------------
# Round-trip: empty snapshot
# ---------------------------------------------------------------------------


class TestEmptyRoundTrip:
    def test_all_keys_present(self, sm):
        sm.save(EMPTY_SNAPSHOT)
        result = sm.load()
        assert set(result.keys()) == {"stations", "vehicles", "users", "active_rides", "degraded_repo"}

    def test_all_collections_empty(self, sm):
        sm.save(EMPTY_SNAPSHOT)
        result = sm.load()
        assert result["stations"] == {}
        assert result["vehicles"] == {}
        assert result["users"] == {}
        assert result["active_rides"] == {}
        assert result["degraded_repo"] == []


# ---------------------------------------------------------------------------
# Vehicles: date parsing and field preservation
# ---------------------------------------------------------------------------


class TestVehicleRestore:
    VEHICLE_SNAPSHOT = {
        **EMPTY_SNAPSHOT,
        "vehicles": {
            "V001": {
                "vehicle_id": "V001",
                "status": "available",
                "rides_since_last_treated": 3,
                "last_treated_date": date(2025, 1, 16),
                "station_id": 1,
                "active_ride_id": None,
            }
        },
    }

    def test_last_treated_date_restored_as_date(self, sm):
        sm.save(self.VEHICLE_SNAPSHOT)
        last_treated = sm.load()["vehicles"]["V001"]["last_treated_date"]
        assert isinstance(last_treated, date)

    def test_last_treated_date_value_correct(self, sm):
        sm.save(self.VEHICLE_SNAPSHOT)
        last_treated = sm.load()["vehicles"]["V001"]["last_treated_date"]
        assert last_treated == date(2025, 1, 16)

    def test_vehicle_fields_preserved(self, sm):
        sm.save(self.VEHICLE_SNAPSHOT)
        v = sm.load()["vehicles"]["V001"]
        assert v["vehicle_id"] == "V001"
        assert v["rides_since_last_treated"] == 3
        assert v["station_id"] == 1
        assert v["active_ride_id"] is None

    def test_vehicle_keys_are_strings(self, sm):
        sm.save(self.VEHICLE_SNAPSHOT)
        assert all(isinstance(k, str) for k in sm.load()["vehicles"])


# ---------------------------------------------------------------------------
# Rides: datetime parsing and field preservation
# ---------------------------------------------------------------------------


class TestRideRestore:
    START = datetime(2026, 3, 1, 10, 0, 0)
    END = datetime(2026, 3, 1, 10, 30, 0)

    def _snap(self, end_time):
        return {
            **EMPTY_SNAPSHOT,
            "active_rides": {
                "42": {
                    "ride_id": 42,
                    "user_id": 1,
                    "vehicle_id": "V001",
                    "start_station_id": 5,
                    "start_time": self.START,
                    "end_time": end_time,
                    "price": None,
                    "reported_degraded": False,
                }
            },
        }

    def test_start_time_restored_as_datetime(self, sm):
        sm.save(self._snap(None))
        restored = sm.load()["active_rides"][42]["start_time"]
        assert isinstance(restored, datetime)
        assert restored == self.START

    def test_end_time_none_preserved(self, sm):
        sm.save(self._snap(None))
        assert sm.load()["active_rides"][42]["end_time"] is None

    def test_end_time_restored_as_datetime(self, sm):
        sm.save(self._snap(self.END))
        restored = sm.load()["active_rides"][42]["end_time"]
        assert isinstance(restored, datetime)
        assert restored == self.END

    def test_ride_keys_are_ints(self, sm):
        sm.save(self._snap(None))
        assert all(isinstance(k, int) for k in sm.load()["active_rides"])


# ---------------------------------------------------------------------------
# Stations: key and field restoration
# ---------------------------------------------------------------------------


class TestStationRestore:
    STATION_SNAPSHOT = {
        **EMPTY_SNAPSHOT,
        "stations": {
            "5": {
                "container_id": 5,
                "name": "Dizengoff Sq",
                "lat": 32.0796,
                "lon": 34.7739,
                "max_capacity": 10,
            }
        },
    }

    def test_station_keys_are_ints(self, sm):
        sm.save(self.STATION_SNAPSHOT)
        assert all(isinstance(k, int) for k in sm.load()["stations"])

    def test_station_id_injected(self, sm):
        sm.save(self.STATION_SNAPSHOT)
        assert sm.load()["stations"][5]["station_id"] == 5


# ---------------------------------------------------------------------------
# Users and degraded repo
# ---------------------------------------------------------------------------


class TestUsersAndDegradedRepo:
    def test_user_keys_are_ints(self, sm):
        snap = {**EMPTY_SNAPSHOT, "users": {"7": {"user_id": 7, "payment_token": "tok_x"}}}
        sm.save(snap)
        assert all(isinstance(k, int) for k in sm.load()["users"])

    def test_degraded_repo_preserved(self, sm):
        snap = {**EMPTY_SNAPSHOT, "degraded_repo": ["V010", "V011"]}
        sm.save(snap)
        assert sm.load()["degraded_repo"] == ["V010", "V011"]
