from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import Role
from app.modules.auth.models import User
from app.modules.claims.models import Claim
from app.modules.inspections.models import Inspection
from app.modules.policies.models import Policy
from app.modules.vehicles.models import Vehicle
from app.modules.vehicles.schemas import VehicleCreate, VehicleHistory, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def scoped_vehicle(db: Session, vehicle_id: str, organization_id: str) -> Vehicle:
    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.organization_id == organization_id))
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.get("", response_model=list[VehicleRead])
def list_vehicles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Vehicle]:
    return list(
        db.scalars(
            select(Vehicle)
            .where(Vehicle.organization_id == user.organization_id)
            .order_by(Vehicle.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> Vehicle:
    vehicle = Vehicle(id=new_id(), organization_id=user.organization_id, **payload.model_dump())
    db.add(vehicle)
    record_audit(db, user, "VEHICLE_CREATED", "vehicle", vehicle.id)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Registration number already exists") from exc
    db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Vehicle:
    return scoped_vehicle(db, vehicle_id, user.organization_id)


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> Vehicle:
    vehicle = scoped_vehicle(db, vehicle_id, user.organization_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)
    record_audit(db, user, "VEHICLE_UPDATED", "vehicle", vehicle.id)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}/history", response_model=VehicleHistory)
def vehicle_history(
    vehicle_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VehicleHistory:
    vehicle = scoped_vehicle(db, vehicle_id, user.organization_id)
    policies = db.scalars(
        select(Policy).where(Policy.vehicle_id == vehicle.id, Policy.organization_id == user.organization_id)
    ).all()
    policy_ids = [policy.id for policy in policies]
    claims = (
        db.scalars(
            select(Claim).where(
                Claim.organization_id == user.organization_id,
                Claim.policy_id.in_(policy_ids),
            )
        ).all()
        if policy_ids
        else []
    )
    inspections = db.scalars(
        select(Inspection)
        .where(Inspection.vehicle_id == vehicle.id, Inspection.organization_id == user.organization_id)
        .order_by(Inspection.created_at.desc())
    ).all()
    return VehicleHistory(
        vehicle=VehicleRead.model_validate(vehicle),
        policies=[{"id": p.id, "policy_number": p.policy_number, "status": p.status} for p in policies],
        claims=[{"id": c.id, "claim_number": c.claim_number, "status": c.status} for c in claims],
        inspections=[
            {"id": item.id, "type": item.type, "status": item.status, "created_at": item.created_at}
            for item in inspections
        ],
    )
