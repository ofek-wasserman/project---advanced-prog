"""API Router - Aggregates all route handlers.

This module creates the main API router that combines all route handlers from
the different domains (health, users, rides) under their respective prefixes
and tags for organized API documentation.

Attributes:
    api_router (APIRouter): The main FastAPI router that combines all sub-routers.
"""

from fastapi import APIRouter

from src.api.routes.health import router as health_router
from src.api.routes.rides import router as rides_router
from src.api.routes.stations import router as stations_router  # new
from src.api.routes.users import router as users_router
from src.api.routes.vehicles import router as vehicles_router  # new

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(rides_router, tags=["rides"])
api_router.include_router(stations_router, tags=["stations"])
api_router.include_router(vehicles_router, tags=["vehicles"])  # new
