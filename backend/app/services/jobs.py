from datetime import datetime

from sqlmodel import Session, select

from app.models import AnalysisJob, AnalysisResult, Dog, Feedback, HabitSummary, JobStatus
from app.services.ml_pipeline import analyze_media
from app.services.storage import StorageService


def process_analysis_job(session: Session, job_id: str) -> None:
    job = session.get(AnalysisJob, job_id)
    if not job:
        return
    job.status = JobStatus.running
    job.progress = 0.2
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()

    try:
        media_path = job.local_path
        if not media_path and job.storage_path:
            media_path = StorageService().download_supabase_object(
                job.storage_path,
                owner_id=job.owner_id,
                dog_id=job.dog_id,
            )
            job.local_path = media_path
            job.progress = 0.4
            session.add(job)
            session.commit()

        dog = session.get(Dog, job.dog_id)
        dog_profile = dog.model_dump() if dog else {}
        result_payload = analyze_media(media_path, job.context_tags, dog_profile=dog_profile)
        result = AnalysisResult(
            job_id=job.id,
            dog_id=job.dog_id,
            owner_id=job.owner_id,
            **result_payload,
        )
        session.add(result)
        job.status = JobStatus.done
        job.progress = 1.0
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()
    except Exception as exc:
        job.status = JobStatus.failed
        job.progress = 1.0
        job.error_message = str(exc)
        job.updated_at = datetime.utcnow()
        session.add(job)
        session.commit()


def update_habits_from_feedback(session: Session, feedback: Feedback) -> HabitSummary:
    habit = session.exec(
        select(HabitSummary).where(
            HabitSummary.dog_id == feedback.dog_id,
            HabitSummary.owner_id == feedback.owner_id,
        )
    ).first()
    if not habit:
        habit = HabitSummary(dog_id=feedback.dog_id, owner_id=feedback.owner_id)
    counts = dict(habit.label_counts)
    counts[feedback.selected_label] = counts.get(feedback.selected_label, 0) + 1
    habit.label_counts = counts
    if feedback.note:
        habit.recent_notes = [feedback.note, *habit.recent_notes][:10]
    habit.updated_at = datetime.utcnow()
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit
