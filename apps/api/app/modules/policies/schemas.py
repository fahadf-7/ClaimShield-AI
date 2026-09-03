from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyBase(BaseModel):
    vehicle_id: str
    policy_number: str = Field(min_length=2, max_length=80)
    start_date: date
    end_date: date
    status: str = "DRAFT"

    @model_validator(mode="after")
    def dates_are_valid(self):
        if self.end_date < self.start_date:
            raise ValueError("Policy end date must be on or after the start date")
        return self


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class PolicyRead(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_at: datetime
