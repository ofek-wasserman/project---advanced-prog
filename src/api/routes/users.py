from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_fleet_manager
from src.api.schemas.users import RegisterRequest, RegisterResponse
from src.services.fleet_manager import FleetManager

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    req: RegisterRequest,
    fleet_manager: FleetManager = Depends(get_fleet_manager),
) -> RegisterResponse:
    user_id = fleet_manager.register_user(req.payment_token)
    return RegisterResponse(user_id=user_id)
