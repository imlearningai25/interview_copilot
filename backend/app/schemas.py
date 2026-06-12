from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class JobBase(BaseModel):
    role: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    job_description: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    role: Optional[str] = Field(None, min_length=1, max_length=255)
    company: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = None
    job_description: Optional[str] = None


class JobResponse(JobBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Session / QA schemas ──────────────────────────────────────

class QAEntryCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class QAEntryUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = None


class QAEntryResponse(BaseModel):
    id: int
    session_id: int
    asked_at: datetime
    question: str
    answer: str

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    job_id: int


class SessionResponse(BaseModel):
    id: int
    job_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    entries: List[QAEntryResponse] = []

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    """Lightweight session listing — no entries payload."""
    id: int
    job_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    entry_count: int = 0

    model_config = {"from_attributes": True}
