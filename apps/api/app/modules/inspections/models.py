from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common import IdMixin, TimestampMixin
from app.database import Base
from app.enums import InspectionStatus, InspectionType


class Inspection(IdMixin, TimestampMixin, Base):
    __tablename__ = "inspections"

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), index=True)
    claim_id: Mapped[str | None] = mapped_column(ForeignKey("claims.id"), nullable=True, index=True)
    policy_id: Mapped[str | None] = mapped_column(ForeignKey("policies.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(30), default=InspectionType.CLAIM.value)
    status: Mapped[str] = mapped_column(String(30), default=InspectionStatus.DRAFT.value)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

