"""
Announcement endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"],
)


class AnnouncementCreate(BaseModel):
    message: str = Field(min_length=3, max_length=500)
    expires_at: str
    starts_at: Optional[str] = None


class AnnouncementUpdate(BaseModel):
    message: Optional[str] = Field(default=None, min_length=3, max_length=500)
    expires_at: Optional[str] = None
    starts_at: Optional[str] = None


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime for {field_name}. Use ISO 8601 format.",
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _ensure_logged_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _normalize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "message": document["message"],
        "starts_at": document.get("starts_at").isoformat() if document.get("starts_at") else None,
        "expires_at": document["expires_at"].isoformat(),
        "created_at": document["created_at"].isoformat(),
        "updated_at": document["updated_at"].isoformat(),
        "created_by": document.get("created_by"),
    }


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get announcements currently visible to all users."""
    now = datetime.now(timezone.utc)
    query = {
        "expires_at": {"$gt": now},
        "$or": [
            {"starts_at": {"$exists": False}},
            {"starts_at": None},
            {"starts_at": {"$lte": now}},
        ],
    }

    announcements: List[Dict[str, Any]] = []
    for announcement in announcements_collection.find(query).sort("expires_at", 1):
        announcements.append(_normalize_announcement(announcement))

    return announcements


@router.get("", response_model=List[Dict[str, Any]])
def list_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements for management. Requires authenticated teacher."""
    _ensure_logged_teacher(teacher_username)

    announcements: List[Dict[str, Any]] = []
    for announcement in announcements_collection.find({}).sort("updated_at", -1):
        announcements.append(_normalize_announcement(announcement))

    return announcements


@router.post("", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementCreate, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create announcement with optional start date and required expiration date."""
    teacher = _ensure_logged_teacher(teacher_username)

    starts_at = _parse_iso_datetime(payload.starts_at, "starts_at") if payload.starts_at else None
    expires_at = _parse_iso_datetime(payload.expires_at, "expires_at")

    if starts_at and starts_at >= expires_at:
        raise HTTPException(
            status_code=422,
            detail="Start date must be earlier than expiration date.",
        )

    now = datetime.now(timezone.utc)
    document = {
        "message": payload.message.strip(),
        "starts_at": starts_at,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
        "created_by": teacher.get("username", teacher.get("_id")),
    }
    result = announcements_collection.insert_one(document)
    created = announcements_collection.find_one({"_id": result.inserted_id})

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    return _normalize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdate,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Update announcement message and dates. Requires authenticated teacher."""
    _ensure_logged_teacher(teacher_username)

    existing = announcements_collection.find_one({"_id": ObjectId(announcement_id)}) if ObjectId.is_valid(announcement_id) else None
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    provided_fields = payload.__fields_set__
    message = payload.message.strip() if "message" in provided_fields and payload.message is not None else existing["message"]

    if "starts_at" in provided_fields:
        starts_at = _parse_iso_datetime(payload.starts_at, "starts_at") if payload.starts_at else None
    else:
        starts_at = existing.get("starts_at")

    if "expires_at" in provided_fields:
        if payload.expires_at is None:
            raise HTTPException(status_code=422, detail="Expiration date is required")
        expires_at = _parse_iso_datetime(payload.expires_at, "expires_at")
    else:
        expires_at = existing["expires_at"]

    if starts_at and starts_at >= expires_at:
        raise HTTPException(
            status_code=422,
            detail="Start date must be earlier than expiration date.",
        )

    updates = {
        "message": message,
        "starts_at": starts_at,
        "expires_at": expires_at,
        "updated_at": datetime.now(timezone.utc),
    }

    announcements_collection.update_one({"_id": existing["_id"]}, {"$set": updates})
    updated = announcements_collection.find_one({"_id": existing["_id"]})

    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update announcement")

    return _normalize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, Any])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Delete announcement by id. Requires authenticated teacher."""
    _ensure_logged_teacher(teacher_username)

    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")

    result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
