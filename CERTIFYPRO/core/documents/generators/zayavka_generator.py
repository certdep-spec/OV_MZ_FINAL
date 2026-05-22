"""
Генератор Заявки (з реєстрацією та додатками)
Оркестратор: делегує реєстрацію та додатки окремим модулям.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from documents import tags as T
from documents.app_registration import ApplicationRegistrar
from documents.appendix_builder import append_appendix
from documents.context.document_context import DocumentDataService
from documents.document_base import DocumentBase
from documents.template_resolver import build_template_name

logger = logging.getLogger(__name__)


class ZayavkaGenerator(DocumentBase):
    """
    Генерує Заявку + Реєстрація + Додатки

    Делегує:
    - Реєстрацію → ApplicationRegistrar
    - Додатки → append_appendix()
    """

    def __init__(
        self,
        template_dir: Path,
        output_dir: Path,
        data_service: DocumentDataService,
    ):
        super().__init__(template_dir, output_dir)
        self.data_service = data_service

    def get_template_name(self) -> str:
        return build_template_name("1_Заявка_бланк")

    def generate(
        self,
        app_data: Dict,
        party_data: Optional[Dict] = None,
        party_id: int = 0,
        parties: Optional[List[Dict]] = None,
        folder: Optional[Path] = None,
        file_date: Optional[str] = None,
        standards_text: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, int]:
        """
        Генерує Заявку + Реєстрація + Додатки.

        Returns:
            {'zayavka': 1, 'dodatok': 1} якщо успішно
        """
        result = {"zayavka": 0, "dodatok": 0}

        try:
            self._validate_app_data(app_data)
            if not parties:
                logger.warning("⚠️ parties відсутній для ZayavkaGenerator")
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
            filename = f"Заявка_{formatted_app_num}_{file_date}.docx"
            zayavka_path = str(folder / filename)

            # ===== ЕТАП 1: Генерація заявки =====
            logger.info("📄 1. Генерація Заявки...")
            context = self._build_zayavka_context(
                app_data, parties, formatted_app_num, standards_text
            )

            if not self.generate_with_docxtpl(
                self.get_template_name(), context, zayavka_path
            ):
                return result

            result["zayavka"] = 1

            # ===== ЕТАП 2: Реєстрація заявки =====
            logger.info("📄 2. Реєстрація Заявки...")
            ApplicationRegistrar.register(Path(zayavka_path), app_data)

            # ===== ЕТАП 3: Додавання додатків =====
            logger.info("📄 3. Додавання Додатків до Заявки...")
            if append_appendix(
                Path(zayavka_path), app_data, parties, self.data_service
            ):
                result["dodatok"] = 1

        except Exception as e:
            logger.error(f"❌ Помилка генерації Заявки: {e}", exc_info=True)

        return result

    def _build_zayavka_context(
        self,
        app_data: Dict,
        parties: List[Dict],
        formatted_app_num: str,
        standards_text: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """Побудова контексту для заявки"""
        reg_data = self.format_registration_data(
            app_data.get("app_number", ""), app_data.get("app_date", "")
        )

        first_party_unit = parties[0].get("unit", "шт") if parties else "шт"

        context = {
            T.strip_brackets(T.APP_NUMBER): formatted_app_num,
            T.strip_brackets(T.APP_DATE): app_data.get("app_date", ""),
            T.strip_brackets(T.COMPANY_NAME): app_data.get("company_name", ""),
            T.strip_brackets(T.COMPANY_CODE): app_data.get("company_code", ""),
            T.strip_brackets(T.PRODUCTION_ADDRESS): app_data.get(
                "production_address", ""
            ),
            T.strip_brackets(T.TU_CODE): app_data.get("tu_code", ""),
            T.strip_brackets(T.DIRECTOR_NAME): app_data.get("director_name", ""),
            T.strip_brackets(T.PROTOCOL): first_party_unit,
            T.strip_brackets(T.REG_NUMBER): reg_data["reg_number"],
            T.strip_brackets(T.REG_DATE): reg_data["reg_date"],
        }

        if standards_text:
            context.update(standards_text)

        return context
