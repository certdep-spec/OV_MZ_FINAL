"""
Базовий клас для генераторів партійних документів ВЦ.

Усуває дублювання між PerelikGenerator, ReshenyaGenerator,
AktVidbirGenerator, AktIdentGenerator.

Нащадки перевизначають лише:
- get_template_name()
- filename_prefix
- result_key
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

from documents.document_base import DocumentBase

logger = logging.getLogger(__name__)


class BasePartyDocumentGenerator(DocumentBase, ABC):
    """
    Базовий генератор для документів партії з однаковим контекстом.

    Всі нащадки мають однакову структуру generate():
    - Валідація app_data
    - Створення папки
    - Побудова контексту (B1-B7, B10-I10, UNIT, A1, A10, C11, FIN)
    - Додавання standards_text
    - Генерація через docxtpl

    Відмінності лише в імені шаблону, префіксі файлу та ключі результату.
    """

    @abstractmethod
    def filename_prefix(self) -> str:
        """Префікс для імені файлу (напр. 'Перелік', 'Рішення')"""

    @abstractmethod
    def result_key(self) -> str:
        """Ключ у словнику результатів (напр. 'perelik', 'reshennya')"""

    def _build_vc_context(
        self,
        app_data: Dict,
        party_data: Dict,
        party_id: int,
        standards_text: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Побудувати контекст для ВЦ документів (Заявка/Перелік/Рішення/Акти).

        Args:
            app_data: Дані заявки
            party_data: Дані партії
            party_id: ID партії
            standards_text: Текст стандартів ({'[1]': '...', ...})

        Returns:
            Словник контексту для docxtpl
        """
        formatted_app_num = self.format_app_number(app_data["app_number"])

        context = {
            "B1": formatted_app_num,
            "B2": app_data.get("app_date", ""),
            "B3": app_data.get("company_name", ""),
            "B4": app_data.get("company_code", ""),
            "B5": app_data.get("production_address", ""),
            "B6": app_data.get("tu_code", ""),
            "B7": app_data.get("director_name", ""),
            "B10": party_data.get("product_name", ""),
            "C10": party_data.get("party_code", "01E"),
            "D10": party_data.get("party_date", ""),
            "E10": party_data.get("mfg_date", ""),
            "F10": str(party_data.get("quantity", 0)),
            "G10": party_data.get("unit", "шт"),
            "UNIT": party_data.get("unit", "шт"),
            "A1": str(party_id),
            "A10": str(party_id),
            "C11": party_data.get("party_date", ""),
            "H10": party_data.get("cert_number", ""),
            "I10": party_data.get("cert_date", ""),
        }

        # Розрахунок терміну придатності
        expiry_date = self.calculate_expiry_date(
            party_data.get("mfg_date", ""),
            party_data.get("shelf_life_months", 36),
        )
        context["FIN"] = expiry_date

        # Додати стандарти
        if standards_text:
            context.update(standards_text)

        return context

    def generate(
        self,
        app_data: Dict,
        party_data: Optional[Dict] = None,
        party_id: int = 0,
        folder: Optional[Path] = None,
        file_date: Optional[str] = None,
        standards_text: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, int]:
        """
        Генерує документ для однієї партії.

        Args:
            app_data: Дані заявки
            party_data: Дані партії
            party_id: ID партії
            folder: Папка для збереження
            file_date: Дата для імені файлу
            standards_text: Текст стандартів

        Returns:
            {result_key: 1} якщо успішно
        """
        result = {self.result_key: 0}

        try:
            self._validate_app_data(app_data)
            if not party_data:
                logger.warning(f"⚠️ party_data відсутній для {self.__class__.__name__}")
                return result

            if folder is None:
                folder = self.create_structured_path(
                    self.output_dir,
                    app_data["app_number"],
                    app_data["app_date"],
                )

            if file_date is None:
                file_date = self._get_file_date()

            formatted_app_num = self.format_app_number(app_data["app_number"])
            party_code = party_data.get("party_code", "01E")
            # Додаємо номер партії щоб уникнути перезапису при однакових party_code
            filename = f"{self.filename_prefix}_{formatted_app_num}_{party_code}_п{party_id}_{file_date}.docx"
            save_path = str(folder / filename)

            context = self._build_vc_context(
                app_data, party_data, party_id, standards_text
            )

            logger.info(f"📄 Генерація {self.filename_prefix} для партії {party_id}...")
            if self.generate_with_docxtpl(self.get_template_name(), context, save_path):
                result[self.result_key] = 1
                logger.info(f"✅ {self.filename_prefix} згенеровано")

        except Exception as e:
            logger.error(
                f"❌ Помилка генерації {self.filename_prefix}: {e}",
                exc_info=True,
            )

        return result
