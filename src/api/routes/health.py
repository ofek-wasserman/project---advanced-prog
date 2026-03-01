"""Health Check Endpoints.

This module provides endpoints for monitoring the health and availability of the
API service. These endpoints are used for load balancers, orchestration platforms,
and monitoring systems to determine if the application is running and responsive.

Endpoints:
    GET /health: Returns the current health status of the application.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Check the health status of the API.

    This endpoint indicates whether the API is running and available to serve
    requests. It performs no complex operations and should respond immediately.

    Returns:
        dict[str, str]: A dictionary with status information.
            Keys:
                - status (str): Always returns "ok" when the API is healthy.

    Example:
        >>> response = await health()
        >>> response
        {"status": "ok"}
    """
    return {"status": "ok"}
