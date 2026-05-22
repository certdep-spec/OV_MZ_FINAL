"""
Сервіс генерації документів
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from models.dto import (
    ApplicationDTO,
    DocumentContextDTO,
    IngredientDTO,
    PartyDTO,
)
from utils.path_utils import create_structured_path as _create_structured_path

from .base_service import BaseService
from .dictionary_service import DictionaryService

logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    """Сервіс для генерації документів"""

    def __init__(self, db_path: str, template_dir: str, output_dir: str):
        super().__init__(db_path)
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        # Перевикористовуємо DictionaryService замість дублювання запитів
        self._dict_service = DictionaryService(db_path)

    def create_structured_path(self, app_number: str, app_date: str) -> Path:
        """Створення структурованої папки для документів"""
        return _create_structured_path(self.output_dir, app_number, app_date)

    def get_standards_text(self, standard_ids: List[int]) -> Dict[str, str]:
        """Отримати тексти стандартів за їх ID (один запит замість N)"""
        result: Dict[str, str] = {f"STD{i}": "" for i in range(1, 7)}
        result["STD_ALL"] = ""

        if not standard_ids:
            return result

        # Фільтруємо тільки валідні ID (1–6) та робимо один запит
        valid_ids = [sid for sid in standard_ids if 1 <= sid <= 6]
        if not valid_ids:
            return result

        placeholders = ",".join("?" * len(valid_ids))
        rows = self._execute_query(
            f"SELECT {self.StandardColumns.ID}, {self.StandardColumns.DESCRIPTION} FROM {self.Tables.STANDARDS} WHERE {self.StandardColumns.ID} IN ({placeholders})",
            tuple(valid_ids),
        )
        for row in rows:
            result[f"STD{self._get_value(row, 'id')}"] = self._get_value(
                row, "description"
            )

        # Конкатенуємо всі знайдені стандарти по порядку для STD_ALL
        descriptions = []
        for i in range(1, 7):
            desc = result[f"STD{i}"]
            if desc:
                descriptions.append(desc.strip())
        if descriptions:
            result["STD_ALL"] = ", ".join(descriptions)

        return result

    def get_ingredients_for_product(
        self, product_name: str, version: Optional[str] = None
    ) -> List[IngredientDTO]:
        """Отримати інгредієнти для продукту (делегування до DictionaryService)"""
        return self._dict_service.get_ingredients_by_product(product_name, version)

    def get_available_versions(self, product_name: str) -> List[str]:
        """Отримати список унікальних версій складу для продукту"""
        return self._dict_service.get_unique_versions_for_product(product_name)

    def get_par_certificates(self, product_name: str, version: str = "") -> str:
        """Отримати список сертифікатів ПАР для продукту та версії (делегування до DictionaryService)"""
        return self._dict_service.get_par_certificates(product_name, version)

    def build_document_context(
        self, application: ApplicationDTO, parties: List[PartyDTO]
    ) -> DocumentContextDTO:
        """Побудувати контекст для генерації документів"""
        # Зібрати унікальні стандарти з усіх партій
        all_standard_ids: set = set()
        for party in parties:
            all_standard_ids.update(party.standards)

        # Отримати тексти стандартів одним запитом
        standards_text = self.get_standards_text(list(all_standard_ids))

        # Зібрати унікальні продукти та їх інгредієнти (batch-запит)
        products_dict: Dict[str, List[IngredientDTO]] = {}
        unique_products = {party.product_name for party in parties}
        if unique_products:
            all_ingredients = self._dict_service.get_ingredients_for_products(
                list(unique_products)
            )
            for product_name in unique_products:
                products_dict[product_name] = [
                    ing for ing in all_ingredients if ing.product_name == product_name
                ]
        else:
            for party in parties:
                product_name = party.product_name
                if product_name not in products_dict:
                    products_dict[product_name] = self.get_ingredients_for_product(
                        product_name
                    )

        return DocumentContextDTO(
            application=application,
            parties=parties,
            products=products_dict,
            standards_text=standards_text,
        )
