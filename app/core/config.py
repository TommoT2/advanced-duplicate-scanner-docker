"""
Application configuration using Pydantic settings
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Advanced Duplicate Scanner"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "sqlite:///app/db/duplicates.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Scanner configuration
    SCANNER_WORKERS: int = 4
    SCANNER_CHUNK_SIZE: int = 8 * 1024 * 1024  # 8MB
    SCANNER_MAX_FILE_SIZE: int = 10 * 1024 * 1024 * 1024  # 10GB
    
    # Cloud storage
    RCLONE_CONFIG_PATH: str = "/app/config/rclone.conf"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    
    # File paths
    DATA_PATH: str = "/app/data"
    LOG_PATH: str = "/app/logs"
    
    # MCP Integration
    MCP_ENABLED: bool = True
    MCP_TIMEOUT: int = 30
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if v.startswith("sqlite"):
            # Ensure SQLite database directory exists
            import os
            from pathlib import Path
            db_path = Path(v.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()