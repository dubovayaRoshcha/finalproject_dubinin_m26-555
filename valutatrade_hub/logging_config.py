import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging():
    """Настройка логирования операций"""

    settings = SettingsLoader()
    log_path = Path(settings.get("log_path"))

    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("valutatrade")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger


def setup_parser_logging():
    log_path = Path("logs/parser.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("valutatrade.parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger
