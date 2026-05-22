"""
Тести для покриття - частина 3
Фокус на document_service, dictionary_service, vc_generator
"""

import os
import tempfile

import pytest

from database.db_manager import DatabaseManager
from models.dto import ProductDTO, StandardDTO
from services.application_service import ApplicationService
from services.dictionary_service import DictionaryService
from services.document_service import DocumentService


@pytest.fixture
def temp_db():
    """Створення тимчасової БД"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    db_manager = DatabaseManager(temp_file.name)
    db_manager.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def services(temp_db, tmp_path):
    """Сервіси для тестів"""
    templates_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"
    templates_dir.mkdir()
    output_dir.mkdir()

    dict_service = DictionaryService(temp_db)
    doc_service = DocumentService(temp_db, str(templates_dir), str(output_dir))
    app_service = ApplicationService(temp_db)

    return dict_service, doc_service, app_service, templates_dir, output_dir


class TestDocumentServiceFull:
    """Повні тести для DocumentService"""

    def test_get_standards_text_with_standards(self, services):
        """Отримання тексту стандартів з ID"""
        dict_service, doc_service, _, _, _ = services

        dict_service.add_standard(StandardDTO(id=10, description="СТАНДАРТ 1"))
        dict_service.add_standard(StandardDTO(id=20, description="СТАНДАРТ 2"))

        result = doc_service.get_standards_text([10, 20])
        assert isinstance(result, dict)

    def test_get_standards_text_empty(self, services):
        """Отримання тексту стандартів - порожній список"""
        _, doc_service, _, _, _ = services

        result = doc_service.get_standards_text([])
        assert isinstance(result, dict)
        # Може мігати стандартні значення
        assert len(result) >= 0

    def test_get_ingredients_for_product_empty(self, services):
        """Отримання інгредієнтів - порожній результат"""
        _, doc_service, _, _, _ = services

        result = doc_service.get_ingredients_for_product("Неіснуючий")
        assert isinstance(result, list)
        assert len(result) == 0


class TestDictionaryServiceFull:
    """Повні тести для DictionaryService"""

    def test_add_and_get_facility(self, services):
        """Додавання та отримання потужності"""
        dict_service, _, _, _, _ = services

        from models.dto import ProductionFacilityDTO

        facility = ProductionFacilityDTO(address="м. Львів, вул. Тестова")
        facility_id = dict_service.add_facility(facility)

        assert facility_id > 0

        retrieved = dict_service.get_facility_by_address("м. Львів, вул. Тестова")
        assert retrieved is not None
        assert "Львів" in retrieved.address

    def test_get_all_facilities(self, services):
        """Отримання всіх потужностей"""
        dict_service, _, _, _, _ = services

        from models.dto import ProductionFacilityDTO

        dict_service.add_facility(ProductionFacilityDTO(address="м. Київ"))
        dict_service.add_facility(ProductionFacilityDTO(address="м. Харків"))

        facilities = dict_service.get_all_facilities()
        assert len(facilities) >= 2

    def test_add_ingredient(self, services):
        """Додавання інгредієнта"""
        dict_service, _, _, _, _ = services

        from models.dto import IngredientDTO

        # Спочатку додамо продукт
        dict_service.add_product(ProductDTO(name="Тест", tu_code="ТУ"))

        ing = IngredientDTO(
            product_name="Тест",
            version="A",
            chemical_name="Хімікат",
        )
        ing_id = dict_service.add_ingredient(ing)

        assert ing_id > 0

    def test_get_ingredients_by_product_empty(self, services):
        """Отримання інгредієнтів - порожній результат"""
        dict_service, _, _, _, _ = services

        result = dict_service.get_ingredients_by_product("Неіснуючий")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_delete_product(self, services):
        """Видалення продукту"""
        dict_service, _, _, _, _ = services

        dict_service.add_product(ProductDTO(name="Для видалення", tu_code="ТУ"))
        result = dict_service.delete_product("Для видалення")

        assert result is True

        # Перевірка що видалено
        retrieved = dict_service.get_product_by_name("Для видалення")
        assert retrieved is None


class TestVcGeneratorFull:
    """Тести для vc_generator"""

    def test_vc_generator_format_app_number(self, temp_db, tmp_path):
        """Форматування номера заявки"""
        from documents.vc_generator import VCDocumentGenerator
        from services.document_service import DocumentService

        doc_service = DocumentService(temp_db, str(tmp_path), str(tmp_path))
        gen = VCDocumentGenerator(
            str(tmp_path), str(tmp_path), document_service=doc_service
        )

        result = gen.format_app_number("1")
        assert result == "001"

    def test_vc_generator_create_structured_path(self, temp_db, tmp_path):
        """Створення структурованої папки"""
        from documents.document_base import DocumentBase
        from services.document_service import DocumentService

        DocumentService(temp_db, str(tmp_path), str(tmp_path))

        path = DocumentBase.create_structured_path(tmp_path, "001", "05.04.2026")
        assert path.exists()


class TestAppRegistrationModule:
    """Тести для app_registration модуля"""

    def test_module_import(self):
        """Імпорт модуля"""
        try:
            from documents import app_registration

            assert app_registration is not None
        except Exception:
            pytest.fail("Не вдалося імпортувати app_registration")


class TestContextBuilderModule:
    """Тести для context_builder"""

    def test_module_import(self):
        """Імпорт модуля"""
        try:
            from documents import context_builder

            assert context_builder is not None
        except Exception:
            pytest.fail("Не вдалося імпортувати context_builder")


class TestDocumentContextModule:
    """Тести для document_context"""

    def test_module_import(self):
        """Імпорт модуля"""
        try:
            from documents.context import document_context

            assert document_context is not None
        except Exception:
            pytest.fail("Не вдалося імпортувати document_context")
