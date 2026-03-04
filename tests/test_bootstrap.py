from pathlib import Path

import pytest

from src.bootstrap import build_fleet_manager


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
