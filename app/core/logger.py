import logging
import sys
from logging.handlers import RotatingFileHandler
from app.core.config import settings


CONSOLE_FORMAT = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
FILE_FORMAT = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S"
)


def configure_logging() -> None:
    """
    Set up the Main Global Logger (Console + Rotating File).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CONSOLE_FORMAT)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(FILE_FORMAT)
    root_logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)
