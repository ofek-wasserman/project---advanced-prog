"""Ride Management Endpoints.

API layer only: this module defines HTTP endpoints for the ride lifecycle.
It does not contain business logic. It delegates all ride operations to the
service layer (`FleetManager`), and relies on the application's global
exception handlers to map domain/service exceptions to HTTP responses.

Endpoints:
    POST /ride/start
        Start a new ride for a user at the provided (lat, lon).

    POST /ride/end
        End an active ride at the provided (lat, lon). The service layer selects
        the nearest station with a free slot, docks the vehicle, and calculates
        billing.

    GET /rides/active-users
        Placeholder (not implemented in Phase 1 tests unless required).

Error mapping (via global exception handlers):
    - InvalidInputError -> 400
    - NotFoundError     -> 404
    - ConflictError     -> 409

"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_fleet_manager
from src.api.schemas.rides import (
    ActiveUsersResponse,
    EndRideRequest,
    EndRideResponse,
    StartRideRequest,
    StartRideResponse,
)
from src.services.fleet_manager import FleetManager

router = APIRouter()


@router.post("/ride/start", response_model=StartRideResponse, status_code=status.HTTP_200_OK)
async def start_ride(
    req: StartRideRequest,
    fleet_manager: FleetManager = Depends(get_fleet_manager),
) -> StartRideResponse:
    ride, start_station_id = fleet_manager.start_ride(
        user_id=req.user_id,
        location=(req.lat, req.lon),
    )

    vehicle = fleet_manager.vehicles[ride.vehicle_id]
    vehicle_type = type(vehicle).__name__

    return StartRideResponse(
        ride_id=ride.ride_id,
        vehicle_id=ride.vehicle_id,
        vehicle_type=vehicle_type,
        start_station_id=start_station_id,
    )


@router.post("/ride/end", response_model=EndRideResponse, status_code=status.HTTP_200_OK)
async def end_ride(
    req: EndRideRequest,
    fleet_manager: FleetManager = Depends(get_fleet_manager),
) -> EndRideResponse:
    end_station_id, payment_charged = fleet_manager.end_ride(
        ride_id=req.ride_id,
        location=(req.lat, req.lon),
    )

    return EndRideResponse(
        ride_id=req.ride_id,
        end_station_id=end_station_id,
        payment_charged=payment_charged,
    )


@router.get("/rides/active-users", response_model=ActiveUsersResponse)
async def active_users() -> ActiveUsersResponse:
    """Get list of active user IDs.

    Returns:
        ActiveUsersResponse: The list of active user IDs.

    Raises:
        HTTPException: 501 Not Implemented - Feature not yet available.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")
