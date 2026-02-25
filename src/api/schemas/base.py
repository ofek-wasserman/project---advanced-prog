from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",  # reject unknown fields instead of ignoring them
        strict=True,  # enforce strict types (no "123" -> int coercion)
    )
