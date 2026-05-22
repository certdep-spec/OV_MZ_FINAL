"""
debug_logger.py — Специальный логгер для отладки передачи данных клиента

Записывает логи в файл debug_client_data.log рядом с .exe
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def _get_log_file() -> Path:
    """Получить путь к файлу логов рядом с .exe"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "debug_client_data.log"
    return Path(__file__).parent / "debug_client_data.log"


# Настраиваем логгер
LOG_FILE = _get_log_file()

# Создаем отдельный logger для отладки данных клиента
debug_logger = logging.getLogger("certifypro.debug_client_data")
debug_logger.setLevel(logging.DEBUG)

# Удаляем старые обработчики если есть
debug_logger.handlers.clear()

# Файловый обработчик
file_handler = logging.FileHandler(str(LOG_FILE), mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)
debug_logger.addHandler(file_handler)

# Консольный обработчик (для разработки)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt="%H:%M:%S")
console_handler.setFormatter(console_formatter)
debug_logger.addHandler(console_handler)


def log_stage(stage: str, data: dict):
    """
    Записать данные на определенном этапе.

    Args:
        stage: Название этапа (например, "launcher_save", "provisioner", "config_init")
        data: Данные для логирования
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    debug_logger.info("=" * 80)
    debug_logger.info(f"📍 ЭТАП: {stage}")
    debug_logger.info(f"⏰ Время: {timestamp}")
    debug_logger.info("=" * 80)

    for key, value in data.items():
        if isinstance(value, (dict, list)):
            debug_logger.info(f"  {key}:")
            for k, v in value.items() if isinstance(value, dict) else enumerate(value):
                debug_logger.info(f"    {k}: {v}")
        else:
            display_value = str(value) if value is not None else "None"
            debug_logger.info(f"  {key}: {display_value}")

    debug_logger.info("")


def log_error(stage: str, error: str):
    """Записать ошибку"""
    debug_logger.error("=" * 80)
    debug_logger.error(f"❌ ОШИБКА на этапе: {stage}")
    debug_logger.error(f"   {error}")
    debug_logger.error("=" * 80)
    debug_logger.error("")


def log_info(message: str):
    """Записать информационное сообщение"""
    debug_logger.info(f"ℹ️ {message}")


def clear_log():
    """Очистить лог файл"""
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    debug_logger.info("Лог файл очищен")
