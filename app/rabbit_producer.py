import json
import logging

import aio_pika

from app.settings import settings

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    def __init__(self, url: str, queue_name: str = "images"):
        self.url = url
        self.queue_name = queue_name
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self):
        if self.connection:
            return
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(self.queue_name, durable=True)

    async def send_message(self, message: dict):
        if not self.channel:
            logger.error("Producer not connected")
            raise RuntimeError("Producer not connected")

        body = json.dumps(message).encode()
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=body),
            routing_key=self.queue_name,
        )
        logger.info(f" [x] Sent {message}")

    async def close(self):
        if self.connection:
            await self.connection.close()


rabbit_producer = None


def get_rabbit_producer() -> RabbitMQProducer:
    global rabbit_producer
    if rabbit_producer is None:
        rabbit_producer = RabbitMQProducer(
            settings.RABBIT_URL,
            settings.QUEUE_NAME,
        )
    return rabbit_producer
