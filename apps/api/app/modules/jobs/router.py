from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import JobState, Role
from app.modules.auth.models import User
from app.modules.jobs.models import AnalysisJob
from app.modules.jobs.schemas import JobRead
from app.worker import damage_analysis, foundation_validation

router = APIRouter(prefix="/jobs", tags=["jobs"])


def scoped_job(db: Session, job_id: str, organization_id: str) -> AnalysisJob:
    job = db.scalar(select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.organization_id == organization_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisJob:
    return scoped_job(db, job_id, user.organization_id)


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> AnalysisJob:
    job = scoped_job(db, job_id, user.organization_id)
    if job.state != JobState.FAILED.value:
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    job.state = JobState.QUEUED.value
    job.progress = 0
    job.error_category = None
    job.error_message = None
    record_audit(db, user, "JOB_RETRIED", "analysis_job", job.id)
    db.commit()
    if job.type == "DAMAGE_ANALYSIS":
        damage_analysis.delay(job.id)
    else:
        foundation_validation.delay(job.id)
    db.refresh(job)
    return job
