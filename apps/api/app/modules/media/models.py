from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common import IdMixin, TimestampMixin
from app.database import Base
from app.enums import MediaStatus


class Media(IdMixin, TimestampMixin, Base):
    __tablename__ = "media"
    __table_args__ = (
        UniqueConstraint("inspection_id", "sha256", name="uq_media_inspection_hash"),
    )

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), index=True)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    width: Mapped[int]
    height: Mapped[int]
    viewpoint: Mapped[str] = mapped_column(String(40), default="UNKNOWN")
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default=MediaStatus.UPLOADED.value)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

