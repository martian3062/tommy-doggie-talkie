import json
from dataclasses import dataclass

from litestar import Router, get, post
from litestar.datastructures import UploadFile
from litestar.di import NamedDependency
from litestar.exceptions import HTTPException
from litestar.params import FromPath, MultipartBody
from litestar.status_codes import HTTP_200_OK
from sqlmodel import Session, select

from app.core.config import get_settings
from app.models import AnalysisJob, AnalysisResult, Dog, Feedback
from app.schemas import AnalysisJobRead, AnalysisResultRead, FeedbackCreate, FeedbackRead
from app.services.jobs import process_analysis_job, update_habits_from_feedback
from app.services.storage import StorageService


@dataclass
class AnalysisJobForm:
    dog_id: str = ""
    context_tags: str = "[]"
    storage_path: str | None = None
    storage_signed_url: str | None = None
    file: UploadFile | None = None


@post("/", status_code=HTTP_200_OK)
async def create_analysis_job(
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
    data: MultipartBody[AnalysisJobForm],
) -> AnalysisJobRead:
    dog = session.get(Dog, data.dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")

    try:
        parsed_tags = json.loads(data.context_tags)
        if not isinstance(parsed_tags, list):
            parsed_tags = []
    except json.JSONDecodeError:
        parsed_tags = []

    local_path = None
    if data.file:
        local_path = await StorageService().save_upload(
            data.file, owner_id=owner_id, dog_id=data.dog_id
        )
    elif data.storage_signed_url:
        local_path = StorageService().download_signed_url(
            data.storage_signed_url,
            owner_id=owner_id,
            dog_id=data.dog_id,
        )

    if not local_path and not data.storage_path:
        raise HTTPException(status_code=400, detail="Provide either a video file or Supabase storage_path")

    job = AnalysisJob(
        owner_id=owner_id,
        dog_id=data.dog_id,
        storage_path=data.storage_path,
        local_path=local_path,
        context_tags=parsed_tags,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    if get_settings().run_jobs_inline:
        process_analysis_job(session, job.id)
        session.refresh(job)

    return AnalysisJobRead.model_validate(job, from_attributes=True)


@get("/{job_id:str}", sync_to_thread=True)
def get_analysis_job(
    job_id: FromPath[str],
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> AnalysisJobRead:
    job = session.get(AnalysisJob, job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisJobRead.model_validate(job, from_attributes=True)


@get("/{job_id:str}/result", sync_to_thread=True)
def get_analysis_result(
    job_id: FromPath[str],
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> AnalysisResultRead:
    result = session.exec(
        select(AnalysisResult).where(
            AnalysisResult.job_id == job_id,
            AnalysisResult.owner_id == owner_id,
        )
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return AnalysisResultRead.model_validate(result, from_attributes=True)


@post("/{job_id:str}/feedback", status_code=HTTP_200_OK, sync_to_thread=True)
def submit_feedback(
    job_id: FromPath[str],
    data: FeedbackCreate,
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> FeedbackRead:
    job = session.get(AnalysisJob, job_id)
    if not job or job.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Job not found")
    feedback = Feedback(
        job_id=job.id,
        dog_id=job.dog_id,
        owner_id=owner_id,
        **data.model_dump(),
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    update_habits_from_feedback(session, feedback)
    return FeedbackRead.model_validate(feedback, from_attributes=True)


analysis_jobs_router = Router(
    path="/api/v1/analysis-jobs",
    tags=["analysis jobs"],
    route_handlers=[
        create_analysis_job,
        get_analysis_job,
        get_analysis_result,
        submit_feedback,
    ],
)
