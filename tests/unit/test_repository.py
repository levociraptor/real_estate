import uuid
import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.repositories.image_repository import ImageRepository
from app.schemas.image_schemas import ImageSchema
from app.models import ImageStatus, Image


@pytest.mark.asyncio
async def test_add_image_creates_image_and_returns_schema(mock_session):
    repo = ImageRepository(mock_session)

    async def fake_refresh(obj):
        obj.id = uuid.uuid4()
        obj.status = ImageStatus.NEW
        obj.created_at = datetime.datetime.now()
        return None

    mock_session.refresh = AsyncMock(side_effect=fake_refresh)

    result = await repo.add_image("image/png", "test.png")

    assert isinstance(result, ImageSchema)
    assert result.content_type == "image/png"
    assert result.original_filename == "test.png"
    assert result.status == ImageStatus.NEW

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_image_by_id_returns_schema(mock_session):
    repo = ImageRepository(mock_session)

    test_id = uuid.uuid4()
    fake_image = Image(
        id=test_id,
        original_filename="test.png",
        content_type="image/png",
        status=ImageStatus.NEW,
        created_at=datetime.datetime.now(),
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_image
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await repo.get_image_by_id(str(test_id))

    assert isinstance(result, ImageSchema)
    assert result.id == test_id
    assert result.original_filename == "test.png"
    assert result.status == ImageStatus.NEW
    mock_session.execute.assert_awaited_once()
