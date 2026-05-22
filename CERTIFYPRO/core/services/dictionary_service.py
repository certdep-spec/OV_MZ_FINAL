"""
Сервіс управління довідниками
"""

import logging
from functools import lru_cache
from typing import Any, List, Optional

from models.dto import (
    IngredientDTO,
    ProductDTO,
    ProductionFacilityDTO,
    StandardDTO,
)

from .base_service import BaseService

logger = logging.getLogger(__name__)

from utils.version_normalizer import normalize_version


class DictionaryService(BaseService):
    """Сервіс для роботи з довідниками системи"""

    @classmethod
    def clear_all_caches(cls):
        """Очистити всі кеші сервісу довідників"""
        try:
            cls.get_all_products.cache_clear()
            cls.get_all_standards.cache_clear()
            cls.get_all_facilities.cache_clear()
            logger.info("🧹 Кеші DictionaryService очищено")
        except Exception as e:
            logger.warning(f"Не вдалося очистити кеш DictionaryService: {e}")

    # ===== ПРИВАТНІ МАППЕРИ =====

    def _row_to_product(self, row: Any) -> ProductDTO:
        """Конвертувати рядок БД в ProductDTO"""
        return ProductDTO(
            id=self._get_value(row, self.ProductColumns.ID),
            name=self._get_value(row, self.ProductColumns.NAME),
            tu_code=self._get_value(row, self.ProductColumns.TU_CODE, ""),
            shelf_life_months=self._get_value(row, self.ProductColumns.SHELF_LIFE_MONTHS, 36),
            dkpp_code=self._get_value(row, self.ProductColumns.DKPP_CODE, "20.41.32-50.00"),
            uktzed_code=self._get_value(row, self.ProductColumns.UKTZED_CODE, "3402"),
            created_at=self._get_value(row, self.ProductColumns.CREATED_AT),
        )

    # ===== ПРОДУКЦІЯ =====

    _PRODUCT_SELECT = (
        f"SELECT {BaseService.ProductColumns.ID}, {BaseService.ProductColumns.NAME}, {BaseService.ProductColumns.TU_CODE}, "
        f"{BaseService.ProductColumns.SHELF_LIFE_MONTHS}, {BaseService.ProductColumns.DKPP_CODE}, "
        f"{BaseService.ProductColumns.UKTZED_CODE}, {BaseService.ProductColumns.CREATED_AT} "
        f"FROM {BaseService.Tables.PRODUCTS}"
    )

    @lru_cache(maxsize=1)
    def get_all_products(self) -> List[ProductDTO]:
        """Отримати всі продукти (з кешуванням)"""
        rows = self._execute_query(f"{self._PRODUCT_SELECT} ORDER BY name")
        return [self._row_to_product(row) for row in rows]

    def get_product_by_name(self, name: str) -> Optional[ProductDTO]:
        """Отримати продукт за назвою"""
        rows = self._execute_query(f"{self._PRODUCT_SELECT} WHERE name = ?", (name,))
        return self._row_to_product(rows[0]) if rows else None

    def get_products_by_tu(self, tu_code: str) -> List[ProductDTO]:
        """Отримати продукти за ТУ"""
        rows = self._execute_query(
            f"{self._PRODUCT_SELECT} WHERE tu_code = ? ORDER BY name",
            (tu_code,),
        )
        return [self._row_to_product(row) for row in rows]

    def add_product(self, product: ProductDTO) -> int:
        """Додати новий продукт"""
        result = self._execute_command(
            f"INSERT INTO {self.Tables.PRODUCTS} ({self.ProductColumns.NAME}, {self.ProductColumns.TU_CODE}, {self.ProductColumns.SHELF_LIFE_MONTHS}, {self.ProductColumns.DKPP_CODE}, {self.ProductColumns.UKTZED_CODE}) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                product.name,
                product.tu_code,
                product.shelf_life_months,
                product.dkpp_code,
                product.uktzed_code,
            ),
        )
        self.get_all_products.cache_clear()
        return result

    def update_product(self, old_name: str, product: ProductDTO) -> bool:
        """Оновити продукт"""
        self._execute_command(
            f"UPDATE {self.Tables.PRODUCTS} SET {self.ProductColumns.NAME}=?, {self.ProductColumns.TU_CODE}=?, {self.ProductColumns.SHELF_LIFE_MONTHS}=?, {self.ProductColumns.DKPP_CODE}=?, {self.ProductColumns.UKTZED_CODE}=? "
            f"WHERE {self.ProductColumns.NAME}=?",
            (
                product.name,
                product.tu_code,
                product.shelf_life_months,
                product.dkpp_code,
                product.uktzed_code,
                old_name,
            ),
        )
        self.get_all_products.cache_clear()
        return True

    def delete_product(self, name: str) -> bool:
        """
        Видалити продукт та всі його інгредієнти.
        Зауваження: Якщо продукт використовується в заявках (партіях),
        це може викликати помилку цілісності БД, якщо є FK.
        """
        try:
            # 1. Спочатку видаляємо всі інгредієнти цього продукту (Склад)
            self._execute_command(
                f"DELETE FROM {self.Tables.INGREDIENTS} WHERE {self.IngredientColumns.PRODUCT_NAME}=?",
                (name,),
            )
            # 2. Потім видаляємо сам продукт
            self._execute_command(
                f"DELETE FROM {self.Tables.PRODUCTS} WHERE {self.ProductColumns.NAME}=?",
                (name,),
            )
            self.get_all_products.cache_clear()
            return True
        except Exception as e:
            logger.error(f"Помилка при видаленні продукту '{name}': {e}")
            raise

    def is_product_in_use(self, name: str) -> bool:
        """Перевірити, чи використовується продукт у існуючих заявках (партіях)"""
        rows = self._execute_query(
            f"SELECT 1 FROM {self.Tables.PARTIES} WHERE {self.PartyColumns.PRODUCT_NAME} = ? LIMIT 1",
            (name,),
        )
        return len(rows) > 0

    # ===== СТАНДАРТИ =====

    @lru_cache(maxsize=2)
    def get_all_standards(self, active_only: bool = True) -> List[StandardDTO]:
        """Отримати всі стандарти (з кешуванням)"""
        if active_only:
            rows = self._execute_query(
                f"SELECT {self.StandardColumns.ID}, {self.StandardColumns.DESCRIPTION}, {self.StandardColumns.ACTIVE} FROM {self.Tables.STANDARDS} WHERE {self.StandardColumns.ACTIVE} = 1 ORDER BY {self.StandardColumns.ID}"
            )
        else:
            rows = self._execute_query(
                f"SELECT {self.StandardColumns.ID}, {self.StandardColumns.DESCRIPTION}, {self.StandardColumns.ACTIVE} FROM {self.Tables.STANDARDS} ORDER BY {self.StandardColumns.ID}"
            )
        return [
            StandardDTO(
                id=self._get_value(row, self.StandardColumns.ID),
                description=self._get_value(row, self.StandardColumns.DESCRIPTION),
                active=bool(self._get_value(row, self.StandardColumns.ACTIVE, False)),
            )
            for row in rows
        ]

    def get_standard_by_id(self, std_id: int) -> Optional[StandardDTO]:
        """Отримати стандарт за ID"""
        rows = self._execute_query(
            f"SELECT {self.StandardColumns.ID}, {self.StandardColumns.DESCRIPTION}, {self.StandardColumns.ACTIVE} FROM {self.Tables.STANDARDS} WHERE {self.StandardColumns.ID} = ?",
            (std_id,),
        )
        if not rows:
            return None
        row = rows[0]
        return StandardDTO(
            id=self._get_value(row, self.StandardColumns.ID),
            description=self._get_value(row, self.StandardColumns.DESCRIPTION),
            active=bool(self._get_value(row, self.StandardColumns.ACTIVE, False)),
        )

    def add_standard(self, standard: StandardDTO) -> int:
        """Додати стандарт"""
        result = self._execute_command(
            f"INSERT INTO {self.Tables.STANDARDS} ({self.StandardColumns.ID}, {self.StandardColumns.DESCRIPTION}, {self.StandardColumns.ACTIVE}) VALUES (?, ?, ?)",
            (standard.id, standard.description, 1 if standard.active else 0),
        )
        self.get_all_standards.cache_clear()
        return result

    def update_standard(self, old_id: int, standard: StandardDTO) -> bool:
        """Оновити стандарт"""
        self._execute_command(
            f"UPDATE {self.Tables.STANDARDS} SET {self.StandardColumns.ID}=?, {self.StandardColumns.DESCRIPTION}=?, {self.StandardColumns.ACTIVE}=? WHERE {self.StandardColumns.ID}=?",
            (
                standard.id,
                standard.description,
                1 if standard.active else 0,
                old_id,
            ),
        )
        self.get_all_standards.cache_clear()
        return True

    def delete_standard(self, std_id: int) -> bool:
        """Видалити стандарт"""
        self._execute_command(
            f"DELETE FROM {self.Tables.STANDARDS} WHERE {self.StandardColumns.ID}=?",
            (std_id,),
        )
        self.get_all_standards.cache_clear()
        return True

    # ===== ВИРОБНИЧІ ПОТУЖНОСТІ =====

    @lru_cache(maxsize=1)
    def get_all_facilities(self) -> List[ProductionFacilityDTO]:
        """Отримати всі потужності (з кешуванням)"""
        rows = self._execute_query(
            f"SELECT {self.FacilityColumns.ID}, {self.FacilityColumns.ADDRESS}, {self.FacilityColumns.COMPANY_NAME} FROM {self.Tables.PRODUCTION_FACILITIES} ORDER BY {self.FacilityColumns.ADDRESS}"
        )
        return [
            ProductionFacilityDTO(
                id=self._get_value(row, self.FacilityColumns.ID),
                address=self._get_value(row, self.FacilityColumns.ADDRESS),
                company_name=self._get_value(row, self.FacilityColumns.COMPANY_NAME, ""),
            )
            for row in rows
        ]

    def get_facility_by_address(self, address: str) -> Optional[ProductionFacilityDTO]:
        """Отримати потужність за адресою"""
        rows = self._execute_query(
            f"SELECT {self.FacilityColumns.ID}, {self.FacilityColumns.ADDRESS}, {self.FacilityColumns.COMPANY_NAME} FROM {self.Tables.PRODUCTION_FACILITIES} WHERE {self.FacilityColumns.ADDRESS} = ?",
            (address,),
        )
        if not rows:
            return None
        row = rows[0]
        return ProductionFacilityDTO(
            id=self._get_value(row, self.FacilityColumns.ID),
            address=self._get_value(row, self.FacilityColumns.ADDRESS),
            company_name=self._get_value(row, self.FacilityColumns.COMPANY_NAME, ""),
        )

    def add_facility(self, facility: ProductionFacilityDTO) -> int:
        """Додати потужність"""
        result = self._execute_command(
            f"INSERT INTO {self.Tables.PRODUCTION_FACILITIES} ({self.FacilityColumns.ADDRESS}, {self.FacilityColumns.COMPANY_NAME}) VALUES (?, ?)",
            (facility.address, facility.company_name),
        )
        self.get_all_facilities.cache_clear()
        return result

    def update_facility(self, old_address: str, facility: ProductionFacilityDTO) -> bool:
        """Оновити потужність"""
        self._execute_command(
            f"UPDATE {self.Tables.PRODUCTION_FACILITIES} SET {self.FacilityColumns.ADDRESS}=?, {self.FacilityColumns.COMPANY_NAME}=? WHERE {self.FacilityColumns.ADDRESS}=?",
            (facility.address, facility.company_name, old_address),
        )
        self.get_all_facilities.cache_clear()
        return True

    def delete_facility(self, address: str) -> bool:
        """Видалити потужність"""
        self._execute_command(
            f"DELETE FROM {self.Tables.PRODUCTION_FACILITIES} WHERE {self.FacilityColumns.ADDRESS}=?",
            (address,),
        )
        self.get_all_facilities.cache_clear()
        return True

    # ===== ІНГРЕДІЄНТИ (СКЛАД) =====

    def _row_to_ingredient(self, row: Any, product_name: str = "") -> IngredientDTO:
        """Конвертувати рядок БД в IngredientDTO"""
        return IngredientDTO(
            id=self._get_value(row, self.IngredientColumns.ID),
            product_name=self._get_value(row, self.IngredientColumns.PRODUCT_NAME, product_name),
            version=self._get_value(row, self.IngredientColumns.VERSION, ""),
            chemical_name=self._get_value(row, self.IngredientColumns.CHEMICAL_NAME, ""),
            trade_mark=self._get_value(row, self.IngredientColumns.TRADE_MARK, ""),
            cas_number=self._get_value(row, self.IngredientColumns.CAS_NUMBER, ""),
            certificate=self._get_value(row, self.IngredientColumns.CERTIFICATE, ""),
        )

    def get_all_ingredients(self) -> List[IngredientDTO]:
        """Отримати всі інгредієнти"""
        rows = self._execute_query(
            f"SELECT {self.IngredientColumns.ID}, {self.IngredientColumns.PRODUCT_NAME}, {self.IngredientColumns.VERSION}, {self.IngredientColumns.CHEMICAL_NAME}, {self.IngredientColumns.TRADE_MARK}, {self.IngredientColumns.CAS_NUMBER}, {self.IngredientColumns.CERTIFICATE} "
            f"FROM {self.Tables.INGREDIENTS} ORDER BY {self.IngredientColumns.PRODUCT_NAME}"
        )
        return [self._row_to_ingredient(row) for row in rows]

    def get_ingredients_by_product(
        self, product_name: str, version: Optional[str] = None
    ) -> List[IngredientDTO]:
        """Отримати інгредієнти для продукту (з опціональною фільтрацією за версією)"""
        base_sql = (
            f"SELECT {self.IngredientColumns.ID}, {self.IngredientColumns.PRODUCT_NAME}, {self.IngredientColumns.VERSION}, {self.IngredientColumns.CHEMICAL_NAME}, {self.IngredientColumns.TRADE_MARK}, {self.IngredientColumns.CAS_NUMBER}, {self.IngredientColumns.CERTIFICATE} "
            f"FROM {self.Tables.INGREDIENTS} WHERE {self.IngredientColumns.PRODUCT_NAME} = ?"
        )
        rows = self._execute_query(
            f"{base_sql} ORDER BY {self.IngredientColumns.ID}",
            (product_name,),
        )
        ingredients = [self._row_to_ingredient(row) for row in rows]
        if version:
            normalized_version = normalize_version(version)
            ingredients = [
                ing
                for ing in ingredients
                if normalize_version(ing.version) == normalized_version
            ]
        return ingredients

    def get_ingredients_for_products(self, product_names: List[str]) -> List[IngredientDTO]:
        """Отримати інгредієнти для списку продуктів за один запит (пакетна вибірка)"""
        if not product_names:
            return []
        placeholders = ",".join("?" * len(product_names))
        rows = self._execute_query(
            f"SELECT {self.IngredientColumns.ID}, {self.IngredientColumns.PRODUCT_NAME}, {self.IngredientColumns.VERSION}, {self.IngredientColumns.CHEMICAL_NAME}, {self.IngredientColumns.TRADE_MARK}, {self.IngredientColumns.CAS_NUMBER}, {self.IngredientColumns.CERTIFICATE} "
            f"FROM {self.Tables.INGREDIENTS} WHERE {self.IngredientColumns.PRODUCT_NAME} IN ({placeholders}) ORDER BY {self.IngredientColumns.ID}",
            tuple(product_names),
        )
        return [self._row_to_ingredient(row) for row in rows]

    def get_unique_versions_for_product(self, product_name: str) -> List[str]:
        """Отримати унікальні версії складу для продукту з нормалізацією дублікатів (кирилиця/латиниця)"""
        rows = self._execute_query(
            f"SELECT DISTINCT {self.IngredientColumns.VERSION} FROM {self.Tables.INGREDIENTS} "
            f"WHERE LOWER(TRIM({self.IngredientColumns.PRODUCT_NAME})) = LOWER(?) AND {self.IngredientColumns.VERSION} IS NOT NULL AND {self.IngredientColumns.VERSION} != ''",
            (product_name.strip(),),
        )
        unique_versions = set()
        for row in rows:
            v = row[self.IngredientColumns.VERSION]
            normalized = normalize_version(v)
            if normalized:
                unique_versions.add(normalized)
        return sorted(list(unique_versions))

    # Аліас для сумісності
    get_available_versions = get_unique_versions_for_product

    def get_par_certificates(self, product_name: str, version: str = "") -> str:
        """Отримати список сертифікатів ПАР для продукту та версії (через кому)"""
        logger.info(
            f"🎯 dictionary_service.get_par_certificates: product={product_name}, version={version or 'EMPTY'}"
        )

        normalized_version = normalize_version(version) if version else ""
        logger.info(f"📌 Нормалізована версія: '{version}' → '{normalized_version}'")

        if normalized_version:
            logger.info(f"📌 Використовується фільтр по версії: '{normalized_version}'")
            # Отримуємо всі версії з БД та порівнюємо нормалізовані значення
            # Використовуємо LOWER для ігнорування регістру
            all_rows = self._execute_query(
                f"SELECT {self.IngredientColumns.VERSION}, {self.IngredientColumns.CERTIFICATE} FROM {self.Tables.INGREDIENTS} "
                f"WHERE LOWER(TRIM({self.IngredientColumns.PRODUCT_NAME})) = LOWER(?) "
                f"AND {self.IngredientColumns.CERTIFICATE} IS NOT NULL "
                f"AND {self.IngredientColumns.CERTIFICATE} != '' "
                f"ORDER BY {self.IngredientColumns.ID}",
                (product_name.strip(),),
            )
            # Фільтруємо по нормалізованій версії
            rows = [
                row
                for row in all_rows
                if normalize_version(row[self.IngredientColumns.VERSION]) == normalized_version
            ]
            certificates = list(
                {
                    row[self.IngredientColumns.CERTIFICATE]
                    for row in rows
                    if row[self.IngredientColumns.CERTIFICATE]
                }
            )
            logger.info(
                f"✅ Знайдено {len(certificates)} сертифікатів для версії '{normalized_version}': {certificates}"
            )
            return ", ".join(sorted(certificates)) if certificates else ""
        else:
            logger.warning(
                f"⚠️ Версія для '{product_name}' порожня — автоматичний вибір вимкнено, щоб уникнути змішування составів."
            )
            # Якщо версія не вказана, ми НЕ повертаємо всі сертифікати, 
            # бо це призводить до помилок (змішування А и В).
            return ""

    def add_ingredient(self, ingredient: IngredientDTO) -> int:
        """Додати інгредієнт"""
        result = self._execute_command(
            f"INSERT INTO {self.Tables.INGREDIENTS} "
            f"({self.IngredientColumns.PRODUCT_NAME}, {self.IngredientColumns.VERSION}, {self.IngredientColumns.CHEMICAL_NAME}, {self.IngredientColumns.TRADE_MARK}, {self.IngredientColumns.CAS_NUMBER}, {self.IngredientColumns.CERTIFICATE}) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                ingredient.product_name,
                ingredient.version,
                ingredient.chemical_name,
                ingredient.trade_mark,
                ingredient.cas_number,
                ingredient.certificate,
            ),
        )
        self.get_all_products.cache_clear()
        return result

    def update_ingredient(self, ingredient_id: int, ingredient: IngredientDTO) -> bool:
        """Оновити інгредієнт"""
        self._execute_command(
            f"UPDATE {self.Tables.INGREDIENTS} SET {self.IngredientColumns.PRODUCT_NAME}=?, {self.IngredientColumns.VERSION}=?, {self.IngredientColumns.CHEMICAL_NAME}=?, "
            f"{self.IngredientColumns.TRADE_MARK}=?, {self.IngredientColumns.CAS_NUMBER}=?, {self.IngredientColumns.CERTIFICATE}=? WHERE {self.IngredientColumns.ID}=?",
            (
                ingredient.product_name,
                ingredient.version,
                ingredient.chemical_name,
                ingredient.trade_mark,
                ingredient.cas_number,
                ingredient.certificate,
                ingredient_id,
            ),
        )
        self.get_all_products.cache_clear()
        return True

    def delete_ingredient(self, ingredient_id: int) -> bool:
        """Видалити інгредієнт"""
        self._execute_command(
            f"DELETE FROM {self.Tables.INGREDIENTS} WHERE {self.IngredientColumns.ID}=?",
            (ingredient_id,),
        )
        self.get_all_products.cache_clear()
        return True
