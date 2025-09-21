import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(level: str = "INFO") -> None:
    """
    Настраивает логирование в JSON формате.
    Все логи пишутся в stdout (для корректной работы в Docker).
    """

    # создаём root-логгер
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    # если хендлеры уже есть — очищаем
    if logger.handlers:
        logger.handlers.clear()

    # пишем в stdout
    log_handler = logging.StreamHandler(sys.stdout)

    # формат JSON
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )

    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()
    logging.getLogger("uvicorn").handlers.clear()
