from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


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
