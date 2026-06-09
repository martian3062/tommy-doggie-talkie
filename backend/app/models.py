from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


def new_id() -> str:
    return str(uuid4())


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Dog(SQLModel, table=True):
    __tablename__ = "dogs"

    id: str = Field(default_factory=new_id, primary_key=True)
    owner_id: str = Field(index=True)
    name: str
    breed: str | None = None
    age_years: float | None = None
    sex: str | None = None
    routines: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    known_habits: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisJob(SQLModel, table=True):
    __tablename__ = "analysis_jobs"

    id: str = Field(default_factory=new_id, primary_key=True)
    owner_id: str = Field(index=True)
    dog_id: str = Field(index=True)
    status: JobStatus = Field(default=JobStatus.queued, index=True)
    progress: float = 0.0
    storage_path: str | None = None
    local_path: str | None = None
    context_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: str = Field(default_factory=new_id, primary_key=True)
    job_id: str = Field(index=True, unique=True)
    dog_id: str = Field(index=True)
    owner_id: str = Field(index=True)
    top_predictions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    uncertainty_reason: str | None = None
    needs_feedback: bool = True
    evidence_timeline: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    raw_signals: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"

    id: str = Field(default_factory=new_id, primary_key=True)
    job_id: str = Field(index=True)
    dog_id: str = Field(index=True)
    owner_id: str = Field(index=True)
    selected_label: str
    is_correct: bool | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HabitSummary(SQLModel, table=True):
    __tablename__ = "habit_summaries"

    id: str = Field(default_factory=new_id, primary_key=True)
    dog_id: str = Field(index=True, unique=True)
    owner_id: str = Field(index=True)
    label_counts: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    recent_notes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
