from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.db.database import get_db
from app.db.models import ConnectRequest, User, Paper
from app.utils.response_formatter import success_response

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────

class InterestRequest(BaseModel):
    user_id: str
    paper_id: str
    message: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str


# ─── POST /connect/interest ──────────────────────────────

@router.post("/interest")
def express_interest(payload: InterestRequest, db: Session = Depends(get_db)):

    # Validate UUID
    try:
        user_uuid = uuid.UUID(payload.user_id)
        paper_uuid = uuid.UUID(payload.paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Check user
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check paper
    paper = db.query(Paper).filter(Paper.id == paper_uuid).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Prevent duplicate
    existing = db.query(ConnectRequest).filter(
        ConnectRequest.user_id == user_uuid,
        ConnectRequest.paper_id == paper_uuid
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Already expressed interest")

    # Create request
    connect_request = ConnectRequest(
        user_id=user_uuid,
        paper_id=paper_uuid,
        message=payload.message,
        status="open"
    )

    db.add(connect_request)
    db.commit()
    db.refresh(connect_request)

    return success_response({
        "request_id": str(connect_request.id),
        "status": connect_request.status
    }, "Interest added successfully")


# ─── GET /connect/paper/{paper_id} ───────────────────────

@router.get("/paper/{paper_id}")
def get_interested_users(paper_id: str, db: Session = Depends(get_db)):

    try:
        paper_uuid = uuid.UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    paper = db.query(Paper).filter(Paper.id == paper_uuid).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    results = (
        db.query(ConnectRequest, User)
        .join(User, ConnectRequest.user_id == User.id)
        .filter(ConnectRequest.paper_id == paper_uuid)
        .all()
    )

    users = [
        {
            "request_id": str(req.id),
            "status": req.status,
            "message": req.message,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
            }
        }
        for req, user in results
    ]

    return success_response({
        "paper_id": paper_id,
        "total": len(users),
        "users": users
    })


# ─── PUT /connect/request/{id} ───────────────────────────

@router.put("/request/{request_id}")
def update_request(request_id: str, payload: UpdateStatusRequest, db: Session = Depends(get_db)):

    try:
        request_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request_id")

    if payload.status not in ["open", "matched", "closed"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    request = db.query(ConnectRequest).filter(ConnectRequest.id == request_uuid).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = payload.status
    db.commit()
    db.refresh(request)

    return success_response({
        "request_id": str(request.id),
        "status": request.status
    }, "Status updated")


# ─── GET /connect/user/{user_id} ─────────────────────────

@router.get("/user/{user_id}")
def get_user_interests(user_id: str, db: Session = Depends(get_db)):

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    results = (
        db.query(ConnectRequest, Paper)
        .join(Paper, ConnectRequest.paper_id == Paper.id)
        .filter(ConnectRequest.user_id == user_uuid)
        .all()
    )

    papers = [
        {
            "request_id": str(req.id),
            "status": req.status,
            "paper": {
                "id": str(paper.id),
                "title": paper.title
            }
        }
        for req, paper in results
    ]

    return success_response({
        "user_id": user_id,
        "total": len(papers),
        "papers": papers
    })