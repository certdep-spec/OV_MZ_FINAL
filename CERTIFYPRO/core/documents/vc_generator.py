"""
Генератор документів ДЛЯ ВЦ (до випробувань) та ФІНАЛЬНИХ документів

Facade паттерн — делегує пайплайнам.
Зберігає повну зворотну сумісність з існуючим GUI.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import config
from documents.context.document_context import DocumentDataService
from documents.document_base import DocumentBase
from documents.pipelines.final_pipeline import FinalPipeline
from documents.pipelines.vc_pipeline import VCPipeline

logger = logging.getLogger(__name__)


class VCDocumentGenerator:
    """
    Facade для генерації документів.

    Делегує оркестрацію пайплайнам.
    Зберігає старий інтерфейс для зворотної сумісності з GUI.
    """

    def __init__(
        self,
        template_dir: str,
        output_dir: str,
        db=None,
        document_service=None,
    ):
        """
        Ініціалізація Facade.

        Args:
            template_dir: Шлях до шаблонів
            output_dir: Шлях до виводу документів
            db: DatabaseManager (legacy, для зворотної сумісності)
            document_service: DocumentService (новий підхід)
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.db_path = config.DB_PATH
        self.db = db  # legacy
        self.document_service = document_service

        # Якщо document_service не передано — створюємо
        if self.document_service is None:
            from services.document_service import DocumentService

            self.document_service = DocumentService(
                str(self.db_path), str(template_dir), str(output_dir)
            )

        # Ініціалізація сервісу даних
        self.context_builder = DocumentDataService(self.document_service)

        # Ініціалізація пайплайнів
        self.vc_pipeline = VCPipeline(
            self.template_dir, self.output_dir, self.context_builder
        )
        self.final_pipeline = FinalPipeline(
            self.template_dir, self.output_dir, self.context_builder
        )

    # ===== ПУБЛІЧНІ МЕТОДИ (ЗВОРОТНА СУМІСНІСТЬ) =====

    def format_app_number(self, app_number: str) -> str:
        """Форматує номер заявки"""
        return DocumentBase.format_app_number(app_number)

    def create_structured_path(self, app_number: str, app_date: str) -> Path:
        """Створення структурованої папки"""
        return DocumentBase.create_structured_path(
            self.output_dir, app_number, app_date
        )

    def get_standards_text(self, standard_ids: List[int]) -> Dict[str, str]:
        """Отримати текст стандартів за їх ID"""
        return self.document_service.get_standards_text(standard_ids)

    def get_available_versions(self, product_name: str) -> List[str]:
        """Отримати список доступних версій для продукту"""
        return self.document_service.get_available_versions(product_name)

    def get_ingredients_for_product(
        self, product_name: str, version: Optional[str] = None
    ) -> List[Dict]:
        """Отримати склад продукції (ПАР)"""
        return self.context_builder.get_ingredients_with_version(product_name, version)

    def calculate_expiry_date(self, mfg_date: str, shelf_life_months: int) -> str:
        """Розрахунок терміну придатності"""
        return DocumentBase.calculate_expiry_date(mfg_date, shelf_life_months)

    def generate_vc_documents(self, app_data: Dict, parties: List[Dict]) -> Dict:
        """
        Генерація всіх документів ДЛЯ ВЦ (до випробувань).

        Делегує VCPipeline.
        """
        try:
            folder = self.create_structured_path(
                app_data["app_number"], app_data["app_date"]
            )
            file_date = self.vc_pipeline._get_file_date()

            return self.vc_pipeline.execute(
                app_data=app_data,
                parties=parties,
                folder=folder,
                file_date=file_date,
            )
        except Exception as e:
            logger.error(f"❌ Помилка генерації ВЦ документів: {e}", exc_info=True)
            return {
                "zayavka": 0,
                "dodatok": 0,
                "perelik": 0,
                "protocol": 0,
                "reshennya": 0,
                "akt_vidbir": 0,
                "akt_ident": 0,
            }

    def generate_final_documents_for_party(
        self, party_data: Dict, app_data: Dict, party_id: int
    ) -> Dict:
        """
        Генерація ФІНАЛЬНИХ документів для ОДНІЄЇ партії.

        Делегує FinalPipeline.
        """
        try:
            folder = self.create_structured_path(
                app_data["app_number"], app_data["app_date"]
            )
            file_date = self.final_pipeline._get_file_date()

            return self.final_pipeline.execute(
                app_data=app_data,
                party_data=party_data,
                party_id=party_id,
                folder=folder,
                file_date=file_date,
            )
        except Exception as e:
            logger.error(
                f"❌ Помилка генерації фінальних документів: {e}",
                exc_info=True,
            )
            return {
                "sertifikat": 0,
                "deklaracija": 0,
                "ugoda": 0,
                "rishennya_vidachu": 0,
                "protokol_analiz": 0,
                "vysnovok": 0,
                "folder": "",
            }

    # СТАРИЙ МЕТОД — для зворотної сумісності
    def generate_final_documents(
        self, party_data: Dict, app_data: Dict, party_id: int = 0
    ) -> Dict:
        """
        Wrapper для зворотної сумісності.
        Використовуйте замість цього generate_final_documents_for_party()
        """
        return self.generate_final_documents_for_party(party_data, app_data, party_id)
