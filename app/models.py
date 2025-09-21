from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Enum, String
from sqlalchemy.dialects.postgresql import UUID as AlchemyUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class ImageStatus(PyEnum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


class Base(DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = "images"

    id: Mapped[UUID] = mapped_column(
                AlchemyUUID(as_uuid=True),
                primary_key=True,
                default=uuid4,
    )
    status: Mapped[ImageStatus] = mapped_column(
        Enum(ImageStatus, name="image_status"),
        default=ImageStatus.NEW,
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.current_timestamp(),
    )
