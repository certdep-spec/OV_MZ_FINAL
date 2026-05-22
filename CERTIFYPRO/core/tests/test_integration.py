"""
Інтеграційні тести для CertifyPro
Тестування повного потоку: створення заявки → збереження → генерація документів
"""

import os
import tempfile

import pytest

from database.db_manager import DatabaseManager
from models.dto import (
    ApplicationDTO,
    PartyDTO,
    ProductDTO,
    StandardDTO,
)
from services.application_service import ApplicationService
from services.dictionary_service import DictionaryService
from services.document_service import DocumentService


@pytest.fixture
def temp_db():
    """Створення тимчасової БД з ініціалізованими таблицями"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()

    # Ініціалізація БД через DatabaseManager
    db_manager = DatabaseManager(temp_file.name)
    db_manager.close()

    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def temp_dirs(tmp_path):
    """Створення тимчасових директорій для шаблонів та документів"""
    templates_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"
    templates_dir.mkdir()
    output_dir.mkdir()
    return templates_dir, output_dir


@pytest.fixture
def services(temp_db, temp_dirs):
    """Створення всіх сервісів для тестів"""
    templates_dir, output_dir = temp_dirs

    app_service = ApplicationService(temp_db)
    dict_service = DictionaryService(temp_db)
    doc_service = DocumentService(temp_db, str(templates_dir), str(output_dir))

    return app_service, dict_service, doc_service


class TestApplicationFlow:
    """Тести повного потоку роботи з заявками"""

    def test_create_and_retrieve_application(self, services):
        """Створення заявки та її отримання"""
        app_service, _, _ = services

        # Створення заявки
        app = ApplicationDTO(
            app_number="001",
            app_date="05.04.2026",
            company_name="ТОВ Тестова Компанія",
            company_code="12345678",
            director_name="Директоров І.Б.",
            tu_code="ТУ 123-456",
        )
        app_id = app_service.save_application(app)

        assert app_id > 0

        # Отримання заявки
        retrieved = app_service.get_application_by_id(app_id)
        assert retrieved is not None
        assert retrieved.company_name == "ТОВ Тестова Компанія"
        assert retrieved.app_number == "001"

    def test_create_application_with_parties(self, services):
        """Створення заявки з партіями"""
        app_service, _, _ = services

        # Створення заявки
        app = ApplicationDTO(
            app_number="002",
            app_date="05.04.2026",
            company_name="ТОВ З Партіями",
        )
        app_id = app_service.save_application(app)

        # Додавання партій
        parties = [
            PartyDTO(
                product_name="Продукт 1",
                party_code="01E",
                party_date="05.04.2026",
                quantity=100,
                unit="шт",
            ),
            PartyDTO(
                product_name="Продукт 2",
                party_code="02E",
                party_date="05.04.2026",
                quantity=200,
                unit="кг",
                standards=[1, 2],
            ),
        ]
        party_ids = app_service.save_parties(app_id, parties)

        assert len(party_ids) == 2

        # Отримання партій
        retrieved_parties = app_service.get_parties_for_application(app_id)
        assert len(retrieved_parties) == 2
        assert retrieved_parties[0].product_name == "Продукт 1"
        assert retrieved_parties[1].standards == [1, 2]

    def test_delete_application_cascade(self, services):
        """Видалення заявки з партіями (cascade)"""
        app_service, _, _ = services

        # Створення заявки з партіями
        app = ApplicationDTO(app_number="003", app_date="05.04.2026")
        app_id = app_service.save_application(app)

        parties = [
            PartyDTO(product_name="Продукт", party_code="01E"),
            PartyDTO(product_name="Продукт 2", party_code="02E"),
        ]
        app_service.save_parties(app_id, parties)

        # Видалення
        app_service.delete_application(app_id)

        # Перевірка що партії теж видалено
        retrieved_parties = app_service.get_parties_for_application(app_id)
        assert len(retrieved_parties) == 0

        # Перевірка що заявку видалено
        retrieved_app = app_service.get_application_by_id(app_id)
        assert retrieved_app is None


class TestDictionaryFlow:
    """Тести потоку роботи з довідниками"""

    def test_add_and_retrieve_products(self, services):
        """Додавання та отримання продуктів"""
        _, dict_service, _ = services

        # Додавання продуктів
        dict_service.add_product(ProductDTO(name="Шампунь", tu_code="ТУ 1"))
        dict_service.add_product(ProductDTO(name="Гель", tu_code="ТУ 2"))
        dict_service.add_product(ProductDTO(name="Крем", tu_code="ТУ 3"))

        # Отримання
        products = dict_service.get_all_products()
        assert len(products) == 3

        names = [p.name for p in products]
        assert "Шампунь" in names
        assert "Гель" in names
        assert "Крем" in names

    def test_add_and_retrieve_standards(self, services):
        """Додавання та отримання стандартів"""
        _, dict_service, _ = services

        # Додавання стандартів
        dict_service.add_standard(StandardDTO(id=1, description="ДСТУ ISO 9001"))
        dict_service.add_standard(StandardDTO(id=2, description="ДСТУ ISO 14001"))

        # Отримання
        standards = dict_service.get_all_standards()
        assert len(standards) == 2

        descriptions = [s.description for s in standards]
        assert "ДСТУ ISO 9001" in descriptions
        assert "ДСТУ ISO 14001" in descriptions

    def test_product_with_ingredients(self, services):
        """Продукт зі складом"""
        _, dict_service, _ = services

        # Додавання продукту
        dict_service.add_product(ProductDTO(name="Шампунь", tu_code="ТУ 1"))

        # Отримання продукту для перевірки ID
        product = dict_service.get_product_by_name("Шампунь")
        assert product is not None


class TestDocumentServiceIntegration:
    """Тести DocumentService"""

    def test_create_structured_path(self, services, tmp_path):
        """Створення структурованої папки"""
        _, _, doc_service = services

        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)

        # Створення папки
        from documents.document_base import DocumentBase

        path = DocumentBase.create_structured_path(output_dir, "001", "05.04.2026")

        assert path.exists()
        assert path.is_dir()
        assert "05.04.2026" in str(path)
        assert "001" in str(path)

    def test_format_app_number(self):
        """Форматування номера заявки"""
        from documents.document_base import DocumentBase

        assert DocumentBase.format_app_number("1") == "001"
        assert DocumentBase.format_app_number("12") == "012"
        assert DocumentBase.format_app_number("123") == "123"
        assert DocumentBase.format_app_number("abc") == "abc"


class TestFullWorkflow:
    """Повний інтеграційний тест всього потоку"""

    def test_full_application_workflow(self, services):
        """
        Повний тест:
        1. Додавання продуктів та стандартів
        2. Створення заявки
        3. Додавання партій
        4. Отримання повної заявки
        5. Перевірка цілісності даних
        """
        app_service, dict_service, doc_service = services

        # 1. Додавання довідників
        dict_service.add_product(ProductDTO(name="Шампунь", tu_code="ТУ 1"))
        dict_service.add_product(ProductDTO(name="Гель", tu_code="ТУ 2"))
        dict_service.add_standard(StandardDTO(id=1, description="ДСТУ ISO 9001"))
        dict_service.add_standard(StandardDTO(id=2, description="ДСТУ ISO 14001"))

        # 2. Створення заявки
        app = ApplicationDTO(
            app_number="010",
            app_date="05.04.2026",
            company_name="ТОВ Інтеграційний Тест",
            company_code="87654321",
            director_name="Тестовий І.Б.",
            tu_code="ТУ 1",
        )
        app_id = app_service.save_application(app)
        assert app_id > 0

        # 3. Додавання партій
        parties = [
            PartyDTO(
                product_name="Шампунь",
                party_code="01E",
                party_date="05.04.2026",
                quantity=1000,
                unit="шт",
                standards=[1],
            ),
            PartyDTO(
                product_name="Гель",
                party_code="02E",
                party_date="05.04.2026",
                quantity=500,
                unit="кг",
                standards=[1, 2],
            ),
        ]
        party_ids = app_service.save_parties(app_id, parties)
        assert len(party_ids) == 2

        # 4. Отримання повної заявки
        retrieved_app = app_service.get_application_by_id(app_id)
        assert retrieved_app is not None
        assert retrieved_app.app_number == "010"
        assert retrieved_app.company_name == "ТОВ Інтеграційний Тест"

        retrieved_parties = app_service.get_parties_for_application(app_id)
        assert len(retrieved_parties) == 2
        assert retrieved_parties[0].product_name == "Шампунь"
        assert retrieved_parties[1].product_name == "Гель"

        # 5. Перевірка цілісності
        all_apps = app_service.get_all_applications()
        assert len(all_apps) >= 1

        # 6. Створення папки для документів
        doc_path = doc_service.create_structured_path(
            retrieved_app.app_number, retrieved_app.app_date
        )
        assert doc_path.exists()
        assert doc_path.is_dir()
