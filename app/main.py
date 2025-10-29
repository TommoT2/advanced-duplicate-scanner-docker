#!/usr/bin/env python3
"""
Advanced Duplicate Scanner - Main FastAPI Application
Enterprise-grade duplicate file detection with cloud integration and MCP tools
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
from typing import Optional

import structlog
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

from app.api.v1.api import api_router
from app.core.config import settings
from app.database.session import engine
from app.database import models
from app.services.scanner_service import ScannerService
from app.services.websocket_manager import WebSocketManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global services
scanner_service: Optional[ScannerService] = None
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global scanner_service
    
    logger.info("Starting Advanced Duplicate Scanner with MCP Integration")
    
    # Initialize database
    try:
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        sys.exit(1)
    
    # Initialize scanner service
    try:
        scanner_service = ScannerService(websocket_manager=websocket_manager)
        await scanner_service.initialize()
        logger.info("Scanner service initialized")
    except Exception as e:
        logger.error("Failed to initialize scanner service", error=str(e))
        sys.exit(1)
    
    # Make scanner service available to the app
    app.state.scanner_service = scanner_service
    app.state.websocket_manager = websocket_manager
    
    yield
    
    # Cleanup
    logger.info("Shutting down Advanced Duplicate Scanner")
    if scanner_service:
        await scanner_service.shutdown()
    logger.info("Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Advanced Duplicate Scanner",
    description="Enterprise-grade duplicate file detection with AI, cloud integration, and MCP tools",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Serve static files (built React app)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def read_root(request: Request):
    """Serve React app or simple HTML interface"""
    static_file = static_dir / "index.html"
    if static_file.exists():
        return FileResponse(str(static_file))
    
    # Fallback simple HTML interface
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Advanced Duplicate Scanner</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
            .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .button { background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
            .button:hover { background: #1d4ed8; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .status.success { background: #dcfce7; color: #166534; }
            .status.error { background: #fef2f2; color: #dc2626; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Advanced Duplicate Scanner</h1>
            <p>Enterprise-grade duplicate file detection with AI and cloud integration</p>
        </div>
        
        <div class="card">
            <h2>Quick Start</h2>
            <p>Welcome to your containerized duplicate scanner! This application runs in Docker and provides:</p>
            <ul>
                <li>🚀 BLAKE3 + xxHash high-performance hashing</li>
                <li>☁️ OneDrive, Dropbox, Google Drive integration</li>
                <li>🤖 AI-powered semantic duplicate detection</li>
                <li>🔧 MCP tool integration for enhanced functionality</li>
            </ul>
            
            <div style="margin-top: 20px;">
                <a href="/api/docs" class="button">📚 API Documentation</a>
                <a href="/api/v1/health" class="button">🏥 Health Check</a>
                <a href="/api/v1/scanner/status" class="button">📊 Scanner Status</a>
            </div>
        </div>
        
        <div class="card">
            <h2>Getting Started</h2>
            <ol>
                <li>Configure your data path in docker-compose.yml (currently mounted at /app/data)</li>
                <li>Set up cloud storage credentials via the API</li>
                <li>Start your first scan using the API endpoints</li>
                <li>Monitor progress in real-time via WebSocket</li>
            </ol>
        </div>
        
        <div class="card">
            <h2>System Information</h2>
            <p><strong>Version:</strong> 1.0.0</p>
            <p><strong>Container:</strong> Docker-based deployment</p>
            <p><strong>Database:</strong> PostgreSQL with Redis caching</p>
            <p><strong>MCP Integration:</strong> Filesystem, Docker, Context7 support</p>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "service": "duplicate-scanner",
        "version": "1.0.0",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "checks": {
            "database": "checking",
            "redis": "checking",
            "filesystem": "checking",
            "scanner_service": "checking"
        }
    }
    
    # Check database connectivity
    try:
        from app.database.session import SessionLocal
        async with SessionLocal() as session:
            await session.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check filesystem access
    try:
        data_path = Path("/app/data")
        if data_path.exists() and data_path.is_dir():
            # Try to list directory
            list(data_path.iterdir())
            health_status["checks"]["filesystem"] = "healthy"
        else:
            health_status["checks"]["filesystem"] = "unhealthy: data directory not accessible"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["filesystem"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check scanner service
    try:
        if hasattr(app.state, 'scanner_service') and app.state.scanner_service:
            service_status = await app.state.scanner_service.get_status()
            health_status["checks"]["scanner_service"] = "healthy"
            health_status["scanner_status"] = service_status
        else:
            health_status["checks"]["scanner_service"] = "unhealthy: service not initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["scanner_service"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            logger.info("Received WebSocket message", data=data)
            
            # Echo back for now (can be extended with specific handlers)
            await websocket_manager.send_personal_message(
                {"type": "echo", "data": data}, websocket
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )