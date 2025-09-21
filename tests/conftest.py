from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """
    Мок сессии SQLAlchemy.
    """
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_producer():
    """
    Мок RabbitMQProducer.
    """
    producer = MagicMock()
    producer.connect = AsyncMock()
    producer.close = AsyncMock()
    producer.send_message = AsyncMock()
    producer.channel = AsyncMock()
    return producer
