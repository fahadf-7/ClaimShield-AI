from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.organizations.models import AuditEvent


def record_audit(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            organization_id=user.organization_id,
            actor_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details or {},
        )
    )
