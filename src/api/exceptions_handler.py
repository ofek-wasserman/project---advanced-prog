# src/api/exceptions_handler.py
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Import your domain/service exception base types.
# If you don't have them yet, create:
#   src/domain/exceptions.py -> InvalidInputError, NotFoundError, ConflictError
from src.domain.exceptions import ConflictError, InvalidInputError, NotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.
    API layer only: maps domain/service exceptions to HTTP responses.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Convert FastAPI/Pydantic validation errors from 422 -> 400
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    @app.exception_handler(InvalidInputError)
    async def invalid_input_handler(
        _request: Request, exc: InvalidInputError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, _exc: Exception
    ) -> JSONResponse:
        # Do not leak stack traces / internals to clients
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
