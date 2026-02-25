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
from src.api.routes.users import router as users_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(rides_router, prefix="/rides", tags=["rides"])
