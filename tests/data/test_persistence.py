from datetime import date, datetime

from src.data.persistence import SnapshotManager

SAMPLE_SNAPSHOT = {
    "stations": {
        "1": {"station_id": 1, "name": "Dizengoff Sq", "lat": 32.0796, "lon": 34.7739, "max_capacity": 10},
    },
    "vehicles": {
        "V001": {
            "vehicle_id": "V001", "type": "BICYCLE", "status": "AVAILABLE",
            "rides_since_last_treated": 2,
            "last_treated_date": date(2026, 2, 1),
            "station_id": 1, "charge_pct": None,
        },
        "V006": {
            "vehicle_id": "V006", "type": "E_BIKE", "status": "AVAILABLE",
            "rides_since_last_treated": 1,
            "last_treated_date": date(2026, 2, 18),
            "station_id": 1, "charge_pct": 85,
        },
    },
    "users": {
        "42": {"user_id": 42, "payment_token": "tok_test_abc"},
    },
    "active_rides": {
        "7": {
            "ride_id": 7, "user_id": 42, "vehicle_id": "V006",
            "start_time": datetime(2026, 2, 24, 10, 0, 0),
            "end_time": None,
            "start_station_id": 1, "end_station_id": None,
            "reported_degraded": False, "price": None,
        }
    },
    "degraded_repo": ["V004"],
}


class TestSnapshotManager:

    def test_returns_none_when_no_file(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        assert sm.load() is None

    def test_exists_false_before_save(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        assert sm.exists() is False

    def test_exists_true_after_save(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        assert sm.exists() is True

    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "snapshot.json"
        SnapshotManager(path).save(SAMPLE_SNAPSHOT)
        assert path.exists()

    def test_station_round_trip(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        result = sm.load()
        assert 1 in result["stations"]
        assert result["stations"][1]["name"] == "Dizengoff Sq"
        assert result["stations"][1]["max_capacity"] == 10

    def test_vehicle_charge_pct_preserved(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        result = sm.load()
        assert result["vehicles"]["V001"]["charge_pct"] is None
        assert result["vehicles"]["V006"]["charge_pct"] == 85

    def test_date_restored_as_date_object(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        result = sm.load()
        treated = result["vehicles"]["V001"]["last_treated_date"]
        assert isinstance(treated, date)
        assert treated == date(2026, 2, 1)

    def test_ride_start_time_restored_as_datetime(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        result = sm.load()
        ride = result["active_rides"][7]
        assert isinstance(ride["start_time"], datetime)

    def test_user_keys_are_ints(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        result = sm.load()
        assert 42 in result["users"]

    def test_degraded_repo_preserved(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        result = sm.load()
        assert "V004" in result["degraded_repo"]

    def test_delete_removes_file(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.save(SAMPLE_SNAPSHOT)
        sm.delete()
        assert not sm.exists()

    def test_delete_is_safe_when_no_file(self, tmp_path):
        sm = SnapshotManager(tmp_path / "snapshot.json")
        sm.delete()  # should not raise
