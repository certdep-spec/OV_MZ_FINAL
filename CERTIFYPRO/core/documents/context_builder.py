import logging
from typing import Any, Dict, List, Optional

from models.dto import (
    ApplicationDTO,
    DocumentContextDTO,
    IngredientDTO,
    PartyDTO,
)

logger = logging.getLogger(__name__)


class DocumentContextBuilder:
    """
    Паттерн Builder для підготовки та збирання даних (DocumentContextDTO).
    Забезпечує чисте інстанціювання контексту без витоків логіки БД у генератори.
    """

    def __init__(self):
        self._application: Optional[ApplicationDTO] = None
        self._parties: List[PartyDTO] = []
        self._products: Dict[str, List[IngredientDTO]] = {}
        self._standards_text: Dict[str, str] = {}

    def with_application(
        self, app_data: Dict[str, Any], parties_data: List[Dict[str, Any]]
    ) -> "DocumentContextBuilder":
        """Ініціалізація з сирих словників, які повертає legacy DatabaseManager (або ApplicationService)"""
        if isinstance(app_data, dict):
            self._application = ApplicationDTO(
                app_number=str(app_data.get("app_number", "")),
                app_date=app_data.get("app_date", ""),
                company_name=app_data.get("company_name", ""),
                company_code=app_data.get("company_code", ""),
                production_address=app_data.get("production_address", ""),
                director_name=app_data.get("director_name", ""),
                tu_code=app_data.get("tu_code", ""),
            )
        else:
            self._application = app_data

        self._parties = []
        for p in parties_data:
            if isinstance(p, dict):
                # парсинг standard ids (у старому коді це список int або [{'id': X}])
                standards = []
                for std in p.get("standards", []):
                    if isinstance(std, dict) and "id" in std:
                        standards.append(int(std["id"]))
                    elif isinstance(std, int):
                        standards.append(std)

                self._parties.append(
                    PartyDTO(
                        product_name=p.get("product_name", ""),
                        unit=p.get("unit", "шт"),
                        party_code=p.get("party_code", ""),
                        party_date=p.get("party_date", ""),
                        mfg_date=p.get("mfg_date", ""),
                        quantity=float(p.get("quantity", 0) or 0),
                        cert_number=p.get("cert_number", ""),
                        cert_date=p.get("cert_date", ""),
                        protocol_number=p.get("protocol_number", ""),
                        protocol_date=p.get("protocol_date", ""),
                        shelf_life_months=int(p.get("shelf_life_months", 36)),
                        standards=standards,
                        version=p.get("version", ""),
                    )
                )
            else:
                self._parties.append(p)

        return self

    def with_standards_text(
        self, standards_dict: Dict[str, str]
    ) -> "DocumentContextBuilder":
        """Завантажує словник з текстовими значеннями стандартів ([1]: 'Текст...')"""
        self._standards_text = standards_dict
        return self

    def with_product_ingredients(
        self, product_name: str, ingredients: List[Dict[str, Any]]
    ) -> "DocumentContextBuilder":
        """Додає склад для конкретного продукту"""
        ing_dtos = []
        for ing in ingredients:
            if isinstance(ing, dict):
                ing_dtos.append(
                    IngredientDTO(
                        product_name=product_name,
                        chemical_name=ing.get("chemical_name", ""),
                        trade_mark=ing.get("trade_mark", ""),
                        cas_number=ing.get("cas_number", ""),
                        certificate=ing.get("certificate", ""),
                        version=ing.get("version", ""),
                    )
                )
            else:
                ing_dtos.append(ing)
        self._products[product_name] = ing_dtos
        return self

    def build(self) -> DocumentContextDTO:
        """Повертає готовий контекст для генераторів"""
        if not self._application:
            raise ValueError(
                "Дані заявки відсутні. Викличте with_application() першим."
            )

        return DocumentContextDTO(
            application=self._application,
            parties=self._parties,
            products=self._products,
            standards_text=self._standards_text,
        )
