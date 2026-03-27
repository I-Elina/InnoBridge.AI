from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.db.database import get_db
from app.db.models import User
from app.utils.validators import (
    validate_email,
    validate_designation,
    validate_skill_level,
    validate_interests,
)
from app.utils.response_formatter import success_response, error_response

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str
    designation: str
    skill_level: str
    interests: List[str]


class UserUpdate(BaseModel):
    designation: Optional[str] = None
    skill_level: Optional[str] = None
    interests: Optional[List[str]] = None


def _serialize_user(user: User) -> dict:
    """Convert a User ORM object to a JSON-serializable dict."""
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "designation": user.designation,
        "skill_level": user.skill_level,
        "interests": user.interests or [],
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/create")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user profile."""
    # Validate inputs
    try:
        email = validate_email(payload.email)
        designation = validate_designation(payload.designation)
        skill_level = validate_skill_level(payload.skill_level)
        interests = validate_interests(payload.interests)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Check for duplicate email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Email '{email}' is already registered")

    user = User(
        name=payload.name.strip(),
        email=email,
        designation=designation,
        skill_level=skill_level,
        interests=interests,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return success_response(_serialize_user(user), "User created successfully")


@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Fetch a user profile by UUID."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return success_response(_serialize_user(user), "User fetched successfully")


@router.put("/{user_id}")
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    """Update a user's designation, skill_level, and/or interests."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if payload.designation is not None:
            user.designation = validate_designation(payload.designation)
        if payload.skill_level is not None:
            user.skill_level = validate_skill_level(payload.skill_level)
        if payload.interests is not None:
            user.interests = validate_interests(payload.interests)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    db.commit()
    db.refresh(user)

    return success_response(_serialize_user(user), "User updated successfully")