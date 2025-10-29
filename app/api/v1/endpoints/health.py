"""
Health check endpoints
"""

from fastapi import APIRouter
from app.core.config import settings
import asyncio

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": asyncio.get_event_loop().time()
    }