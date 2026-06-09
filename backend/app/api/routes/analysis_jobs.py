import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlmodel import select

from app.api.deps import OwnerDep, SessionDep
from app.core.config import get_settings
from app.models import AnalysisJob, AnalysisResult, Dog, Feedback
from app.schemas import AnalysisJobRead, AnalysisResultRead, FeedbackCreate, FeedbackRead
from app.services.jobs import process_analysis_job, update_habits_from_feedback
from app.services.storage import StorageService

router = APIRouter(prefix="/analysis-jobs", tags=["analysis jobs"])


@router.post("", response_model=AnalysisJobRead)
async def create_analysis_job(
    session: SessionDep,
    owner_id: OwnerDep,
    dog_id: str = Form(...),
    context_tags: str = Form(default="[]"),
    storage_path: str | None = Form(default=None),
    storage_signed_url: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
) -> AnalysisJob:
    dog = session.get(Dog, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")

    try:
        parsed_tags = json.loads(context_tags)
        if not isinstance(parsed_tags, list):
            parsed_tags = []
    except json.JSONDecodeError:
        parsed_tags = []

    local_path = None
    if file:
        local_path = await StorageService().save_upload(file, owner_id=owner_id, dog_id=dog_id)
    elif storage_signed_url:
        local_path = StorageService().download_signed_url(
            storage_signed_url,
            owner_id=owner_id,
            dog_id=dog_id,
        )

    if not local_path and not storage_path:
        raise HTTPException(status_code=400, detail="Provide either a video file or Supabase storage_path")

    job = AnalysisJob(
        owner_id=owner_id,
        dog_id=dog_id,
        storage_path=storage_path,
        local_path=local_path,
        context_tags=parsed_tags,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    if get_settings().run_jobs_inline:
        process_analysis_job(session, job.id)
        session.refresh(job)

    return job


@router.get("/{job_id}", response_model=AnalysisJobRead)
def get_analysis_job(job_id: str, session: SessionDep, owner_id: OwnerDep) -> AnalysisJob:
    job = session.get(AnalysisJob, job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/result", response_model=AnalysisResultRead)
def get_analysis_result(job_id: str, session: SessionDep, owner_id: OwnerDep) -> AnalysisResult:
    result = session.exec(
        select(AnalysisResult).where(
            AnalysisResult.job_id == job_id,
            AnalysisResult.owner_id == owner_id,
        )
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.post("/{job_id}/feedback", response_model=FeedbackRead)
def submit_feedback(
    job_id: str,
    payload: FeedbackCreate,
    session: SessionDep,
    owner_id: OwnerDep,
) -> Feedback:
    job = session.get(AnalysisJob, job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Job not found")
    feedback = Feedback(
        job_id=job.id,
        dog_id=job.dog_id,
        owner_id=owner_id,
        **payload.model_dump(),
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    update_habits_from_feedback(session, feedback)
    return feedback
