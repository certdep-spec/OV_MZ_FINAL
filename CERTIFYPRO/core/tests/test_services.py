"""
Unit-тести для сервісів
"""

import os
import tempfile
import unittest
from pathlib import Path

from models.dto import (
    ApplicationDTO,
    FinalDocumentsDTO,
    IngredientDTO,
    PartyDTO,
    ProductDTO,
    ProductionFacilityDTO,
    StandardDTO,
)
from services.application_service import ApplicationService
from services.dictionary_service import DictionaryService
from services.document_service import DocumentService


class TestDictionaryService(unittest.TestCase):
    """Тести для DictionaryService"""

    def setUp(self):
        """Створення тимчасової БД для тестів"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.service = DictionaryService(self.temp_db.name)
        self._init_test_db()

    def tearDown(self):
        """Видалення тимчасової БД"""
        self.service.close()
        os.unlink(self.temp_db.name)

    def _init_test_db(self):
        """Ініціалізація тестової БД"""
        with self.service._get_connection() as conn:
            cursor = conn.cursor()

            # Створення таблиць
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    tu_code TEXT,
                    shelf_life_months INTEGER DEFAULT 36,
                    dkpp_code TEXT DEFAULT '20.41.32-50.00',
                    uktzed_code TEXT DEFAULT '3402',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS standards (
                    id INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    active INTEGER DEFAULT 1
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS production_facilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    company_name TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    version TEXT,
                    chemical_name TEXT,
                    trade_mark TEXT,
                    cas_number TEXT,
                    certificate TEXT
                )
            """)

    def test_add_product(self):
        """Додавання продукту"""
        product = ProductDTO(name="Тестовий продукт", tu_code="ТУ 123", shelf_life_months=24)
        product_id = self.service.add_product(product)

        self.assertGreater(product_id, 0)

        # Перевірка отримання
        retrieved = self.service.get_product_by_name("Тестовий продукт")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Тестовий продукт")
        self.assertEqual(retrieved.tu_code, "ТУ 123")
        self.assertEqual(retrieved.shelf_life_months, 24)

    def test_get_all_products(self):
        """Отримання всіх продуктів"""
        self.service.add_product(ProductDTO(name="Продукт 1"))
        self.service.add_product(ProductDTO(name="Продукт 2"))
        self.service.add_product(ProductDTO(name="Продукт 3"))

        products = self.service.get_all_products()

        self.assertEqual(len(products), 3)
        names = [p.name for p in products]
        self.assertIn("Продукт 1", names)
        self.assertIn("Продукт 2", names)
        self.assertIn("Продукт 3", names)

    def test_update_product(self):
        """Оновлення продукту"""
        # Додавання
        product = ProductDTO(name="Старий продукт", tu_code="ТУ 1")
        self.service.add_product(product)

        # Оновлення
        updated = ProductDTO(name="Новий продукт", tu_code="ТУ 2", shelf_life_months=48)
        result = self.service.update_product("Старий продукт", updated)

        self.assertTrue(result)

        # Перевірка
        retrieved = self.service.get_product_by_name("Новий продукт")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.tu_code, "ТУ 2")
        self.assertEqual(retrieved.shelf_life_months, 48)

    def test_delete_product(self):
        """Видалення продукту"""
        product = ProductDTO(name="Продукт для видалення")
        self.service.add_product(product)

        # Видалення
        result = self.service.delete_product("Продукт для видалення")
        self.assertTrue(result)

        # Перевірка видалення
        retrieved = self.service.get_product_by_name("Продукт для видалення")
        self.assertIsNone(retrieved)

    def test_add_standard(self):
        """Додавання стандарту"""
        standard = StandardDTO(id=100, description="Тестовий стандарт")
        standard_id = self.service.add_standard(standard)

        self.assertEqual(standard_id, 100)

        retrieved = self.service.get_standard_by_id(100)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.description, "Тестовий стандарт")

    def test_get_all_standards(self):
        """Отримання всіх стандартів"""
        self.service.add_standard(StandardDTO(id=1, description="Стандарт 1"))
        self.service.add_standard(StandardDTO(id=2, description="Стандарт 2"))
        self.service.add_standard(StandardDTO(id=3, description="Стандарт 3", active=False))

        # Тільки активні
        standards = self.service.get_all_standards(active_only=True)
        self.assertEqual(len(standards), 2)

        # Всі
        all_standards = self.service.get_all_standards(active_only=False)
        self.assertEqual(len(all_standards), 3)

    def test_add_facility(self):
        """Додавання потужності"""
        facility = ProductionFacilityDTO(
            address="м. Київ, вул. Тестова, 1", company_name="ТОВ Тест"
        )
        facility_id = self.service.add_facility(facility)

        self.assertGreater(facility_id, 0)

        retrieved = self.service.get_facility_by_address("м. Київ, вул. Тестова, 1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.company_name, "ТОВ Тест")

    def test_add_ingredient(self):
        """Додавання інгредієнту"""
        ingredient = IngredientDTO(
            product_name="Продукт",
            version="A",
            chemical_name="Хімічна назва",
            trade_mark="ТМ Тест",
            cas_number="123-45-6",
            certificate="Сертифікат 1",
        )
        ing_id = self.service.add_ingredient(ingredient)

        self.assertGreater(ing_id, 0)

        ingredients = self.service.get_ingredients_by_product("Продукт")
        self.assertEqual(len(ingredients), 1)
        self.assertEqual(ingredients[0].chemical_name, "Хімічна назва")
        self.assertEqual(ingredients[0].version, "A")

    def test_get_ingredients_by_version(self):
        """Отримання інгредієнтів з фільтрацією за версією"""
        self.service.add_ingredient(
            IngredientDTO(
                product_name="Продукт",
                version="A",
                chemical_name="Інгредієнт 1",
            )
        )
        self.service.add_ingredient(
            IngredientDTO(
                product_name="Продукт",
                version="A",
                chemical_name="Інгредієнт 2",
            )
        )
        self.service.add_ingredient(
            IngredientDTO(
                product_name="Продукт",
                version="B",
                chemical_name="Інгредієнт 3",
            )
        )

        # Всі інгредієнти
        all_ings = self.service.get_ingredients_by_product("Продукт")
        self.assertEqual(len(all_ings), 3)

        # Тільки версія A
        version_a = self.service.get_ingredients_by_product("Продукт", version="A")
        self.assertEqual(len(version_a), 2)

    def test_get_unique_versions(self):
        """Отримання унікальних версій"""
        self.service.add_ingredient(IngredientDTO(product_name="Продукт", version="A"))
        self.service.add_ingredient(IngredientDTO(product_name="Продукт", version="B"))
        self.service.add_ingredient(IngredientDTO(product_name="Продукт", version="A"))  # Дубль

        versions = self.service.get_unique_versions_for_product("Продукт")
        self.assertEqual(versions, ["A", "B"])

    def test_cyrillic_latin_normalization(self):
        """Тест нормалізації кирилиці та латиниці для версій (В кирилична та B латинська)"""
        # Додаємо інгредієнти з версією "В" (кирилиця U+0412) та "B" (латиниця U+0042)
        self.service.add_ingredient(IngredientDTO(product_name="Продукт", version="В", chemical_name="Інгр 1"))
        self.service.add_ingredient(IngredientDTO(product_name="Продукт", version="B", chemical_name="Інгр 2"))

        # 1. Перевіряємо унікальні версії - має повернути тільки одну "B" (латинську)
        versions = self.service.get_unique_versions_for_product("Продукт")
        self.assertEqual(versions, ["B"])

        # 2. Отримання інгредієнтів за будь-яким варіантом написання "B/В" має повертати обидва інгредієнти
        ingredients_cyr = self.service.get_ingredients_by_product("Продукт", version="В")
        ingredients_lat = self.service.get_ingredients_by_product("Продукт", version="B")

        self.assertEqual(len(ingredients_cyr), 2)
        self.assertEqual(len(ingredients_lat), 2)


class TestApplicationService(unittest.TestCase):
    """Тести для ApplicationService"""

    def setUp(self):
        """Створення тимчасової БД для тестів"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.service = ApplicationService(self.temp_db.name)
        self._init_test_db()

    def tearDown(self):
        """Видалення тимчасової БД"""
        self.service.close()
        os.unlink(self.temp_db.name)

    def _init_test_db(self):
        """Ініціалізація тестової БД"""
        with self.service._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_number TEXT NOT NULL UNIQUE,
                    app_date TEXT NOT NULL,
                    company_name TEXT,
                    company_code TEXT,
                    company_address TEXT,
                    director_name TEXT,
                    tu_code TEXT,
                    production_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    party_number INTEGER,
                    product_name TEXT NOT NULL,
                    party_code TEXT,
                    party_date TEXT,
                    mfg_date TEXT,
                    quantity REAL,
                    unit TEXT DEFAULT 'шт',
                    standards_data TEXT,
                    protocol_number TEXT,
                    protocol_date TEXT,
                    cert_number TEXT,
                    cert_date TEXT,
                    shelf_life_months INTEGER DEFAULT 36,
                    dkpp_code TEXT DEFAULT '20.41.32-50.00',
                    uktzed_code TEXT DEFAULT '3402',
                    final_docs_completed INTEGER DEFAULT 0,
                    final_docs_generated_at TIMESTAMP,
                    version TEXT,
                    is_import INTEGER DEFAULT 0,
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
                )
            """)

    def test_save_application(self):
        """Збереження заявки"""
        app = ApplicationDTO(
            app_number="001",
            app_date="01.01.2026",
            company_name="ТОВ Тест",
            company_code="12345678",
            director_name="Директоров І.Б.",
        )
        app_id = self.service.save_application(app)

        self.assertGreater(app_id, 0)

        retrieved = self.service.get_application_by_number("001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.company_name, "ТОВ Тест")

    def test_update_existing_application(self):
        """Оновлення існуючої заявки"""
        # Створення
        app = ApplicationDTO(app_number="001", app_date="01.01.2026", company_name="ТОВ 1")
        self.service.save_application(app)

        # Оновлення
        app.company_name = "ТОВ 2"
        self.service.save_application(app)

        retrieved = self.service.get_application_by_number("001")
        self.assertEqual(retrieved.company_name, "ТОВ 2")

    def test_update_application_by_id_with_number_change(self):
        """Оновлення заявки за ID зі зміною номера"""
        # Створення
        app = ApplicationDTO(app_number="001", app_date="01.01.2026", company_name="ТОВ 1")
        app_id = self.service.save_application(app)
        app.id = app_id

        # Оновлення номера
        app.app_number = "002"
        self.service.save_application(app)

        # Перевірка: старий номер не повинен існувати (якщо ми оновили той самий рядок)
        # Примітка: В нашій реалізації UPDATE змінює номер рядка з даним ID.
        old_retrieved = self.service.get_application_by_number("001")
        self.assertIsNone(old_retrieved)

        new_retrieved = self.service.get_application_by_number("002")
        self.assertIsNotNone(new_retrieved)
        self.assertEqual(new_retrieved.id, app_id)

    def test_get_last_app_number(self):
        """Отримання останнього номера заявки"""
        self.service.save_application(ApplicationDTO(app_number="001", app_date="01.01.2026"))
        self.service.save_application(ApplicationDTO(app_number="002", app_date="02.01.2026"))
        self.service.save_application(ApplicationDTO(app_number="003", app_date="03.01.2026"))

        last_number = self.service.get_last_app_number()
        self.assertEqual(last_number, "003")

    def test_get_last_app_number_empty(self):
        """Отримання номера з порожньої БД"""
        last_number = self.service.get_last_app_number()
        self.assertEqual(last_number, "001")

    def test_save_and_get_parties(self):
        """Збереження та отримання партій"""
        # Створення заявки
        app = ApplicationDTO(app_number="001", app_date="01.01.2026")
        app_id = self.service.save_application(app)

        # Збереження партій
        parties = [
            PartyDTO(product_name="Продукт 1", party_code="01E", quantity=100),
            PartyDTO(
                product_name="Продукт 2",
                party_code="02E",
                quantity=200,
                standards=[1, 2],
            ),
        ]
        party_ids = self.service.save_parties(app_id, parties)

        self.assertEqual(len(party_ids), 2)

        # Отримання партій
        retrieved = self.service.get_parties_for_application(app_id)
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved[0].product_name, "Продукт 1")
        self.assertEqual(retrieved[1].standards, [1, 2])

    def test_delete_application_cascade(self):
        """Видалення заявки з партіями (cascade)"""
        app = ApplicationDTO(app_number="001", app_date="01.01.2026")
        app_id = self.service.save_application(app)

        parties = [PartyDTO(product_name="Продукт", party_code="01E")]
        self.service.save_parties(app_id, parties)

        # Видалення
        self.service.delete_application(app_id)

        # Перевірка
        retrieved = self.service.get_application_by_number("001")
        self.assertIsNone(retrieved)

        parties = self.service.get_parties_for_application(app_id)
        self.assertEqual(len(parties), 0)

    def test_update_party_final_documents(self):
        """Оновлення фінальних документів партії"""
        # Створення заявки та партії
        app = ApplicationDTO(app_number="001", app_date="01.01.2026")
        app_id = self.service.save_application(app)

        parties = [PartyDTO(product_name="Продукт", party_code="01E")]
        party_ids = self.service.save_parties(app_id, parties)
        party_id = party_ids[0]

        # Оновлення фінальних документів
        final_data = FinalDocumentsDTO(
            protocol_number="123",
            protocol_date="15.01.2026",
            cert_number="UA.123",
            cert_date="20.01.2026",
        )
        result = self.service.update_party_final_documents(party_id, final_data)

        self.assertTrue(result)

        # Отримання
        retrieved = self.service.get_party_final_documents(party_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.protocol_number, "123")
        self.assertEqual(retrieved.cert_number, "UA.123")
        self.assertTrue(retrieved.completed)


class TestDocumentService(unittest.TestCase):
    """Тести для DocumentService"""

    def setUp(self):
        """Створення тимчасових папок для тестів"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_dir = Path(self.temp_dir.name) / "templates"
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.template_dir.mkdir()
        self.output_dir.mkdir()

        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.service = DocumentService(
            self.temp_db.name, str(self.template_dir), str(self.output_dir)
        )
        self._init_test_db()

    def tearDown(self):
        """Видалення тимчасових файлів"""
        self.service.close()
        os.unlink(self.temp_db.name)
        self.temp_dir.cleanup()

    def _init_test_db(self):
        """Ініціалізація тестової БД"""
        with self.service._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS standards (
                    id INTEGER PRIMARY KEY,
                    description TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    version TEXT,
                    chemical_name TEXT,
                    trade_mark TEXT,
                    cas_number TEXT,
                    certificate TEXT
                )
            """)

    def test_create_structured_path(self):
        """Створення структурованої папки"""
        path = self.service.create_structured_path("001", "15.01.2026")

        expected = self.output_dir / "2026" / "01_Січень" / "Заявка_001"
        self.assertEqual(path, expected)
        self.assertTrue(path.exists())

    def test_get_standards_text(self):
        """Отримання текстів стандартів"""
        with self.service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO standards (id, description) VALUES (1, 'Стандарт 1')")
            cursor.execute("INSERT INTO standards (id, description) VALUES (2, 'Стандарт 2')")

        result = self.service.get_standards_text([1, 2, 3])

        self.assertEqual(result["STD1"], "Стандарт 1")
        self.assertEqual(result["STD2"], "Стандарт 2")
        self.assertEqual(result["STD3"], "")  # Не існує в БД
        self.assertEqual(result["STD_ALL"], "Стандарт 1, Стандарт 2")

    def test_get_available_versions(self):
        """Отримання доступних версій"""
        with self.service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ingredients (product_name, version) VALUES ('Продукт', 'A')"
            )
            cursor.execute(
                "INSERT INTO ingredients (product_name, version) VALUES ('Продукт', 'B')"
            )
            cursor.execute(
                "INSERT INTO ingredients (product_name, version) VALUES ('Продукт', 'A')"
            )  # Дубль

        versions = self.service.get_available_versions("Продукт")

        self.assertEqual(versions, ["A", "B"])


if __name__ == "__main__":
    unittest.main()
