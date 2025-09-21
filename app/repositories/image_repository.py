from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ImageNotFound
from app.models import Image
from app.schemas.image_schemas import ImageSchema


class ImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_image(self, content_type: str, original_filename: str) -> ImageSchema:
        img = Image(
            original_filename=original_filename,
            content_type=content_type,
        )
        self.session.add(img)
        await self.session.commit()
        await self.session.refresh(img)
        image_schema = ImageSchema.model_validate(img)
        return image_schema

    async def get_image_by_id(self, id: str) -> ImageSchema:
        stmt = select(Image).where(Image.id == id)
        result = await self.session.execute(stmt)
        img = result.scalar_one_or_none()
        if not img:
            raise ImageNotFound
        image_schema = ImageSchema.model_validate(img)
        return image_schema
