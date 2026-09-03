from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import ClaimStatus, Role
from app.modules.auth.models import User
from app.modules.claims.models import Claim
from app.modules.claims.schemas import ClaimCreate, ClaimRead, ClaimUpdate, DashboardSummary
from app.modules.policies.router import scoped_policy
from app.modules.vehicles.models import Vehicle

router = APIRouter(prefix="/claims", tags=["claims"])

ALLOWED_TRANSITIONS = {
    ClaimStatus.DRAFT.value: {ClaimStatus.EVIDENCE_PENDING.value, ClaimStatus.CANCELLED.value},
    ClaimStatus.EVIDENCE_PENDING.value: {ClaimStatus.PROCESSING.value, ClaimStatus.CANCELLED.value},
    ClaimStatus.PROCESSING.value: {ClaimStatus.REVIEW_PENDING.value, ClaimStatus.CANCELLED.value},
    ClaimStatus.REVIEW_PENDING.value: {ClaimStatus.COMPLETED.value, ClaimStatus.EVIDENCE_PENDING.value},
    ClaimStatus.COMPLETED.value: set(),
    ClaimStatus.CANCELLED.value: set(),
}


def scoped_claim(db: Session, claim_id: str, organization_id: str) -> Claim:
    claim = db.scalar(select(Claim).where(Claim.id == claim_id, Claim.organization_id == organization_id))
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> DashboardSummary:
    counts = dict(
        db.execute(
            select(Claim.status, func.count(Claim.id))
            .where(Claim.organization_id == user.organization_id)
            .group_by(Claim.status)
        ).all()
    )
    vehicles = db.scalar(select(func.count(Vehicle.id)).where(Vehicle.organization_id == user.organization_id)) or 0
    return DashboardSummary(
        open_claims=sum(
            counts.get(state.value, 0)
            for state in ClaimStatus
            if state not in {ClaimStatus.COMPLETED, ClaimStatus.CANCELLED}
        ),
        evidence_pending=counts.get(ClaimStatus.EVIDENCE_PENDING.value, 0),
        processing=counts.get(ClaimStatus.PROCESSING.value, 0),
        review_pending=counts.get(ClaimStatus.REVIEW_PENDING.value, 0),
        completed=counts.get(ClaimStatus.COMPLETED.value, 0),
        vehicles=vehicles,
    )


@router.get("", response_model=list[ClaimRead])
def list_claims(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    claim_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Claim]:
    query = select(Claim).where(Claim.organization_id == user.organization_id)
    if claim_status:
        query = query.where(Claim.status == claim_status)
    return list(db.scalars(query.order_by(Claim.created_at.desc()).limit(limit).offset(offset)))


@router.post("", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Claim:
    policy = scoped_policy(db, payload.policy_id, user.organization_id)
    if payload.incident_date.date() < policy.start_date or payload.incident_date.date() > policy.end_date:
        raise HTTPException(status_code=422, detail="Incident date is outside the policy period")
    if payload.status not in {ClaimStatus.DRAFT.value, ClaimStatus.EVIDENCE_PENDING.value}:
        raise HTTPException(status_code=422, detail="New claims must be draft or evidence pending")
    exists = db.scalar(
        select(Claim.id).where(
            Claim.organization_id == user.organization_id,
            Claim.claim_number == payload.claim_number,
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail="Claim number already exists")
    claim = Claim(id=new_id(), organization_id=user.organization_id, **payload.model_dump())
    db.add(claim)
    record_audit(db, user, "CLAIM_CREATED", "claim", claim.id)
    db.commit()
    db.refresh(claim)
    return claim


@router.get("/{claim_id}", response_model=ClaimRead)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Claim:
    return scoped_claim(db, claim_id, user.organization_id)


@router.patch("/{claim_id}", response_model=ClaimRead)
def update_claim(
    claim_id: str,
    payload: ClaimUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> Claim:
    claim = scoped_claim(db, claim_id, user.organization_id)
    updates = payload.model_dump(exclude_unset=True)
    next_status = updates.get("status")
    if next_status and next_status != claim.status and next_status not in ALLOWED_TRANSITIONS[claim.status]:
        raise HTTPException(status_code=409, detail=f"Claim cannot move from {claim.status} to {next_status}")
    for key, value in updates.items():
        setattr(claim, key, value)
    record_audit(db, user, "CLAIM_UPDATED", "claim", claim.id, {"fields": list(updates)})
    db.commit()
    db.refresh(claim)
    return claim
