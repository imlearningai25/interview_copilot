from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    sessions = relationship("Session", back_populates="job",
                            cascade="all, delete-orphan", order_by="Session.started_at.desc()")

    # Partial unique index: at most one active job at a time (PostgreSQL enforces this)
    __table_args__ = (
        Index("uq_one_active_job", "is_active", unique=True,
              postgresql_where=Column("is_active") == True),
    )


class Session(Base):
    __tablename__ = "sessions"

    id         = Column(Integer, primary_key=True, index=True)
    job_id     = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at   = Column(DateTime(timezone=True), nullable=True)

    job     = relationship("Job", back_populates="sessions")
    entries = relationship("QAEntry", back_populates="session",
                           cascade="all, delete-orphan", order_by="QAEntry.asked_at")


class QAEntry(Base):
    __tablename__ = "qa_entries"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    asked_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    question   = Column(Text, nullable=False)
    answer     = Column(Text, nullable=False)

    session = relationship("Session", back_populates="entries")
