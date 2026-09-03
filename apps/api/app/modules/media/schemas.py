from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    inspection_id: str
    original_filename: str
    media_type: str
    size_bytes: int
    width: int
    height: int
    viewpoint: str
    sha256: str
    status: str
    created_at: datetime
