"""
Налаштування логування CertifyPro.

Виділено з config.py для зменшення coupling.
"""

import logging
import os
from pathlib import Path


def setup_logging(logs_dir: Path, log_level: str = "INFO") -> None:
    """
    Налаштувати логування один раз (щоб не дублювати хендлери).

    Args:
        logs_dir: Папка для лог-файлів
        log_level: Рівень логування (DEBUG, INFO, WARNING, ERROR)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if logging.getLogger().handlers:
        return

    from logging.handlers import RotatingFileHandler

    log_file = logs_dir / "certifypro.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler],
    )
