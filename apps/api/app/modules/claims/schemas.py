from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClaimBase(BaseModel):
    policy_id: str
    claim_number: str = Field(min_length=2, max_length=80)
    incident_date: datetime
    incident_location: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=10, max_length=4000)
    status: str = "DRAFT"


class ClaimCreate(ClaimBase):
    pass


class ClaimUpdate(BaseModel):
    incident_location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, min_length=10, max_length=4000)
    status: str | None = None


class ClaimRead(ClaimBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    open_claims: int
    evidence_pending: int
    processing: int
    review_pending: int
    completed: int
    vehicles: int

