from pathlib import Path

from aiofile import async_open
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (FileTooBig, ImageNotProcessedYetError,
                            ImageSaveWithError, NotAllowedContentType)
from app.models import ImageStatus
from app.repositories.image_repository import ImageRepository
from app.schemas.image_schemas import ImageSchema
from app.settings import settings


class ImageService:
    def __init__(self, session: AsyncSession) -> None:
        self.allowed_content_types = settings.ALLOWED_CONTENT_TYPES
        self.max_file_size = settings.MAX_IMG_SIZE
        self.image_repository = ImageRepository(session)

    async def upload_image(self, image: UploadFile) -> ImageSchema:
        content_type = image.content_type
        if content_type not in self.allowed_content_types:
            raise NotAllowedContentType
        if image.size is None:
            raise ValueError("File size is unknown")
        if image.size > self.max_file_size:
            raise FileTooBig
        image.file.seek(0)

        original_filename = image.filename
        image_schema = await self.image_repository.add_image(
            content_type,
            original_filename,
        )
        path_to_file = Path(settings.PATH_TO_IMAGE) / str(image_schema.id)
        async with async_open(path_to_file, "wb") as file:
            while chunk := image.file.read(1024 * 1024):
                await file.write(chunk)

        return image_schema

    async def get_image_info(self, id: str) -> ImageSchema:
        image = await self.image_repository.get_image_by_id(id)
        return image

    async def get_image(self, id: str, resolution: int) -> FileResponse:
        image_schema = await self.image_repository.get_image_by_id(id)
        if image_schema.status == ImageStatus.ERROR:
            raise ImageSaveWithError
        if image_schema.status == ImageStatus.PROCESSING:
            raise ImageNotProcessedYetError
        file_name = str(image_schema.id) + "_" + str(resolution) + ".jpg"
        path_to_file = Path(settings.PATH_TO_IMAGE) / file_name
        return FileResponse(path_to_file)
