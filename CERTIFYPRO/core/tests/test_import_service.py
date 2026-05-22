"""
Тести для ImportService
"""

import os
import tempfile

import pandas as pd
import pytest

from database.db_manager import DatabaseManager
from services.dictionary_service import DictionaryService
from services.import_service import ImportService


@pytest.fixture
def temp_db():
    """Створення тимчасової БД з ініціалізованими таблицями"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    db_manager = DatabaseManager(temp_file.name)
    db_manager.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def import_service(temp_db):
    """Створення ImportService для тестів"""
    return ImportService(temp_db)


@pytest.fixture
def dict_service(temp_db):
    """Створення DictionaryService для перевірки результатів"""
    return DictionaryService(temp_db)


@pytest.fixture
def sample_excel(tmp_path):
    """Створення тестового Excel файлу"""
    excel_path = tmp_path / "test_import.xlsx"

    # Аркуш Продукції
    df_products = pd.DataFrame(
        {
            0: ["Шампунь", "Гель", "Крем"],
            1: ["ТУ 123", "ТУ 456", "ТУ 789"],
            2: [24, 36, 12],
        }
    )

    # Аркуш Стандарти
    df_standards = pd.DataFrame(
        {0: [1, 2, 3], 1: ["ДСТУ ISO 9001", "ДСТУ ISO 14001", "ДСТУ 123"]}
    )

    # Аркуш Потужності
    df_facilities = pd.DataFrame(
        {0: ["м. Київ, вул. Тестова, 1", "м. Львів, вул. Тестова, 2"]}
    )

    # Аркуш Склад
    df_ingredients = pd.DataFrame(
        {
            0: ["Шампунь", "Шампунь", "Гель"],
            1: ["A", "A", "A"],
            2: ["Вода дистильована", "ПАР", "Гелеутворювач"],
            3: ["", "ТМ Тест", ""],
            4: ["7732-18-5", "", ""],
            5: ["", "Сертифікат 1", ""],
        }
    )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_products.to_excel(
            writer, sheet_name="ДОВІДНИК_ПРОДУКЦІЯ", index=False, header=False
        )
        df_standards.to_excel(writer, sheet_name="НД", index=False, header=False)
        df_facilities.to_excel(
            writer, sheet_name="ДОВІДНИК_ПОТУЖНОСТІ", index=False, header=False
        )
        df_ingredients.to_excel(
            writer, sheet_name="ДОВІДНИК_СКЛАД", index=False, header=False
        )

    return str(excel_path)


class TestImportService:
    """Тести для ImportService"""

    def test_import_from_excel(self, import_service, dict_service, sample_excel):
        """Повний імпорт з Excel"""
        stats = import_service.import_from_excel(sample_excel)

        assert stats["products"] == 3
        assert stats["standards"] == 3
        assert stats["facilities"] == 2
        assert stats["ingredients"] == 3
        assert stats["errors"] == 0

        # Перевірка що дані дійсно додано
        products = dict_service.get_all_products()
        assert len(products) == 3

        standards = dict_service.get_all_standards()
        assert len(standards) == 3

        facilities = dict_service.get_all_facilities()
        assert len(facilities) == 2

    def test_import_file_not_found(self, import_service):
        """Імпорт неіснуючого файлу"""
        with pytest.raises(Exception):
            import_service.import_from_excel("/nonexistent/file.xlsx")

    def test_import_partial(self, import_service, dict_service, tmp_path):
        """Імпорт з неповним Excel (тільки деякі аркуші)"""
        excel_path = tmp_path / "partial.xlsx"

        # Тільки аркуш Продукції
        df_products = pd.DataFrame({0: ["Тестовий продукт"], 1: ["ТУ 000"], 2: [36]})

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_products.to_excel(
                writer,
                sheet_name="ДОВІДНИК_ПРОДУКЦІЯ",
                index=False,
                header=False,
            )

        stats = import_service.import_from_excel(str(excel_path))

        assert stats["products"] == 1
        assert stats["standards"] == 0
        assert stats["facilities"] == 0
        assert stats["ingredients"] == 0

    def test_import_clears_old_data(self, import_service, dict_service, tmp_path):
        """Імпорт повинен очищати старі дані"""
        # Створюємо Excel з продуктами
        excel1 = tmp_path / "first.xlsx"
        df_products = pd.DataFrame(
            {0: ["Продукт 1", "Продукт 2"], 1: ["ТУ 1", "ТУ 2"], 2: [24, 36]}
        )
        with pd.ExcelWriter(excel1, engine="openpyxl") as writer:
            df_products.to_excel(
                writer,
                sheet_name="ДОВІДНИК_ПРОДУКЦІЯ",
                index=False,
                header=False,
            )

        # Спочатку імпортимо
        import_service.import_from_excel(str(excel1))

        # Перевіряємо що дані є
        products_before = dict_service.get_all_products()
        assert len(products_before) == 2

        # Створюємо новий Excel з менше даних
        excel2 = tmp_path / "new.xlsx"
        df_products = pd.DataFrame({0: ["Новий продукт"], 1: ["ТУ 999"], 2: [24]})

        with pd.ExcelWriter(excel2, engine="openpyxl") as writer:
            df_products.to_excel(
                writer,
                sheet_name="ДОВІДНИК_ПРОДУКЦІЯ",
                index=False,
                header=False,
            )

        # Імпортимо знову (має очистити і додати нові)
        import_service.import_from_excel(str(excel2))

        # Перевіряємо що тепер тільки один продукт
        products_after = dict_service.get_all_products()
        assert len(products_after) == 1
        assert products_after[0].name == "Новий продукт"

    def test_import_products_data_validation(
        self, import_service, dict_service, tmp_path
    ):
        """Перевірка валідації даних продукції"""
        excel_path = tmp_path / "validation.xlsx"

        # Дані з порожніми/невалідними рядками
        df_products = pd.DataFrame(
            {
                0: ["", "nan", "Валідний продукт", "Valid2"],
                1: ["ТУ 1", "ТУ 2", "", "ТУ 4"],
                2: [24, None, 36, 48],
            }
        )

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_products.to_excel(
                writer,
                sheet_name="ДОВІДНИК_ПРОДУКЦІЯ",
                index=False,
                header=False,
            )

        stats = import_service.import_from_excel(str(excel_path))

        # Має імпортувати тільки валідні рядки
        assert stats["products"] == 2

        products = dict_service.get_all_products()
        names = [p.name for p in products]
        assert "Валідний продукт" in names
        assert "Valid2" in names

    def test_import_client_mismatch(self, import_service, tmp_path, monkeypatch):
        """Перевірка помилки при невідповідності клієнта"""
        excel_path = tmp_path / "wrong_client.xlsx"

        # Створюємо Excel з ID іншого клієнта
        df_app = pd.DataFrame([[""] * 5] * 10)
        df_app.iloc[7, 1] = "other_client"  # CLIENT_ID_ROW=7, CLIENT_ID_COL=1

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_app.to_excel(writer, sheet_name="ЗАЯВКА", index=False, header=False)

        # Мокаємо get_client_config щоб він повертав 'current_client'
        class MockConfig:
            client_id = "current_client"

        import services.import_service as isrv

        monkeypatch.setattr(isrv, "CONFIG_AVAILABLE", True)
        monkeypatch.setattr(isrv, "get_client_config", lambda: MockConfig())

        # Очікуємо DataImportError
        from exceptions import DataImportError

        with pytest.raises(DataImportError) as exc_info:
            import_service.import_from_excel(str(excel_path))

        assert "Невідповідність клієнта" in str(exc_info.value)


class TestImportServiceIntegration:
    """Інтеграційні тести для ImportService"""

    def test_full_workflow(self, import_service, dict_service, sample_excel):
        """Повний потік: імпорт → перевірка → оновлення"""
        # Імпорт
        stats = import_service.import_from_excel(sample_excel)

        assert stats["products"] > 0

        # Перевірка продуктів
        products = dict_service.get_all_products()
        assert len(products) == 3

        # Перевірка конкретних продуктів
        shampoo = dict_service.get_product_by_name("Шампунь")
        assert shampoo is not None
        assert shampoo.tu_code == "ТУ 123"
        assert shampoo.shelf_life_months == 24

        # Перевірка стандартів
        standards = dict_service.get_all_standards()
        std_descriptions = [s.description for s in standards]
        assert "ДСТУ ISO 9001" in std_descriptions

        # Перевірка інгредієнтів
        ingredients = dict_service.get_ingredients_by_product("Шампунь")
        assert len(ingredients) == 2
