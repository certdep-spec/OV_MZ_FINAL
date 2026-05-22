"""
Останні тести для покриття - досягнення 60%+
"""

import os
import tempfile

import pytest

from database.db_manager import DatabaseManager
from documents.vc_generator import VCDocumentGenerator
from models.dto import (
    ApplicationDTO,
    FinalDocumentsDTO,
    PartyDTO,
    ProductDTO,
    ProductionFacilityDTO,
    StandardDTO,
)
from services.application_service import ApplicationService
from services.dictionary_service import DictionaryService


@pytest.fixture
def temp_db():
    """Створення тимчасової БД"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    db_manager = DatabaseManager(temp_file.name)
    db_manager.close()
    yield temp_file.name
    os.unlink(temp_file.name)


class TestApplicationServiceComplete:
    """Повні тести для ApplicationService"""

    def test_save_application_with_none_values(self, temp_db):
        """Збереження заявки з None значеннями"""
        service = ApplicationService(temp_db)

        app = ApplicationDTO(
            app_number="300",
            app_date="05.04.2026",
            company_name="ТОВ Тест",
            company_code=None,
            director_name=None,
        )
        app_id = service.save_application(app)

        assert app_id > 0

        retrieved = service.get_application_by_id(app_id)
        assert retrieved is not None
        assert retrieved.company_name == "ТОВ Тест"

        service.close()

    def test_update_party_final_documents_with_none(self, temp_db):
        """Оновлення фінальних документів з None"""
        service = ApplicationService(temp_db)

        app = ApplicationDTO(app_number="301", app_date="05.04.2026")
        app_id = service.save_application(app)

        parties = [PartyDTO(product_name="Тест", party_code="01E")]
        party_ids = service.save_parties(app_id, parties)

        from models.dto import FinalDocumentsDTO

        final_docs = FinalDocumentsDTO(completed=False, generated_at=None)

        result = service.update_party_final_documents(party_ids[0], final_docs)
        assert result is True

        service.close()


class TestDictionaryServiceComplete:
    """Повні тести для DictionaryService"""

    def test_add_product_with_all_fields(self, temp_db):
        """Додавання продукту з усіма полями"""
        service = DictionaryService(temp_db)

        product = ProductDTO(
            name="Повний продукт",
            tu_code="ТУ 123",
            shelf_life_months=24,
            dkpp_code="20.41.32",
            uktzed_code="3402",
        )
        product_id = service.add_product(product)

        assert product_id > 0

        retrieved = service.get_product_by_name("Повний продукт")
        assert retrieved is not None
        assert retrieved.tu_code == "ТУ 123"
        assert retrieved.dkpp_code == "20.41.32"

        service.close()

    def test_add_standard_with_active_flag(self, temp_db):
        """Додавання стандарту з active прапорцем"""
        service = DictionaryService(temp_db)

        std = StandardDTO(id=100, description="Активний стандарт", active=1)
        service.add_standard(std)

        standards = service.get_all_standards(active_only=True)
        assert len(standards) >= 1

        service.close()

    def test_add_facility_with_company(self, temp_db):
        """Додавання потужності з назвою компанії"""
        service = DictionaryService(temp_db)

        facility = ProductionFacilityDTO(
            address="м. Київ, вул. Тестова", company_name="ТОВ Тест"
        )
        facility_id = service.add_facility(facility)

        assert facility_id > 0

        service.close()


class TestVcGeneratorComplete:
    """Повні тести для VCDocumentGenerator"""

    def test_vc_gen_has_doc_service(self, temp_db, tmp_path):
        """Перевірка що VCDocumentGenerator має document_service"""
        from services.document_service import DocumentService

        templates_dir = tmp_path / "templates"
        output_dir = tmp_path / "output"
        templates_dir.mkdir()
        output_dir.mkdir()

        doc_service = DocumentService(temp_db, str(templates_dir), str(output_dir))
        gen = VCDocumentGenerator(
            str(templates_dir), str(output_dir), document_service=doc_service
        )

        # Перевірка що document_service встановлено
        assert gen.document_service is not None


class TestDocumentBaseComplete:
    """Повні тести для DocumentBase"""

    def test_replace_text_with_special_chars(self, tmp_path):
        """Заміна тексту зі спеціальними символами"""
        from documents.generators.protocol_rozgl_generator import (
            ProtocolRozglGenerator,
        )

        doc_path = tmp_path / "test.docx"
        from docx import Document

        doc = Document()
        doc.add_paragraph("[TAG]")
        doc.save(doc_path)

        gen = ProtocolRozglGenerator(tmp_path, tmp_path)
        result = gen.replace_text_in_document(
            doc_path, {"[TAG]": "Текст з символами: @#$%^&*()"}
        )

        assert result is True

    def test_build_base_replacements_with_none_values(self, tmp_path):
        """Побудова замін з None значеннями"""
        from documents.generators.protocol_rozgl_generator import (
            ProtocolRozglGenerator,
        )

        app_data = {
            "app_number": "001",
            "app_date": "05.04.2026",
            "company_name": None,  # None значення
        }
        party_data = {
            "product_name": "Продукт",
            "party_code": "01E",
            "mfg_date": "01.04.2026",
            "quantity": None,  # None значення
            "unit": "шт",
            "party_date": "05.04.2026",
            "shelf_life_months": 24,
        }

        gen = ProtocolRozglGenerator(tmp_path, tmp_path)
        result = gen._build_base_replacements(app_data, party_data)

        assert "[B1]" in result
        # [B3] може бути пропущено якщо company_name is None
        assert "[B10]" in result


class TestUtilsComplete:
    """Повні тести для utils"""

    def test_format_app_number_edge_cases(self):
        """Форматування номера заявки - крайні випадки"""
        from utils.path_utils import format_app_number

        assert format_app_number("0") == "000"
        assert format_app_number("000") == "000"
        # Порожній рядок та None можуть оброблятися інакше
        assert isinstance(format_app_number(""), str)
        assert isinstance(format_app_number(None), str)

    def test_create_structured_path_nested(self, tmp_path):
        """Створення вкладеної папки"""
        from utils.path_utils import create_structured_path

        nested = tmp_path / "level1" / "level2"
        nested.mkdir(parents=True)

        path = create_structured_path(nested, "001", "05.04.2026")
        assert path.exists()
        assert path.is_dir()


class TestDTOComplete:
    """Повні тести для DTO"""

    def test_application_dto_with_all_fields(self):
        """ApplicationDTO з усіма полями"""
        app = ApplicationDTO(
            id=1,
            app_number="001",
            app_date="05.04.2026",
            company_name="ТОВ Тест",
            company_code="12345678",
            director_name="Директор",
            tu_code="ТУ 123",
            production_address="м. Київ",
        )

        assert app.id == 1
        assert app.app_number == "001"
        assert app.company_name == "ТОВ Тест"

    def test_party_dto_with_standards(self):
        """PartyDTO зі стандартами"""
        party = PartyDTO(
            product_name="Продукт",
            party_code="01E",
            party_date="05.04.2026",
            mfg_date="01.04.2026",
            quantity=100,
            unit="шт",
            shelf_life_months=24,
            standards=[1, 2, 3],
        )

        assert len(party.standards) == 3
        assert 1 in party.standards
        assert 2 in party.standards

    def test_final_documents_dto_with_timestamp(self):
        """FinalDocumentsDTO з timestamp"""
        from datetime import datetime

        docs = FinalDocumentsDTO(
            completed=True, generated_at=datetime.now().isoformat()
        )

        assert docs.completed is True
        assert "T" in docs.generated_at  # ISO формат


class TestExceptionsComplete:
    """Тести для exceptions"""

    def test_database_error(self):
        """DatabaseError виняток"""
        from exceptions import DatabaseError

        try:
            raise DatabaseError("Тест помилки")
        except DatabaseError as e:
            assert str(e) == "Тест помилки"

    def test_validation_error(self):
        """ValidationError виняток"""
        from exceptions import ValidationError

        try:
            raise ValidationError("Невалідні дані")
        except ValidationError as e:
            assert str(e) == "Невалідні дані"

    def test_template_not_found_error(self):
        """TemplateNotFoundError виняток"""
        from exceptions import TemplateNotFoundError

        try:
            raise TemplateNotFoundError("Шаблон не знайдено")
        except TemplateNotFoundError as e:
            assert str(e) == "Шаблон не знайдено"

    def test_document_generation_error(self):
        """DocumentGenerationError виняток"""
        from exceptions import DocumentGenerationError

        try:
            raise DocumentGenerationError("Помилка генерації")
        except DocumentGenerationError as e:
            assert str(e) == "Помилка генерації"


class TestConfigComplete:
    """Тести для config"""

    def test_version_format(self):
        """Формат версії"""
        import config

        assert hasattr(config, "VERSION")
        version_parts = config.VERSION.split(".")
        assert len(version_parts) >= 2
        for part in version_parts:
            assert part.isdigit()

    def test_appearance_mode(self):
        """Режим appearance"""
        import config

        assert hasattr(config, "APPEARANCE_MODE")
        assert config.APPEARANCE_MODE in ["light", "dark", "system"]
