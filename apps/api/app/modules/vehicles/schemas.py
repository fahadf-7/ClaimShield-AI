from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VehicleBase(BaseModel):
    registration_number: str = Field(min_length=2, max_length=40)
    vin: str | None = Field(default=None, max_length=17)
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=50)

    @field_validator("registration_number")
    @classmethod
    def normalize_registration(cls, value: str) -> str:
        return "".join(value.upper().split())

    @field_validator("vin")
    @classmethod
    def normalize_vin(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = value.upper().replace(" ", "")
        if len(normalized) != 17 or any(char in normalized for char in "IOQ"):
            raise ValueError("VIN must contain 17 valid characters and exclude I, O, and Q")
        return normalized


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    vin: str | None = None
    make: str | None = Field(default=None, min_length=1, max_length=80)
    model: str | None = Field(default=None, min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=50)


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class VehicleHistory(BaseModel):
    vehicle: VehicleRead
    policies: list[dict]
    claims: list[dict]
    inspections: list[dict]

