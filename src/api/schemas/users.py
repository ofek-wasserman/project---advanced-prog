from pydantic import Field

from src.api.schemas.base import StrictBaseModel


class RegisterRequest(StrictBaseModel):
    payment_token: str = Field(..., min_length=1, description="Payment token for registration")


class RegisterResponse(StrictBaseModel):
    user_id: int = Field(..., description="Unique identifier for the registered user")
