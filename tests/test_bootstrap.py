from pathlib import Path

import pytest

from src.bootstrap import build_fleet_manager
from src.data.state_serializer import save_state


def test_bootstrap_loads_data() -> None:
    """
    Smoke test verifying that bootstrap loads stations and vehicles from CSV.
    """
    fm = build_fleet_manager(
        stations_csv=Path("data/stations.csv"),
        vehicles_csv=Path("data/vehicles.csv"),
    )

    assert len(fm.stations) > 0
    assert len(fm.vehicles) > 0


def test_bootstrap_fails_fast_on_missing_csv() -> None:
    """
    Bootstrap should fail fast if a CSV file is missing.
    """
    with pytest.raises(RuntimeError):
        build_fleet_manager(
            stations_csv=Path("data/missing.csv"),
            vehicles_csv=Path("data/vehicles.csv"),
        )


def test_bootstrap_applies_persisted_state_on_restart(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"

    fm = build_fleet_manager(
        stations_csv=Path("data/stations.csv"),
        vehicles_csv=Path("data/vehicles.csv"),
        state_path=state_path,
    )

    start_location = (fm.stations[1].lat, fm.stations[1].lon)
    user1 = fm.register_user("tok_u1")
    user2 = fm.register_user("tok_u2")
    active_ride, _ = fm.start_ride(user_id=user1, location=start_location)
    save_state(fm, state_path)

    restarted = build_fleet_manager(
        stations_csv=Path("data/stations.csv"),
        vehicles_csv=Path("data/vehicles.csv"),
        state_path=state_path,
    )

    # users restored
    assert sorted(restarted.users.keys()) == [1, 2]
    assert restarted.users[1].payment_token == "tok_u1"
    assert restarted.users[2].payment_token == "tok_u2"

    # active rides restored
    assert active_ride.ride_id in restarted.active_rides.rides
    restored_ride = restarted.active_rides.rides[active_ride.ride_id]
    assert restored_ride.user_id == user1
    assert restored_ride.vehicle_id == active_ride.vehicle_id

    # vehicles restored for in-ride state
    restored_vehicle = restarted.vehicles[active_ride.vehicle_id]
    assert restored_vehicle.active_ride_id == active_ride.ride_id
    assert restored_vehicle.station_id is None

    # no duplication/corruption in runtime location model
    station_vehicle_ids = set().union(
        *(station.get_vehicle_ids() for station in restarted.stations.values())
    )
    active_vehicle_ids = {ride.vehicle_id for ride in restarted.active_rides.rides.values()}
    degraded_vehicle_ids = restarted.degraded_repo.get_vehicle_ids()

    assert station_vehicle_ids.isdisjoint(active_vehicle_ids)
    assert station_vehicle_ids.isdisjoint(degraded_vehicle_ids)
    assert active_vehicle_ids.isdisjoint(degraded_vehicle_ids)
    assert (
        len(station_vehicle_ids | active_vehicle_ids | degraded_vehicle_ids)
        == len(restarted.vehicles)
    )

    # ID counters continue after restart without collisions
    new_user_id = restarted.register_user("tok_u3")
    assert new_user_id > user2
    next_ride, _ = restarted.start_ride(user_id=user2, location=start_location)
    assert next_ride.ride_id > active_ride.ride_id
