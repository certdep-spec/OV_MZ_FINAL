"""
Unit-тести для DTO моделей (pytest)
"""

import unittest

from models.dto import (
    ApplicationDTO,
    DocumentContextDTO,
    ImportStatsDTO,
    IngredientDTO,
    PartyDTO,
    ProductDTO,
)


class TestProductDTO:
    """Тести для ProductDTO"""

    def test_create_product_with_defaults(self):
        """Створення продукту з значеннями за замовчуванням"""
        product = ProductDTO(name="Тестовий продукт")

        assert product.name == "Тестовий продукт"
        assert product.tu_code == ""
        assert product.shelf_life_months == 36
        assert product.dkpp_code == "20.41.32-50.00"
        assert product.uktzed_code == "3402"
        assert product.id is None

    def test_create_product_with_values(self):
        """Створення продукту з конкретними значеннями"""
        product = ProductDTO(
            id=1,
            name="Продукт А",
            tu_code="ТУ 123-456",
            shelf_life_months=24,
            dkpp_code="10.51",
            uktzed_code="1234",
        )

        assert product.id == 1
        assert product.name == "Продукт А"
        assert product.tu_code == "ТУ 123-456"
        assert product.shelf_life_months == 24

    def test_product_equality(self):
        """Перевірка рівності продуктів"""
        product1 = ProductDTO(name="Продукт", tu_code="ТУ 1")
        product2 = ProductDTO(name="Продукт", tu_code="ТУ 1")
        product3 = ProductDTO(name="Продукт", tu_code="ТУ 2")

        assert product1 == product2
        assert product1 != product3


class TestApplicationDTO(unittest.TestCase):
    """Тести для ApplicationDTO"""

    def test_create_application_empty(self):
        """Створення порожньої заявки"""
        app = ApplicationDTO(app_number="001", app_date="01.01.2026")

        self.assertEqual(app.app_number, "001")
        self.assertEqual(app.app_date, "01.01.2026")
        self.assertEqual(app.company_name, "")
        self.assertEqual(app.parties, [])

    def test_create_application_with_parties(self):
        """Створення заявки з партіями"""
        parties = [
            PartyDTO(product_name="Продукт 1", party_code="01E"),
            PartyDTO(product_name="Продукт 2", party_code="02E"),
        ]
        app = ApplicationDTO(
            app_number="002",
            app_date="02.01.2026",
            company_name="ТОВ Тест",
            parties=parties,
        )

        self.assertEqual(len(app.parties), 2)
        self.assertEqual(app.parties[0].product_name, "Продукт 1")
        self.assertEqual(app.parties[1].product_name, "Продукт 2")


class TestPartyDTO(unittest.TestCase):
    """Тести для PartyDTO"""

    def test_create_party_with_defaults(self):
        """Створення партії з значеннями за замовчуванням"""
        party = PartyDTO(product_name="Продукт")

        self.assertEqual(party.product_name, "Продукт")
        self.assertEqual(party.party_code, "")
        self.assertEqual(party.quantity, 0.0)
        self.assertEqual(party.unit, "шт")
        self.assertEqual(party.standards, [])

    def test_create_party_with_standards(self):
        """Створення партії зі стандартами"""
        party = PartyDTO(product_name="Продукт", party_code="01E", standards=[1, 2, 3])

        self.assertEqual(party.standards, [1, 2, 3])


class TestImportStatsDTO(unittest.TestCase):
    """Тести для ImportStatsDTO"""

    def test_create_empty_stats(self):
        """Створення порожньої статистики"""
        stats = ImportStatsDTO()

        self.assertEqual(stats.products, 0)
        self.assertEqual(stats.standards, 0)
        self.assertEqual(stats.facilities, 0)
        self.assertEqual(stats.ingredients, 0)
        self.assertEqual(stats.errors, 0)

    def test_create_stats_with_values(self):
        """Створення статистики з значеннями"""
        stats = ImportStatsDTO(
            products=10, standards=5, facilities=2, ingredients=50, errors=1
        )

        self.assertEqual(stats.products, 10)
        self.assertEqual(stats.errors, 1)


class TestDocumentContextDTO(unittest.TestCase):
    """Тести для DocumentContextDTO"""

    def test_create_context(self):
        """Створення контексту документа"""
        app = ApplicationDTO(app_number="001", app_date="01.01.2026")
        parties = [PartyDTO(product_name="Продукт", party_code="01E")]

        context = DocumentContextDTO(application=app, parties=parties)

        self.assertEqual(context.application, app)
        self.assertEqual(len(context.parties), 1)
        self.assertEqual(context.products, {})
        self.assertEqual(context.standards_text, {})

    def test_get_ingredients_for_product(self):
        """Отримання інгредієнтів для продукту"""
        ingredients = [
            IngredientDTO(
                product_name="Продукт",
                chemical_name="Інгредієнт 1",
                version="A",
            ),
            IngredientDTO(
                product_name="Продукт",
                chemical_name="Інгредієнт 2",
                version="A",
            ),
            IngredientDTO(
                product_name="Продукт",
                chemical_name="Інгредієнт 3",
                version="B",
            ),
        ]

        context = DocumentContextDTO(
            application=ApplicationDTO(app_number="001", app_date="01.01.2026"),
            parties=[],
            products={"Продукт": ingredients},
        )

        # Без фільтрації за версією
        all_ings = context.get_ingredients_for_product("Продукт")
        self.assertEqual(len(all_ings), 3)

        # З фільтрацією за версією
        filtered_ings = context.get_ingredients_for_product("Продукт", version="A")
        self.assertEqual(len(filtered_ings), 2)

        # Тест кирилиця/латиниця міксу для версії (кирилична В vs латинська B)
        filtered_ings_b_latin = context.get_ingredients_for_product("Продукт", version="B")
        self.assertEqual(len(filtered_ings_b_latin), 1)
        self.assertEqual(filtered_ings_b_latin[0].chemical_name, "Інгредієнт 3")

        filtered_ings_b_cyrillic = context.get_ingredients_for_product("Продукт", version="В") # кирилична В
        self.assertEqual(len(filtered_ings_b_cyrillic), 1)
        self.assertEqual(filtered_ings_b_cyrillic[0].chemical_name, "Інгредієнт 3")


if __name__ == "__main__":
    unittest.main()
