from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import ImageStatus


class ImageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ImageStatus
    original_filename: str
    content_type: str
    created_at: datetime
