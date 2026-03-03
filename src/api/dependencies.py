from fastapi import Request

from src.services.fleet_manager import FleetManager


def get_fleet_manager(request: Request) -> FleetManager:
    return request.app.state.fleet_manager