from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.common import new_id
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import ReviewDecision, Role
from app.modules.auth.models import User
from app.modules.claims.router import scoped_claim
from app.modules.reviews.models import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewRead

router = APIRouter(prefix="/claims/{claim_id}/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewRead])
def list_reviews(
    claim_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Review]:
    scoped_claim(db, claim_id, user.organization_id)
    return list(
        db.scalars(
            select(Review)
            .where(Review.claim_id == claim_id, Review.organization_id == user.organization_id)
            .order_by(Review.version.desc())
        )
    )


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(
    claim_id: str,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN.value, Role.REVIEWER.value)),
) -> Review:
    scoped_claim(db, claim_id, user.organization_id)
    if payload.decision not in {item.value for item in ReviewDecision}:
        raise HTTPException(status_code=422, detail="Invalid review decision")
    latest = (
        db.scalar(
            select(func.max(Review.version)).where(
                Review.claim_id == claim_id, Review.organization_id == user.organization_id
            )
        )
        or 0
    )
    review = Review(
        id=new_id(),
        organization_id=user.organization_id,
        claim_id=claim_id,
        reviewer_id=user.id,
        decision=payload.decision,
        notes=payload.notes,
        version=latest + 1,
    )
    db.add(review)
    record_audit(db, user, "REVIEW_CREATED", "review", review.id, {"claim_id": claim_id})
    db.commit()
    db.refresh(review)
    return review
