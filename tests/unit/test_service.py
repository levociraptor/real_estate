import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from fastapi import UploadFile
from starlette.responses import FileResponse
from starlette.datastructures import Headers
import io
import uuid
import datetime

from app.services.image_service import ImageService
from app.models import ImageStatus
from app.schemas.image_schemas import ImageSchema
from app.exceptions import (
    NotAllowedContentType,
    FileTooBig,
    ImageSaveWithError,
    ImageNotProcessedYetError,
)


@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repository):
    with patch("app.services.image_service.ImageRepository", return_value=mock_repository):
        return ImageService(session=AsyncMock())


@pytest.mark.asyncio
async def test_upload_image_success(service, mock_repository, tmp_path):
    fake_id = uuid.uuid4()
    fake_schema = ImageSchema(
        id=fake_id,
        status=ImageStatus.NEW,
        original_filename="test.png",
        content_type="image/png",
        created_at=datetime.datetime.now(),
    )
    mock_repository.add_image.return_value = fake_schema
    headers = Headers({"content-type": "image/png"})

    file_content = b"fake_image_data" * 10
    upload = UploadFile(filename="test.png", headers=headers, file=io.BytesIO(file_content))
    upload.size = len(file_content)

    mock_file = AsyncMock()
    mock_open_cm = AsyncMock(return_value=mock_file)
    mock_open_cm.__aenter__.return_value = mock_file
    mock_open_cm.__aexit__.return_value = None

    def mock_async_open(*args, **kwargs):
        return mock_open_cm

    with patch("app.services.image_service.Path", return_value=tmp_path), \
         patch("app.services.image_service.async_open", mock_async_open):

        result = await service.upload_image(upload)

    assert isinstance(result, ImageSchema)
    assert result.id == fake_id
    mock_repository.add_image.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_image_not_allowed_content_type(service):
    headers = Headers({"content-type": "text/plain"})
    upload = UploadFile(filename="bad.txt", headers=headers, file=io.BytesIO(b"123"))
    upload.size = 3

    with pytest.raises(NotAllowedContentType):
        await service.upload_image(upload)


@pytest.mark.asyncio
async def test_upload_image_too_big(service):
    headers = Headers({"content-type": "image/png"})
    upload = UploadFile(filename="big.png", headers=headers, file=io.BytesIO(b"1"))
    upload.size = service.max_file_size + 1

    with pytest.raises(FileTooBig):
        await service.upload_image(upload)


@pytest.mark.asyncio
async def test_get_image_info_returns_schema(service, mock_repository):
    fake_id = uuid.uuid4()
    fake_schema = ImageSchema(
        id=fake_id,
        status=ImageStatus.NEW,
        original_filename="test.png",
        content_type="image/png",
        created_at=datetime.datetime.now(),
    )
    mock_repository.get_image_by_id.return_value = fake_schema

    result = await service.get_image_info(str(fake_id))

    assert result == fake_schema
    mock_repository.get_image_by_id.assert_awaited_once_with(str(fake_id))


@pytest.mark.asyncio
async def test_get_image_returns_file(service, mock_repository, tmp_path):
    fake_id = uuid.uuid4()
    fake_schema = ImageSchema(
        id=fake_id,
        status=ImageStatus.DONE,
        original_filename="test.png",
        content_type="image/png",
        created_at=datetime.datetime.now(),
    )
    mock_repository.get_image_by_id.return_value = fake_schema

    fake_file = tmp_path / f"{fake_id}_100.jpg"
    fake_file.write_bytes(b"data")

    with patch("app.services.image_service.Path", return_value=tmp_path):
        response = await service.get_image(str(fake_id), 100)

    assert isinstance(response, FileResponse)
    assert str(fake_id) in str(response.path)


@pytest.mark.asyncio
async def test_get_image_raises_if_error(service, mock_repository):
    fake_schema = ImageSchema(
        id=uuid.uuid4(),
        status=ImageStatus.ERROR,
        original_filename="x.png",
        content_type="image/png",
        created_at=datetime.datetime.now(),
    )
    mock_repository.get_image_by_id.return_value = fake_schema

    with pytest.raises(ImageSaveWithError):
        await service.get_image(str(fake_schema.id), 100)


@pytest.mark.asyncio
async def test_get_image_raises_if_processing(service, mock_repository):
    fake_schema = ImageSchema(
        id=uuid.uuid4(),
        status=ImageStatus.PROCESSING,
        original_filename="x.png",
        content_type="image/png",
        created_at=datetime.datetime.now(),
    )
    mock_repository.get_image_by_id.return_value = fake_schema

    with pytest.raises(ImageNotProcessedYetError):
        await service.get_image(str(fake_schema.id), 100)
