from typing import Literal

from pydantic import Field

from src.api.schemas.base import StrictBaseModel


class ReportDegradedRequest(StrictBaseModel):
    user_id: int = Field(..., gt=0)
    vehicle_id: str = Field(..., min_length=1)


class ReportDegradedResponse(StrictBaseModel):
    result: Literal["ok"]
