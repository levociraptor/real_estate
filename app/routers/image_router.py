import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db_session
from app.exceptions import (FileTooBig, ImageNotFound,
                            ImageNotProcessedYetError, ImageSaveWithError,
                            NotAllowedContentType)
from app.rabbit_producer import RabbitMQProducer, get_rabbit_producer
from app.services.image_service import ImageService
from app.settings import settings

logger = logging.getLogger(__name__)
image_router = APIRouter()


@image_router.post("/image")
async def upload_image(
    image: UploadFile,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    producer: Annotated[RabbitMQProducer, Depends(get_rabbit_producer)]
):
    try:
        image_service = ImageService(session)
        image_schema = await image_service.upload_image(image)
        await producer.send_message({
            "image_id": str(image_schema.id),
        })
    except NotAllowedContentType as e:
        logger.error("Not Allowed Content type.", exc_info=e)
        raise HTTPException(
            status_code=415,
            detail="Неподдерживаемый тип файла."
        )
    except FileTooBig as e:
        logger.error("Too big image to upload.", exc_info=e)
        raise HTTPException(
            status_code=413,
            detail="Файл слишком большой."
        )
    return image_schema


@image_router.get("/image_info/{id}")
async def get_images_info(
    id: str,
    session: Annotated[AsyncSession, Depends(get_async_db_session)]
):
    try:
        image_service = ImageService(session)
        image = await image_service.get_image_info(id)
    except ImageNotFound as e:
        logger.error("Image not found.", exc_info=e)
        raise HTTPException(
            status_code=404,
            detail="Image not found."
        )
    return image


@image_router.get("/image/{id}/{resolution}")
async def get_image(
    id: str,
    resolution: int,
    session: Annotated[AsyncSession, Depends(get_async_db_session)]
):
    try:
        if resolution not in settings.THUMBNAILS_RESOLUTION:
            raise HTTPException(
                status_code=400,
                detail="Bad request.",
            )
        image_service = ImageService(session)
        image = await image_service.get_image(id, resolution)
    except ImageNotFound as e:
        logger.error("Image not found.", exc_info=e)
        raise HTTPException(
            status_code=404,
            detail="Image not found.",
        )
    except ImageSaveWithError as e:
        logger.error("Image not saved correctly.", exc_info=e)
        raise HTTPException(
            status_code=424,
            detail="Thumbnail generation failed. Please try uploading the image again.",
        )
    except ImageNotProcessedYetError as e:
        logger.error("Image not ready yet.", exc_info=e)
        raise HTTPException(
            status_code=425,
            detail="Thumbnail generation not ready yet.",
        )
    return image
