import logging
import os
from pathlib import Path
from typing import Optional

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "autoagent.log"
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_loggers = {}


def setup_logger(name: Optional[str] = None, level: int = LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name or "autoagent")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    os.makedirs(LOG_DIR, exist_ok=True)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    if name not in _loggers:
        _loggers[name] = setup_logger(name)
    return _loggers[name]
