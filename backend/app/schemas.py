from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import JobStatus


class DogCreate(BaseModel):
    name: str = Field(min_length=1)
    breed: str | None = None
    breed_source: str = "unknown"
    breed_confidence: float | None = Field(default=None, ge=0, le=1)
    breed_predictions: list[dict[str, Any]] = Field(default_factory=list)
    breed_behavior_profile: dict[str, Any] = Field(default_factory=dict)
    age_years: float | None = Field(default=None, ge=0)
    sex: str | None = None
    routines: dict[str, Any] = Field(default_factory=dict)
    known_habits: dict[str, Any] = Field(default_factory=dict)


class DogRead(DogCreate):
    id: str
    owner_id: str
    created_at: datetime


class Prediction(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class AnalysisJobRead(BaseModel):
    id: str
    dog_id: str
    status: JobStatus
    progress: float
    storage_path: str | None = None
    local_path: str | None = None
    context_tags: list[str] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisResultRead(BaseModel):
    job_id: str
    dog_id: str
    top_predictions: list[Prediction]
    uncertainty_reason: str | None = None
    needs_feedback: bool
    evidence_timeline: list[dict[str, Any]] = Field(default_factory=list)
    raw_signals: dict[str, Any] = Field(default_factory=dict)


class FeedbackCreate(BaseModel):
    selected_label: str
    is_correct: bool | None = None
    note: str | None = None


class FeedbackRead(FeedbackCreate):
    id: str
    job_id: str
    dog_id: str
    owner_id: str
    created_at: datetime


class HabitSummaryRead(BaseModel):
    dog_id: str
    label_counts: dict[str, int] = Field(default_factory=dict)
    recent_notes: list[str] = Field(default_factory=list)
    updated_at: datetime


class RetrainResponse(BaseModel):
    dog_id: str
    queued: bool
    message: str


class BreedPrediction(BaseModel):
    breed: str
    confidence: float = Field(ge=0, le=1)
    source: str


class BreedProfileRead(BaseModel):
    slug: str
    display_name: str
    group: str
    energy_level: str
    behavior_biases: dict[str, float]
    common_patterns: list[str]
    health_watch: list[str]
    interpretation_notes: list[str]


class BreedDetectionRead(BaseModel):
    dog_id: str
    breed_predictions: list[BreedPrediction]
    selected_breed: str | None = None
    breed_source: str
    behavior_profile: BreedProfileRead | None = None
