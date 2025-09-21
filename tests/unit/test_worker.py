import pytest
import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch
from PIL import Image as PILImage
from contextlib import asynccontextmanager

from worker import resize_image, generate_thumbnails, process_message
from app.models import Image, ImageStatus


def test_resize_image_creates_thumbnail(tmp_path: Path):
    original = tmp_path / "original.jpg"
    with PILImage.new("RGB", (200, 200), color="red") as img:
        img.save(original, "JPEG")

    thumb = tmp_path / "thumb.jpg"
    resize_image(original, thumb, 100)

    assert thumb.exists()

    with PILImage.open(thumb) as img:
        assert img.width <= 100
        assert img.height <= 100


@pytest.mark.asyncio
async def test_generate_thumbnails_calls_resize_image(tmp_path):
    image_id = "test.jpg"
    original = tmp_path / image_id
    original.write_bytes(b"fake data")

    with patch("worker.resize_image") as mock_resize, \
         patch("worker.settings") as mock_settings:
        mock_settings.PATH_TO_IMAGE = tmp_path
        mock_settings.THUMBNAILS_RESOLUTION = [50, 100]

        await generate_thumbnails(image_id)

    assert mock_resize.call_count == 2


class DummyMessage:
    def __init__(self, body: dict):
        self.body = json.dumps(body).encode()

    def process(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_process_message_success(tmp_path):
    fake_id = str(uuid.uuid4())
    fake_img = Image(id=fake_id, status=ImageStatus.NEW)

    mock_session = AsyncMock()
    mock_session.get.return_value = fake_img
    mock_session.commit = AsyncMock()

    @asynccontextmanager
    async def fake_session_gen():
        yield mock_session

    with patch("worker.session_gen", fake_session_gen), \
         patch("worker.generate_thumbnails", AsyncMock()) as mock_thumbs:

        msg = DummyMessage({"image_id": fake_id})
        await process_message(msg)

    assert fake_img.status in (ImageStatus.PROCESSING, ImageStatus.DONE)
    mock_thumbs.assert_awaited_once_with(fake_id)


@pytest.mark.asyncio
async def test_process_message_image_not_found():
    fake_id = str(uuid.uuid4())
    mock_session = AsyncMock()
    mock_session.get.return_value = None
    mock_session.commit = AsyncMock()

    @asynccontextmanager
    async def fake_session_gen():
        yield mock_session

    with patch("worker.session_gen", fake_session_gen):
        msg = DummyMessage({"image_id": fake_id})
        await process_message(msg)

    mock_session.get.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
