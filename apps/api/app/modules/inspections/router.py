from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id, utcnow
from app.database import get_db
from app.dependencies import get_current_user
from app.enums import (
    ClaimStatus,
    InspectionStatus,
    InspectionType,
    JobState,
    MediaStatus,
)
from app.modules.auth.models import User
from app.modules.claims.router import scoped_claim
from app.modules.inspections.models import Inspection
from app.modules.inspections.schemas import InspectionCreate, InspectionDetail, InspectionRead
from app.modules.jobs.models import AnalysisJob
from app.modules.media.models import Media
from app.modules.policies.router import scoped_policy
from app.modules.vehicles.router import scoped_vehicle
from app.worker import foundation_validation

router = APIRouter(prefix="/inspections", tags=["inspections"])


def scoped_inspection(db: Session, inspection_id: str, organization_id: str) -> Inspection:
    inspection = db.scalar(
        select(Inspection).where(
            Inspection.id == inspection_id, Inspection.organization_id == organization_id
        )
    )
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.get("", response_model=list[InspectionRead])
def list_inspections(
    claim_id: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Inspection]:
    query = select(Inspection).where(Inspection.organization_id == user.organization_id)
    if claim_id:
        query = query.where(Inspection.claim_id == claim_id)
    if vehicle_id:
        query = query.where(Inspection.vehicle_id == vehicle_id)
    return list(db.scalars(query.order_by(Inspection.created_at.desc())))


@router.post("", response_model=InspectionRead, status_code=status.HTTP_201_CREATED)
def create_inspection(
    payload: InspectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Inspection:
    if payload.type not in {item.value for item in InspectionType}:
        raise HTTPException(status_code=422, detail="Invalid inspection type")
    scoped_vehicle(db, payload.vehicle_id, user.organization_id)
    if payload.policy_id:
        policy = scoped_policy(db, payload.policy_id, user.organization_id)
        if policy.vehicle_id != payload.vehicle_id:
            raise HTTPException(status_code=422, detail="Policy does not belong to this vehicle")
    if payload.claim_id:
        claim = scoped_claim(db, payload.claim_id, user.organization_id)
        policy = scoped_policy(db, claim.policy_id, user.organization_id)
        if policy.vehicle_id != payload.vehicle_id:
            raise HTTPException(status_code=422, detail="Claim does not belong to this vehicle")
        if payload.type != InspectionType.CLAIM.value:
            raise HTTPException(status_code=422, detail="A claim must use a claim inspection")
    if payload.type == InspectionType.CLAIM.value and not payload.claim_id:
        raise HTTPException(status_code=422, detail="Claim inspection requires a claim")
    inspection = Inspection(id=new_id(), organization_id=user.organization_id, **payload.model_dump())
    db.add(inspection)
    record_audit(db, user, "INSPECTION_CREATED", "inspection", inspection.id)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("/{inspection_id}", response_model=InspectionDetail)
def get_inspection(
    inspection_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InspectionDetail:
    inspection = scoped_inspection(db, inspection_id, user.organization_id)
    media = db.scalars(
        select(Media).where(Media.inspection_id == inspection.id, Media.organization_id == user.organization_id)
    ).all()
    jobs = db.scalars(
        select(AnalysisJob)
        .where(AnalysisJob.inspection_id == inspection.id, AnalysisJob.organization_id == user.organization_id)
        .order_by(AnalysisJob.created_at.desc())
    ).all()
    return InspectionDetail(
        **InspectionRead.model_validate(inspection).model_dump(),
        media=[
            {
                "id": item.id,
                "filename": item.original_filename,
                "viewpoint": item.viewpoint,
                "status": item.status,
                "width": item.width,
                "height": item.height,
            }
            for item in media
        ],
        jobs=[
            {
                "id": job.id,
                "type": job.type,
                "state": job.state,
                "progress": job.progress,
                "error_message": job.error_message,
                "result": job.result_json,
            }
            for job in jobs
        ],
    )


@router.post("/{inspection_id}/submit", response_model=InspectionDetail)
def submit_inspection(
    inspection_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InspectionDetail:
    inspection = scoped_inspection(db, inspection_id, user.organization_id)
    existing_job = db.scalar(
        select(AnalysisJob).where(
            AnalysisJob.inspection_id == inspection.id,
            AnalysisJob.organization_id == user.organization_id,
            AnalysisJob.idempotency_key == (idempotency_key or f"submit:{inspection.id}:v1"),
        )
    )
    if inspection.status != InspectionStatus.DRAFT.value:
        if existing_job:
            return get_inspection(inspection_id, db, user)
        raise HTTPException(status_code=409, detail="Inspection has already been submitted")
    media = db.scalars(
        select(Media).where(Media.inspection_id == inspection.id, Media.organization_id == user.organization_id)
    ).all()
    if not media:
        raise HTTPException(status_code=422, detail="Add at least one valid image before submission")
    inspection.status = InspectionStatus.PROCESSING.value
    inspection.submitted_at = utcnow()
    for item in media:
        item.status = MediaStatus.LOCKED.value
    job = AnalysisJob(
        id=new_id(),
        organization_id=user.organization_id,
        inspection_id=inspection.id,
        claim_id=inspection.claim_id,
        type="FOUNDATION_VALIDATION",
        state=JobState.QUEUED.value,
        correlation_id=str(uuid4()),
        idempotency_key=idempotency_key or f"submit:{inspection.id}:v1",
    )
    db.add(job)
    if inspection.claim_id:
        claim = scoped_claim(db, inspection.claim_id, user.organization_id)
        claim.status = ClaimStatus.PROCESSING.value
    record_audit(db, user, "INSPECTION_SUBMITTED", "inspection", inspection.id)
    db.commit()
    foundation_validation.delay(job.id)
    db.expire_all()
    return get_inspection(inspection_id, db, user)
