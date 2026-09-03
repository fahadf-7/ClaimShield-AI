from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common import IdMixin, TimestampMixin
from app.database import Base
from app.enums import PolicyStatus


class Policy(IdMixin, TimestampMixin, Base):
    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("organization_id", "policy_number", name="uq_policy_org_number"),)

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), index=True)
    policy_number: Mapped[str] = mapped_column(String(80), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default=PolicyStatus.DRAFT.value)
