from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    inspection_id: str
    claim_id: str | None
    type: str
    state: str
    progress: int
    attempt_count: int
    correlation_id: str
    error_category: str | None
    error_message: str | None
    result_json: dict[str, Any]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
