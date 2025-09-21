import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db_session
from app.exceptions import DBHealtCheckException, RabbitHealthCheckException
from app.services.health_check_service import HealthCheckService

logger = logging.getLogger(__name__)
health_check_router = APIRouter(prefix="/health", tags=["health_check"])


@health_check_router.get("/")
async def health_sheck(session: Annotated[AsyncSession, Depends(get_async_db_session)]):
    health_check_service = HealthCheckService(session=session)
    errors = []
    try:
        await health_check_service.check_db()
    except DBHealtCheckException as e:
        logger.error("Db Error:", exc_info=True)
        errors.append(f"Db Error: {e}")
    try:
        await health_check_service.check_rabbit()
    except RabbitHealthCheckException as e:
        logger.error("RabbitMQ error:", exc_info=True)
        errors.append(f"RabbitMQ error: {e}")
    if errors:
        raise HTTPException(
            status_code=500,
            detail={"status": "unhealthy", "errors": errors}
        )
    return {"status": "healthy"}
