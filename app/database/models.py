"""
Database models for duplicate scanner
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base

class ScanSession(Base):
    __tablename__ = "scan_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scan configuration
    paths = Column(JSON, nullable=False)  # List of paths to scan
    algorithms = Column(JSON, nullable=False)  # List of hash algorithms to use
    chunk_size = Column(Integer, default=8388608)  # 8MB
    workers = Column(Integer, default=4)
    
    # Statistics
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    space_saved = Column(BigInteger, default=0)  # Bytes
    
    # Relationships
    files = relationship("FileRecord", back_populates="scan_session")
    duplicate_groups = relationship("DuplicateGroup", back_populates="scan_session")

class FileRecord(Base):
    __tablename__ = "file_records"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_session_id = Column(Integer, ForeignKey("scan_sessions.id"), nullable=False)
    
    # File information
    path = Column(Text, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    size = Column(BigInteger, nullable=False, index=True)
    modified_time = Column(DateTime(timezone=True), nullable=False)
    created_time = Column(DateTime(timezone=True), nullable=True)
    
    # File type and metadata
    file_type = Column(String(50), nullable=True, index=True)
    mime_type = Column(String(100), nullable=True)
    extension = Column(String(20), nullable=True, index=True)
    
    # Hash values
    xxhash64 = Column(String(16), nullable=True, index=True)  # Fast pre-filter hash
    blake3_hash = Column(String(64), nullable=True, index=True)  # Primary hash
    sha256_hash = Column(String(64), nullable=True)  # Optional secure hash
    
    # Chunked hashing for large files
    chunk_hashes = Column(JSON, nullable=True)  # List of chunk hashes
    
    # Cloud storage information
    cloud_provider = Column(String(50), nullable=True)  # onedrive, dropbox, gdrive, etc.
    cloud_path = Column(Text, nullable=True)
    cloud_id = Column(String(255), nullable=True)
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scan_session = relationship("ScanSession", back_populates="files")
    duplicate_memberships = relationship("DuplicateMembership", back_populates="file_record")

class DuplicateGroup(Base):
    __tablename__ = "duplicate_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_session_id = Column(Integer, ForeignKey("scan_sessions.id"), nullable=False)
    
    # Group identification
    hash_value = Column(String(64), nullable=False, index=True)
    hash_algorithm = Column(String(20), nullable=False)  # blake3, sha256, etc.
    
    # Group metadata
    file_count = Column(Integer, nullable=False)
    total_size = Column(BigInteger, nullable=False)  # Size of one file (all identical)
    space_wasted = Column(BigInteger, nullable=False)  # (file_count - 1) * total_size
    
    # Analysis results
    confidence_score = Column(Integer, default=100)  # 0-100, 100 for exact hash matches
    similarity_type = Column(String(50), default="exact")  # exact, similar, partial
    
    # User actions
    reviewed = Column(Boolean, default=False)
    action_taken = Column(String(50), nullable=True)  # keep_first, keep_newest, manual, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scan_session = relationship("ScanSession", back_populates="duplicate_groups")
    memberships = relationship("DuplicateMembership", back_populates="duplicate_group")

class DuplicateMembership(Base):
    __tablename__ = "duplicate_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    duplicate_group_id = Column(Integer, ForeignKey("duplicate_groups.id"), nullable=False)
    file_record_id = Column(Integer, ForeignKey("file_records.id"), nullable=False)
    
    # Member-specific information
    is_original = Column(Boolean, default=False)  # Which file to keep
    marked_for_deletion = Column(Boolean, default=False)
    deletion_reason = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    duplicate_group = relationship("DuplicateGroup", back_populates="memberships")
    file_record = relationship("FileRecord", back_populates="duplicate_memberships")

class CloudConnection(Base):
    __tablename__ = "cloud_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Connection details
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False, index=True)  # onedrive, dropbox, gdrive
    
    # Authentication
    auth_type = Column(String(50), nullable=False)  # oauth2, api_key, etc.
    encrypted_credentials = Column(Text, nullable=True)  # JSON with encrypted tokens
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    sync_error = Column(Text, nullable=True)
    
    # Configuration
    sync_paths = Column(JSON, nullable=True)  # List of paths to sync
    auto_sync = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())