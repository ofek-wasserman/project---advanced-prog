"""API Layer - FastAPI Endpoints Module.

This package contains all HTTP REST API endpoints for the vehicle sharing system.
It uses FastAPI to provide async endpoints that handle user registration, ride
management, and system health monitoring.

Modules:
    router: Main API router that aggregates all route handlers
    routes: Sub-package containing route handlers organized by domain
        - health: Health check endpoints
        - users: User management endpoints
        - rides: Ride management endpoints

Example:
    The API is initialized and run through the main application module::

        from src.api.router import api_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(api_router)

Note:
    All endpoints are async to support concurrent request handling.
    Authentication and validation will be added in future iterations.
"""
