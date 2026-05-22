"""
Абстрактний базовий клас для пайплайнів генерації документів.

Визначає спільний інтерфейс для всіх пайплайнів.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BasePipeline(ABC):
    """
    Базовий клас пайплайну генерації документів.

    Кожен нащадок визначає конкретну послідовність
    генерації документів (ВЦ, фінальні, тощо).
    """

    def __init__(self, name: str):
        """
        Ініціалізація пайплайну.

        Args:
            name: Назва пайплайну (для логування)
        """
        self.name = name

    def _get_file_date(self) -> str:
        """Отримати поточну дату для імені файлу."""
        return datetime.now().strftime("%Y-%m-%d")

    def _print_report(self, results: Dict[str, Any], folder: Path = None):
        """
        Друкує звіт про генерацію документів.

        Нащадки повинні перевизначити цей метод для
        специфічного звіту.

        Args:
            results: Словник з результатами генерації
            folder: Шлях до папки з документами
        """
        logger.info("\n" + "=" * 60)
        logger.info(f"📊 ЗВІТ ПРО ГЕНЕРАЦІЮ: {self.name}")
        logger.info("=" * 60)
        if folder:
            logger.info(f"📁 Папка: {folder}")
        for key, value in results.items():
            if key != "folder" and isinstance(value, int):
                logger.info(f"✅ {key}: {value}")
        total = sum(
            v for k, v in results.items() if k != "folder" and isinstance(v, int)
        )
        logger.info(f"📋 Всього згенеровано: {total} документів")
        logger.info("=" * 60 + "\n")

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Виконати пайплайн генерації документів.

        Returns:
            Словник з результатами генерації
        """
