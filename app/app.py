import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import initialize_db, shutdown
from app.logging.logging import setup_logging
from app.rabbit_producer import get_rabbit_producer
from app.routers.health_check_router import health_check_router
from app.routers.image_router import image_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App starting...")
    producer = get_rabbit_producer()
    await producer.connect()
    await initialize_db()

    yield
    await shutdown()
    await producer.close()
    logger.info("App shutting down...")


app = FastAPI(
    title="Image API",
    summary="API for working with images",
    lifespan=lifespan,
)

app.include_router(image_router)
app.include_router(health_check_router)
