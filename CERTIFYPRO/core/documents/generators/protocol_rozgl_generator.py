"""
Генератор Протоколу розгляду заявки
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from documents.document_base import DocumentBase
from documents.template_resolver import build_template_name

logger = logging.getLogger(__name__)


class ProtocolRozglGenerator(DocumentBase):
    """Генерує Протокол розгляду заявки"""

    def get_template_name(self) -> str:
        return build_template_name("3_Протокол_розгляду_бланк")

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
        Генерує Протокол розгляду.

        Args:
            app_data: Дані заявки
            party_data: Не використовується для цього документа
            party_id: Не використовується
            folder: Папка для збереження
            file_date: Дата для імені файлу
            standards_text: Текст стандартів

        Returns:
            {'protocol': 1} якщо успішно
        """
        result = {"protocol": 0}

        try:
            self._validate_app_data(app_data)

            if folder is None:
                folder = self.create_structured_path(
                    self.output_dir,
                    app_data["app_number"],
                    app_data["app_date"],
                )

            if file_date is None:
                file_date = self._get_file_date()

            formatted_app_num = self.format_app_number(app_data["app_number"])
            filename = f"Протокол_розгляду_{formatted_app_num}_{file_date}.docx"
            save_path = str(folder / filename)

            # Побудова контексту
            context = {
                "B1": formatted_app_num,
                "B2": app_data.get("app_date", ""),
                "B3": app_data.get("company_name", ""),
                "B4": app_data.get("company_code", ""),
                "B5": app_data.get("production_address", ""),
                "B6": app_data.get("tu_code", ""),
                "B7": app_data.get("director_name", ""),
            }

            # Додати стандарти
            if standards_text:
                context.update(standards_text)

            logger.info("📄 Генерація Протоколу розгляду...")
            if self.generate_with_docxtpl(self.get_template_name(), context, save_path):
                result["protocol"] = 1
                logger.info("✅ Протокол розгляду згенеровано")

        except Exception as e:
            logger.error(f"❌ Помилка генерації Протоколу розгляду: {e}", exc_info=True)

        return result
