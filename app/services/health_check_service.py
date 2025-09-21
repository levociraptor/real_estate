from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DBHealtCheckException, RabbitHealthCheckException
from app.rabbit_producer import get_rabbit_producer


class HealthCheckService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check_db(self):
        try:
            async with self.session.begin():
                await self.session.execute(text("SELECT 1"))
        except Exception as e:
            raise DBHealtCheckException(str(e))

    async def check_rabbit(self):
        producer = get_rabbit_producer()
        try:
            producer.channel.declare_queue(producer.queue_name, passive=False)
        except Exception as e:
            raise RabbitHealthCheckException(str(e))
