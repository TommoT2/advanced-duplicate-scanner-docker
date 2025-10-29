"""
File management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

class FileInfo(BaseModel):
    id: int
    path: str
    name: str
    size: int
    modified_time: str
    file_type: Optional[str] = None
    blake3_hash: Optional[str] = None
    xxhash64: Optional[str] = None

@router.get("/", response_model=List[FileInfo])
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    scan_session_id: Optional[int] = None
):
    """List processed files"""
    return []

@router.get("/{file_id}", response_model=FileInfo)
async def get_file(file_id: int):
    """Get specific file information"""
    raise HTTPException(status_code=404, detail="File not found")

@router.delete("/{file_id}")
async def delete_file(file_id: int):
    """Delete a file (mark for deletion)"""
    return {"message": f"File {file_id} marked for deletion"}

@router.get("/browse/{path:path}")
async def browse_path(path: str):
    """Browse files in a specific path"""
    return {
        "path": path,
        "files": [],
        "directories": []
    }