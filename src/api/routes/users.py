from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_fleet_manager
from src.api.schemas.users import RegisterRequest, RegisterResponse
from src.services.fleet_manager import FleetManager

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_200_OK)
async def register_user(
    req: RegisterRequest,
    fleet_manager: FleetManager = Depends(get_fleet_manager),
) -> RegisterResponse:
    try:
        user_id = fleet_manager.register_user(req.payment_token)
        return RegisterResponse(user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
