"""CRUD for server-side chat session persistence."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import ChatSession, User

router = APIRouter(prefix="/chat/sessions", tags=["chat-sessions"])


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New conversation"
    messages: list = []


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[list] = None


class ChatSessionOut(BaseModel):
    id: int
    title: str
    messages: list
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[ChatSessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
        .all()
    )
    return [
        ChatSessionOut(
            id=r.id,
            title=r.title or "New conversation",
            messages=r.messages or [],
            created_at=r.created_at.isoformat() if r.created_at else "",
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        )
        for r in rows
    ]


@router.post("", response_model=ChatSessionOut, status_code=201)
def create_session(
    body: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(
        user_id=current_user.id,
        title=body.title or "New conversation",
        messages=body.messages,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionOut(
        id=session.id,
        title=session.title,
        messages=session.messages or [],
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
    )


@router.get("/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "Session not found")
    return ChatSessionOut(
        id=s.id,
        title=s.title,
        messages=s.messages or [],
        created_at=s.created_at.isoformat() if s.created_at else "",
        updated_at=s.updated_at.isoformat() if s.updated_at else "",
    )


@router.put("/{session_id}", response_model=ChatSessionOut)
def update_session(
    session_id: int,
    body: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "Session not found")
    if body.title is not None:
        s.title = body.title
    if body.messages is not None:
        s.messages = body.messages
    db.commit()
    db.refresh(s)
    return ChatSessionOut(
        id=s.id,
        title=s.title,
        messages=s.messages or [],
        created_at=s.created_at.isoformat() if s.created_at else "",
        updated_at=s.updated_at.isoformat() if s.updated_at else "",
    )


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "Session not found")
    db.delete(s)
    db.commit()
