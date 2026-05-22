"""
Генератор Висновку відповідності
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from documents.document_base import DocumentBase
from documents.template_resolver import build_template_name

logger = logging.getLogger(__name__)


class VysnovokGenerator(DocumentBase):
    """Генерує Висновок відповідності"""

    def get_template_name(self) -> str:
        return build_template_name("8_Результат_дій_з_оцінення_бланк")

    def generate(
        self,
        app_data: Dict,
        party_data: Optional[Dict] = None,
        party_id: int = 0,
        folder: Optional[Path] = None,
        file_date: Optional[str] = None,
        par_certificates: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, int]:
        """
        Генерує Висновок для однієї партії.

        Args:
            app_data: Дані заявки
            party_data: Дані партії
            party_id: ID партії
            folder: Папка для збереження
            file_date: Дата для імені файлу
            par_certificates: Сертифікати ПАР

        Returns:
            {'vysnovok': 1} якщо успішно
        """
        result = {"vysnovok": 0}

        try:
            self._validate_app_data(app_data)
            if not party_data:
                logger.warning("⚠️ party_data відсутній для VysnovokGenerator")
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
            filename = f"Висновок_{formatted_app_num}_{party_code}_п{party_id}_{file_date}.docx"
            save_path = str(folder / filename)

            # Побудова замін
            replacements = self._build_final_replacements(
                app_data, party_data, party_id, par_certificates
            )

            logger.info(f"📄 Генерація Висновку для партії {party_id}...")
            if self.generate_with_copy_and_replace(
                self.get_template_name(), replacements, save_path
            ):
                result["vysnovok"] = 1
                logger.info("✅ Висновок згенеровано")

        except Exception as e:
            logger.error(f"❌ Помилка генерації Висновку: {e}", exc_info=True)

        return result

    def _build_final_replacements(
        self,
        app_data: Dict,
        party_data: Dict,
        party_id: int,
        par_certificates: Optional[str] = None,
    ) -> Dict[str, str]:
        """Побудова замін (делегує в DocumentBase)"""
        return super()._build_final_replacements(
            app_data, party_data, party_id, par_certificates
        )
