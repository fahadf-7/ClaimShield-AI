from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InspectionCreate(BaseModel):
    vehicle_id: str
    policy_id: str | None = None
    claim_id: str | None = None
    type: str


class InspectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    vehicle_id: str
    policy_id: str | None
    claim_id: str | None
    type: str
    status: str
    submitted_at: datetime | None
    created_at: datetime


class InspectionDetail(InspectionRead):
    media: list[dict]
    jobs: list[dict]
