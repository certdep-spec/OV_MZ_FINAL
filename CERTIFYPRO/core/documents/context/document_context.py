"""
DocumentDataService — сервіс для збору даних, необхідних генераторам документів.

Відповідає за:
- Збір унікальних ID стандартів з партій
- Отримання тексту стандартів з БД
- Отримання інгредієнтів для продукту (з урахуванням версії)
- Групування партій за продуктами
- Визначення версії складу для продукту
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class DocumentDataService:
    """
    Підготовлює дані для генераторів документів.

    Відповідає за:
    - Збір унікальних ID стандартів
    - Отримання тексту стандартів
    - Отримання інгредієнтів для продукту
    - Групування партій за продуктами
    """

    def __init__(self, document_service):
        """
        Ініціалізація.

        Args:
            document_service: DocumentService для запитів до БД
        """
        self.document_service = document_service

    def collect_all_standards(self, parties: List[Dict]) -> Dict[str, str]:
        """
        Збирає всі унікальні ID стандартів з усіх партій.

        Args:
            parties: Список даних партій

        Returns:
            Словник {STD_ID: текст_стандарту}
        """
        all_standard_ids: Set[int] = set()

        for party in parties:
            if party.get("standards"):
                for std in party["standards"]:
                    if isinstance(std, dict) and "id" in std:
                        all_standard_ids.add(int(std["id"]))
                    elif isinstance(std, int):
                        all_standard_ids.add(std)

        if all_standard_ids:
            standards_text = self.document_service.get_standards_text(
                list(all_standard_ids)
            )
            logger.info(f"📋 Зібрано {len(all_standard_ids)} стандартів")
            return standards_text

        return {}

    def collect_party_standards(self, party: Dict) -> Dict[str, str]:
        """
        Збирає стандарти для конкретної партії.

        Args:
            party: Дані партії

        Returns:
            Словник {STD_ID: текст_стандарту}
        """
        party_standard_ids: List[int] = []

        if party.get("standards"):
            for std in party["standards"]:
                if isinstance(std, dict) and "id" in std:
                    party_standard_ids.append(int(std["id"]))
                elif isinstance(std, int):
                    party_standard_ids.append(std)

        if party_standard_ids:
            return self.document_service.get_standards_text(party_standard_ids)

        return {}

    def get_ingredients_with_version(
        self, product_name: str, version: Optional[str] = None
    ) -> List[Dict]:
        """
        Отримує інгредієнти для продукту з урахуванням версії.

        Args:
            product_name: Назва продукту
            version: Версія складу (опціонально)

        Returns:
            Список інгредієнтів (без дублікатів)
        """
        ingredients_dto = self.document_service.get_ingredients_for_product(
            product_name, version or ""
        )

        # Конвертуємо DTO у dict та видаляємо дублікати
        ingredients = []
        seen = set()

        for ing in ingredients_dto:
            key = (
                ing.chemical_name or "",
                ing.trade_mark or "",
                ing.cas_number or "",
                ing.certificate or "",
            )

            if key not in seen:
                seen.add(key)
                ingredients.append(
                    {
                        "chemical_name": ing.chemical_name or "",
                        "trade_mark": ing.trade_mark or "",
                        "cas_number": ing.cas_number or "",
                        "certificate": ing.certificate or "",
                    }
                )

        logger.info(
            f"   📋 Знайдено {len(ingredients)} унікальних інгредієнтів "
            f"для '{product_name[:50]}' (Версія: {version})"
        )
        return ingredients

    def get_par_certificates(
        self, product_name: str, version: Optional[str] = None
    ) -> str:
        """
        Отримує список сертифікатів ПАР для продукту.

        Args:
            product_name: Назва продукту
            version: Версія складу (опціонально)

        Returns:
            Рядок з переліком сертифікатів через кому
        """
        return self.document_service.get_par_certificates(product_name, version or "")

    def get_available_versions(self, product_name: str) -> List[str]:
        """
        Отримує доступні версії складу для продукту.

        Args:
            product_name: Назва продукту

        Returns:
            Список версій
        """
        return self.document_service.get_available_versions(product_name)

    def group_parties_by_product(self, parties: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Групує партії за продуктами.

        Args:
            parties: Список даних партій

        Returns:
            Словник {назва_продукту: [партії]}
        """
        products_dict: Dict[str, List[Dict]] = {}

        for party in parties:
            product_name = party.get("product_name", "")
            if product_name not in products_dict:
                products_dict[product_name] = []
            products_dict[product_name].append(party)

        logger.info(f"📦 Знайдено продуктів: {len(products_dict)}")
        return products_dict

    def select_version_for_product(
        self, product_name: str, parties: List[Dict]
    ) -> Optional[str]:
        """
        Визначає версію складу для продукту.
        Якщо в партії явно вказана версія - використовує її.
        Інакше, якщо версій кілька - повертає першу.

        Args:
            product_name: Назва продукту
            parties: Партії цього продукту

        Returns:
            Обрана версія або None
        """
        # Спершу перевіримо, чи вказана версія безпосередньо у переданих партіях
        for party in parties:
            p_ver = party.get("version")
            if p_ver:
                logger.info(f"🎯 Використовуємо версію '{p_ver}' з деталей партії для продукту '{product_name[:30]}'")
                return p_ver

        versions = self.get_available_versions(product_name)

        if len(versions) >= 2:
            logger.warning(
                f"   ⚠️ Знайдено {len(versions)} версій складу для {product_name[:30]}. "
                f"Використовую першу: {versions[0]}"
            )
            return versions[0]
        elif len(versions) == 1:
            return versions[0]

        return None


# Backward-compat alias (старый код может ещё использовать DocumentContextBuilder)
DocumentContextBuilder = DocumentDataService
