from pathlib import Path

from src.data.loaders import StationDataLoader, VehicleDataLoader
from src.data.state_serializer import load_state
from src.services.fleet_manager import FleetManager


def build_fleet_manager(
    stations_csv: Path,
    vehicles_csv: Path,
    state_path: Path = Path("data/state.json"),
) -> FleetManager:
    """
    Build and return a FleetManager instance using data loaded from CSV files:
    - Load stations and vehicles using the Data layer loaders
    - Initialize the FleetManager with those objects
    - Fail fast if CSV files are missing or invalid

    Notes:
    - FleetManager initialization is responsible for linking vehicles to stations
      and removing vehicles that require maintenance.
    """
    try:
        stations = StationDataLoader(stations_csv).create_objects()
        vehicles = VehicleDataLoader(vehicles_csv).create_objects()
        fleet_manager = FleetManager(stations=stations, vehicles=vehicles)
        load_state(fleet_manager, state_path)
        return fleet_manager

    except Exception as e:
        raise RuntimeError(f"Bootstrap failed: {e}") from e
