"""
Duplicate management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

class DuplicateFile(BaseModel):
    id: int
    path: str
    name: str
    size: int
    is_original: bool
    marked_for_deletion: bool

class DuplicateGroup(BaseModel):
    id: int
    hash_value: str
    file_count: int
    total_size: int
    space_wasted: int
    confidence_score: int
    files: List[DuplicateFile]

@router.get("/groups", response_model=List[DuplicateGroup])
async def list_duplicate_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    scan_session_id: Optional[int] = None
):
    """List duplicate groups"""
    return []

@router.get("/groups/{group_id}", response_model=DuplicateGroup)
async def get_duplicate_group(group_id: int):
    """Get specific duplicate group"""
    raise HTTPException(status_code=404, detail="Duplicate group not found")

@router.post("/groups/{group_id}/resolve")
async def resolve_duplicate_group(group_id: int, action: str):
    """Resolve a duplicate group with specified action"""
    valid_actions = ["keep_first", "keep_newest", "keep_largest", "manual"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    return {
        "message": f"Duplicate group {group_id} resolved with action: {action}",
        "group_id": group_id,
        "action": action
    }

@router.get("/stats")
async def get_duplicate_stats():
    """Get duplicate statistics"""
    return {
        "total_duplicates": 0,
        "total_groups": 0,
        "space_wasted": 0,
        "space_recoverable": 0
    }