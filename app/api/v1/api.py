"""
API router aggregating all endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import scanner, health, files, duplicates

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scanner.router, prefix="/scanner", tags=["scanner"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(duplicates.router, prefix="/duplicates", tags=["duplicates"])