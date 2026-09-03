from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    decision: str
    notes: str = Field(default="", max_length=4000)


class ReviewRead(ReviewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    reviewer_id: str
    version: int
    created_at: datetime
