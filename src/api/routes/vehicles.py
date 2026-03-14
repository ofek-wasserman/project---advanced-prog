from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_fleet_manager
from src.api.schemas.vehicles import ReportDegradedRequest, ReportDegradedResponse
from src.services.fleet_manager import FleetManager

router = APIRouter()


@router.post(
    "/vehicle/report-degraded",
    response_model=ReportDegradedResponse,
    status_code=status.HTTP_200_OK,
)
async def report_degraded(
    req: ReportDegradedRequest,
    fleet_manager: FleetManager = Depends(get_fleet_manager),
) -> ReportDegradedResponse:
    fleet_manager.report_vehicle_degraded(
        user_id=req.user_id,
        vehicle_id=req.vehicle_id,
    )
    return ReportDegradedResponse(result="ok")
