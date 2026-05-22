"""
Генератор Угоди (Мультиклієнтська версія)
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from documents.document_base import DocumentBase
from documents.template_resolver import build_template_name

logger = logging.getLogger(__name__)


class UgodaGenerator(DocumentBase):
    """Генерує Угоду"""

    def get_template_name(self, is_import: bool = False) -> str:
        """
        Повернути ім'я шаблону угоди.

        Args:
            is_import: True для імпортної продукції, False для вітчизняної

        Returns:
            Назва файлу шаблону
        """
        if is_import:
            return build_template_name("12_Угода_бланк_імпорт")
        return build_template_name("12_Угода_бланк")

    def _detect_import_type(self, app_data: Dict, party_data: Dict) -> bool:
        """
        Визначити чи є продукція імпортною.

        Логіка визначення:
        1. Перевірити чи підтримує клієнт імпортну продукцію (feature flag)
        2. Якщо в party_data або app_data є явний прапорець 'is_import' - використовувати його
        3. Якщо прапорця немає - перевірити чи співпадає Заявитель і Виробник
        4. Якщо не вдалося визначити - за замовчуванням вважати вітчизняною (False)
        """
        # 0. Перевіряємо чи підтримується імпорт для цього клієнта
        try:
            from config import has_feature

            if not has_feature("import_product"):
                return False
        except Exception:
            pass

        # 1. Перевіряємо явний прапорець
        if party_data and party_data.get("is_import") is not None:
            return bool(party_data["is_import"])

        if app_data and app_data.get("is_import") is not None:
            return bool(app_data["is_import"])

        # 2. Автоматичне визначення за співпадінням Заявитель == Виробник
        try:
            applicant_name = app_data.get("company_name", "").strip()
            production_address = app_data.get("production_address", "").strip()

            if not applicant_name or not production_address:
                return False

            from config import DB_PATH
            from services.dictionary_service import DictionaryService

            dict_service = DictionaryService(str(DB_PATH))
            facility = dict_service.get_facility_by_address(production_address)

            if facility and facility.company_name:
                manufacturer_name = facility.company_name.strip()
                is_domestic = applicant_name.lower() == manufacturer_name.lower()
                return not is_domestic

        except Exception as e:
            logger.warning(f"Не вдалося визначити тип продукції: {e}")

        return False

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
        """Генерує Угоду для однієї партії"""
        result = {"ugoda": 0}

        try:
            self._validate_app_data(app_data)
            if not party_data:
                return result

            if folder is None:
                folder = self.create_structured_path(
                    self.output_dir,
                    app_data["app_number"],
                    app_data["app_date"],
                )

            if file_date is None:
                file_date = self._get_file_date()

            # Визначаємо тип угоди (імпортна чи вітчизняна)
            is_import = self._detect_import_type(app_data, party_data)
            template_name = self.get_template_name(is_import)

            formatted_app_num = self.format_app_number(app_data["app_number"])
            party_code = party_data.get("party_code", "01E")
            filename = f"Угода_{formatted_app_num}_{party_code}_п{party_id}_{file_date}.docx"
            save_path = str(folder / filename)

            replacements = self._build_final_replacements(
                app_data, party_data, party_id, par_certificates
            )

            logger.info(
                f"📄 Генерація Угоди для партії {party_id} (імпорт={is_import})..."
            )
            if self.generate_with_copy_and_replace(
                template_name, replacements, save_path
            ):
                result["ugoda"] = 1

        except Exception as e:
            logger.error(f"❌ Помилка генерації Угоди: {e}", exc_info=True)

        return result
