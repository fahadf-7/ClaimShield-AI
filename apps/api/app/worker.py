from celery import Celery

from app.config import settings

celery_app = Celery("claimshield", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(name="claimshield.foundation_validation", bind=True, max_retries=2)
def foundation_validation(self, job_id: str) -> dict:
    from sqlalchemy import select

    from app.common import utcnow
    from app.database import SessionLocal
    from app.enums import InspectionStatus, JobState
    from app.modules.inspections.models import Inspection
    from app.modules.jobs.models import AnalysisJob
    from app.modules.media.models import Media

    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return {"status": "missing"}
        if job.state == JobState.SUCCEEDED.value:
            return job.result_json

        job.state = JobState.RUNNING.value
        job.started_at = utcnow()
        job.progress = 25
        job.attempt_count += 1
        db.commit()

        media = db.scalars(
            select(Media).where(
                Media.inspection_id == job.inspection_id,
                Media.organization_id == job.organization_id,
            )
        ).all()
        result = {
            "media_count": len(media),
            "message": "Phase 0 media validation completed. No AI analysis was performed.",
        }
        job.state = JobState.SUCCEEDED.value
        job.progress = 100
        job.completed_at = utcnow()
        job.result_json = result
        inspection = db.get(Inspection, job.inspection_id)
        if inspection is not None:
            inspection.status = InspectionStatus.READY.value
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.state = JobState.FAILED.value
            job.error_category = "FOUNDATION_VALIDATION_ERROR"
            job.error_message = "Media validation could not be completed."
            job.completed_at = utcnow()
            db.commit()
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 8)) from exc
    finally:
        db.close()
