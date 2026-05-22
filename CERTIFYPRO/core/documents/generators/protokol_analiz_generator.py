"""
Генератор Протоколу аналізування
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from documents.document_base import DocumentBase
from documents.template_resolver import build_template_name

logger = logging.getLogger(__name__)


class ProtokolAnalizGenerator(DocumentBase):
    """Генерує Протокол аналізування"""

    def get_template_name(self) -> str:
        return build_template_name("7_Протокол_аналізування_бланк")

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
        Генерує Протокол аналізування для однієї партії.

        Особливість: використовує protocol_date замість party_date для тегу [C11]
        """
        result = {"protokol_analiz": 0}

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

            formatted_app_num = self.format_app_number(app_data["app_number"])
            party_code = party_data.get("party_code", "01E")
            filename = f"Протокол_аналізування_{formatted_app_num}_{party_code}_п{party_id}_{file_date}.docx"
            save_path = str(folder / filename)

            # Базові заміни
            replacements = self._build_final_replacements(
                app_data, party_data, party_id, par_certificates
            )

            # Особливість: для протоколу використовуємо protocol_date замість party_date
            protocol_date = party_data.get("protocol_date", "").strip()
            replacements["[C11]"] = protocol_date
            replacements["{{C11}}"] = protocol_date
            replacements["{C11}"] = protocol_date

            logger.info(f"📄 Генерація Протоколу аналізування для партії {party_id}...")
            if self.generate_with_copy_and_replace(
                self.get_template_name(), replacements, save_path
            ):
                result["protokol_analiz"] = 1

        except Exception as e:
            logger.error(
                f"❌ Помилка генерації Протоколу аналізування: {e}",
                exc_info=True,
            )

        return result
