from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import PolicyStatus, Role
from app.modules.auth.models import User
from app.modules.policies.models import Policy
from app.modules.policies.schemas import PolicyCreate, PolicyRead, PolicyUpdate
from app.modules.vehicles.router import scoped_vehicle

router = APIRouter(prefix="/policies", tags=["policies"])


def scoped_policy(db: Session, policy_id: str, organization_id: str) -> Policy:
    policy = db.scalar(
        select(Policy).where(Policy.id == policy_id, Policy.organization_id == organization_id)
    )
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.get("", response_model=list[PolicyRead])
def list_policies(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Policy]:
    return list(
        db.scalars(
            select(Policy)
            .where(Policy.organization_id == user.organization_id)
            .order_by(Policy.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> Policy:
    scoped_vehicle(db, payload.vehicle_id, user.organization_id)
    if payload.status not in {item.value for item in PolicyStatus}:
        raise HTTPException(status_code=422, detail="Invalid policy status")
    policy = Policy(id=new_id(), organization_id=user.organization_id, **payload.model_dump())
    db.add(policy)
    record_audit(db, user, "POLICY_CREATED", "policy", policy.id)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Policy number already exists") from exc
    db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Policy:
    return scoped_policy(db, policy_id, user.organization_id)


@router.patch("/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: str,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> Policy:
    policy = scoped_policy(db, policy_id, user.organization_id)
    updates = payload.model_dump(exclude_unset=True)
    start = updates.get("start_date", policy.start_date)
    end = updates.get("end_date", policy.end_date)
    if end < start:
        raise HTTPException(status_code=422, detail="Policy end date must follow start date")
    if "status" in updates and updates["status"] not in {item.value for item in PolicyStatus}:
        raise HTTPException(status_code=422, detail="Invalid policy status")
    for key, value in updates.items():
        setattr(policy, key, value)
    record_audit(db, user, "POLICY_UPDATED", "policy", policy.id)
    db.commit()
    db.refresh(policy)
    return policy
