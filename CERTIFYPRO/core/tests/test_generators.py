"""
Тести для генераторів документів
"""

from unittest.mock import patch

import pytest

from documents.generators.akt_ident_generator import AktIdentGenerator
from documents.generators.akt_vidbir_generator import AktVidbirGenerator
from documents.generators.deklaraciya_generator import DeklaraciyaGenerator
from documents.generators.perelik_generator import PerelikGenerator
from documents.generators.protocol_rozgl_generator import (
    ProtocolRozglGenerator,
)
from documents.generators.reshenya_generator import ReshenyaGenerator
from documents.generators.sertifikat_generator import SertifikatGenerator
from documents.generators.ugoda_generator import UgodaGenerator
from models.dto import ApplicationDTO, DocumentContextDTO, PartyDTO


@pytest.fixture
def sample_app_data():
    """Створення тестових даних заявки (dict формат)"""
    return {
        "app_number": "005",
        "app_date": "05.04.2026",
        "company_name": "ТОВ Тестова Компанія",
        "company_code": "12345678",
        "director_name": "Директоров І.Б.",
        "tu_code": "ТУ 123-456",
        "production_address": "м. Київ, вул. Тестова, 1",
    }


@pytest.fixture
def temp_dirs(tmp_path):
    """Тимчасові директорії"""
    templates_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"
    templates_dir.mkdir()
    output_dir.mkdir()
    return templates_dir, output_dir


def mock_all_generation_methods(mock_docxtpl, mock_copy):
    """Helper щоб замокати обидва методи генерації"""
    mock_docxtpl.return_value = True
    mock_copy.return_value = True


class TestProtocolRozglGenerator:
    """Тести для генератора протоколу розгляду"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = ProtocolRozglGenerator(templates_dir, output_dir)
        assert gen.get_template_name() == "3_Протокол_розгляду_бланк_Д.docx"

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = ProtocolRozglGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert "protocol" in result


class TestPerelikGenerator:
    """Тести для генератора переліку"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = PerelikGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name()
        assert isinstance(template_name, str)
        assert len(template_name) > 0

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = PerelikGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestReshenyaGenerator:
    """Тести для генератора рішення"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = ReshenyaGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name()
        assert isinstance(template_name, str)
        assert len(template_name) > 0

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = ReshenyaGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestAktVidbirGenerator:
    """Тести для генератора акту відбору"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = AktVidbirGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name()
        assert isinstance(template_name, str)
        assert len(template_name) > 0

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = AktVidbirGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestAktIdentGenerator:
    """Тести для генератора акту ідентифікації"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = AktIdentGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name()
        assert isinstance(template_name, str)
        assert len(template_name) > 0

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = AktIdentGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestSertifikatGenerator:
    """Тести для генератора сертифікату"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = SertifikatGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name()
        assert isinstance(template_name, str)
        assert len(template_name) > 0

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = SertifikatGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestDeklaraciyaGenerator:
    """Тести для генератора декларації"""

    def test_get_template_name(self, temp_dirs):
        """Перевірка імені шаблону"""
        templates_dir, output_dir = temp_dirs
        gen = DeklaraciyaGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name()
        assert isinstance(template_name, str)
        assert len(template_name) > 0

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = DeklaraciyaGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestUgodaGenerator:
    """Тести для генератора угоди"""

    def test_get_template_name_standard(self, temp_dirs):
        """Перевірка імені шаблону для вітчизняної продукції"""
        templates_dir, output_dir = temp_dirs
        gen = UgodaGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name(is_import=False)
        assert template_name == "12_Угода_бланк_Д.docx"

    def test_get_template_name_import(self, temp_dirs):
        """Перевірка імені шаблону для імпортної продукції"""
        templates_dir, output_dir = temp_dirs
        gen = UgodaGenerator(templates_dir, output_dir)
        template_name = gen.get_template_name(is_import=True)
        assert template_name == "12_Угода_бланк_імпорт_Д.docx"

    def test_detect_import_type_same_company(self, temp_dirs):
        """Перевірка: Заявитель == Виробник → вітчизняна"""
        templates_dir, output_dir = temp_dirs
        gen = UgodaGenerator(templates_dir, output_dir)

        # Мокаємо DictionaryService
        from unittest.mock import patch

        from models.dto import ProductionFacilityDTO

        with patch(
            "services.dictionary_service.DictionaryService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_facility_by_address.return_value = ProductionFacilityDTO(
                id=1,
                address="вул. Тестова, 1",
                company_name="ТОВ «ДЖОНСОН»",
            )

            app_data = {
                "company_name": "ТОВ «ДЖОНСОН»",
                "production_address": "вул. Тестова, 1",
            }
            party_data = {"product_name": "Продукт"}

            # Заявитель == Виробник → вітчизняна
            assert gen._detect_import_type(app_data, party_data) is False

    def test_detect_import_type_different_company(self, temp_dirs):
        """Перевірка: Заявитель != Виробник → імпортна"""
        templates_dir, output_dir = temp_dirs
        gen = UgodaGenerator(templates_dir, output_dir)

        from unittest.mock import patch

        from models.dto import ProductionFacilityDTO

        with patch(
            "services.dictionary_service.DictionaryService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_facility_by_address.return_value = ProductionFacilityDTO(
                id=1,
                address="вул. Іноземна, 100",
                company_name="Foreign Corp",
            )

            app_data = {
                "company_name": "ТОВ «ДЖОНСОН»",
                "production_address": "вул. Іноземна, 100",
            }
            party_data = {"product_name": "Продукт"}

            # Заявитель != Виробник → імпортна
            assert gen._detect_import_type(app_data, party_data) is True

    @patch("documents.document_base.DocumentBase.generate_with_copy_and_replace")
    @patch("documents.document_base.DocumentBase.generate_with_docxtpl")
    def test_generate_success(
        self, mock_docxtpl, mock_copy, sample_app_data, temp_dirs
    ):
        """Тест успішної генерації"""
        mock_docxtpl.return_value = True
        mock_copy.return_value = True
        templates_dir, output_dir = temp_dirs

        gen = UgodaGenerator(templates_dir, output_dir)
        result = gen.generate(sample_app_data)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestDocumentContextDTO:
    """Тести для DocumentContextDTO"""

    def test_context_creation(self):
        """Створення контексту"""
        app = ApplicationDTO(
            app_number="001",
            app_date="05.04.2026",
            company_name="ТОВ Тест",
        )
        parties = [
            PartyDTO(product_name="Продукт", party_code="01E"),
        ]
        context = DocumentContextDTO(
            application=app,
            parties=parties,
            standards_text={"[X]": "test"},
        )

        assert context.application.app_number == "001"
        assert len(context.parties) == 1
        assert "[X]" in context.standards_text

    def test_context_with_multiple_parties(self):
        """Контекст з кількома партіями"""
        app = ApplicationDTO(app_number="002", app_date="05.04.2026")
        parties = [
            PartyDTO(product_name="Продукт 1", party_code="01E"),
            PartyDTO(product_name="Продукт 2", party_code="02E"),
            PartyDTO(product_name="Продукт 3", party_code="03E"),
        ]
        context = DocumentContextDTO(application=app, parties=parties)

        assert len(context.parties) == 3
        assert context.parties[0].product_name == "Продукт 1"
        assert context.parties[2].party_code == "03E"
