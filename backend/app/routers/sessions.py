from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Job, QAEntry, Session as SessionModel
from ..schemas import (
    QAEntryCreate, QAEntryResponse, QAEntryUpdate,
    SessionCreate, SessionResponse, SessionSummary,
)


class BulkDeleteRequest(BaseModel):
    ids: List[int]

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    job = db.get(Job, data.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    session = SessionModel(job_id=data.job_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=List[SessionSummary])
def list_sessions(job_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(
        SessionModel,
        func.count(QAEntry.id).label("entry_count"),
    ).outerjoin(QAEntry, QAEntry.session_id == SessionModel.id)

    if job_id is not None:
        q = q.filter(SessionModel.job_id == job_id)

    rows = q.group_by(SessionModel.id).order_by(SessionModel.started_at.desc()).all()

    results = []
    for session, count in rows:
        results.append(SessionSummary(
            id=session.id,
            job_id=session.job_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            entry_count=count,
        ))
    return results


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = (
        db.query(SessionModel)
        .options(joinedload(SessionModel.entries))
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("", status_code=204)
def bulk_delete_sessions(body: BulkDeleteRequest, db: Session = Depends(get_db)):
    db.query(SessionModel).filter(SessionModel.id.in_(body.ids)).delete(synchronize_session=False)
    db.commit()


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()


@router.patch("/{session_id}/end", response_model=SessionResponse)
def end_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/entries", response_model=QAEntryResponse, status_code=201)
def add_entry(session_id: int, data: QAEntryCreate, db: Session = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    entry = QAEntry(session_id=session_id, question=data.question, answer=data.answer)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{session_id}/entries/{entry_id}", response_model=QAEntryResponse)
def update_entry(
    session_id: int, entry_id: int, data: QAEntryUpdate, db: Session = Depends(get_db)
):
    entry = (
        db.query(QAEntry)
        .filter(QAEntry.id == entry_id, QAEntry.session_id == session_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if data.question is not None:
        entry.question = data.question
    if data.answer is not None:
        entry.answer = data.answer
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{session_id}/entries/{entry_id}", status_code=204)
def delete_entry(session_id: int, entry_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(QAEntry)
        .filter(QAEntry.id == entry_id, QAEntry.session_id == session_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
