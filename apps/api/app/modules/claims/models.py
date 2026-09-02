from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common import IdMixin, TimestampMixin
from app.database import Base
from app.enums import ClaimStatus


class Claim(IdMixin, TimestampMixin, Base):
    __tablename__ = "claims"

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id"), index=True)
    claim_number: Mapped[str] = mapped_column(String(80), index=True)
    incident_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    incident_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=ClaimStatus.DRAFT.value)

