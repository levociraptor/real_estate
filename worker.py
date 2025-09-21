import asyncio
import json
import logging
from pathlib import Path

import aio_pika
from PIL import Image as PILImage
from sqlalchemy import select

from app.database import session_gen
from app.exceptions import ImageNotFound
from app.logging.logging import setup_logging
from app.models import Image, ImageStatus
from app.settings import settings

setup_logging()
logger = logging.getLogger("image_worker")


async def generate_thumbnails(image_id: str) -> None:
    original_path = Path(settings.PATH_TO_IMAGE) / image_id
    if not original_path.exists():
        logger.error(f"Original image not found: {original_path}")
        raise ImageNotFound(f"Original image not found: {original_path}")

    for resolution in settings.THUMBNAILS_RESOLUTION:
        thumb_path = (
            Path(settings.PATH_TO_IMAGE)
            / f"{image_id}_{resolution}.jpg"
        )
        await asyncio.to_thread(
            resize_image,
            original_path,
            thumb_path,
            resolution,
        )


def resize_image(
        original_path: Path,
        thumb_path: Path,
        resolution: int,
) -> None:

    with PILImage.open(original_path) as img:
        img = img.convert("RGB")
        img.thumbnail((resolution, resolution), PILImage.LANCZOS)
        img.save(thumb_path, "JPEG", quality=85)
        logger.info(f"Thumbnail saved: {thumb_path}")


async def process_message(
        message: aio_pika.abc.AbstractIncomingMessage,
) -> None:
    async with message.process():
        body = json.loads(message.body.decode())
        image_id = body["image_id"]

        logger.info(f"Processing image {image_id}")

        async with session_gen() as session:
            stmt = select(Image).where(Image.id == image_id)
            result = await session.execute(stmt)
            img = result.scalar_one_or_none()
            if not img:
                logger.error(f"Image {image_id} not found")
                return

            img.status = ImageStatus.PROCESSING
            await session.commit()

        try:
            await generate_thumbnails(image_id)

            async with session_gen() as session:
                stmt = select(Image).where(Image.id == image_id)
                result = await session.execute(stmt)
                img = result.scalar_one()
                img.status = ImageStatus.DONE
                await session.commit()

            logger.info(f"Done image {image_id}")

        except Exception as e:
            async with session_gen() as session:
                stmt = select(Image).where(Image.id == image_id)
                result = await session.execute(stmt)
                img = result.scalar_one()
                img.status = ImageStatus.ERROR
                await session.commit()
            logger.error(f"[!] Error processing {image_id}:", exc_info=e)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.RABBIT_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("images", durable=True)

    logger.info("Worker started. Waiting for messages.")
    await queue.consume(process_message)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
