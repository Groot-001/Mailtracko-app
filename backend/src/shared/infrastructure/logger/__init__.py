import logging
import sys

from pythonjsonlogger import jsonlogger

from src.core.config.settings import config


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("mail_tracko")
    logger.setLevel(config.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(  # pyright: ignore[reportPrivateImportUsage]
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


logger = setup_logger()
