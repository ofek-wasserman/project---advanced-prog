from fastapi import FastAPI

from src.api.router import api_router

app = FastAPI(
    title="Vehicle Sharing API",
    description="API for managing vehicle sharing services",
    version="1.0.0",
)
app.include_router(api_router)
