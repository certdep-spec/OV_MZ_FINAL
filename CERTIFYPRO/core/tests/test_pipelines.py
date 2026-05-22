"""
Інтеграційні тести для documents/pipelines/
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from documents.pipelines.base_pipeline import BasePipeline
from documents.pipelines.final_pipeline import FinalPipeline
from documents.pipelines.vc_pipeline import VCPipeline

# ===== TEST FIXTURES =====


@pytest.fixture
def mock_context_builder():
    """Мок context_builder"""
    builder = MagicMock()
    builder.collect_all_standards.return_value = {"STD1": "ДСТУ 123"}
    builder.collect_party_standards.return_value = {"STD1": "ДСТУ 123"}
    builder.get_par_certificates.return_value = "Сертифікат 1, Сертифікат 2"
    builder.get_ingredients_with_version.return_value = []
    return builder


@pytest.fixture
def tmp_dirs():
    """Тимчасові директорії для шаблонів та виводу"""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "templates"
        output_dir = Path(temp_dir) / "output"
        template_dir.mkdir()
        output_dir.mkdir()
        yield template_dir, output_dir


# ===== BASE PIPELINE TESTS =====


class TestBasePipeline:
    """Тести для BasePipeline"""

    def test_concrete_subclass_required(self):
        """Абстрактний клас не можна інстанціювати напряму"""
        with pytest.raises(TypeError):
            BasePipeline("test")

    def test_get_file_date(self):
        """_get_file_date повертає дату у форматі YYYY-MM-DD"""
        from documents.pipelines.vc_pipeline import VCPipeline

        pipeline = VCPipeline.__new__(VCPipeline)
        BasePipeline.__init__(pipeline, "test")

        date_str = pipeline._get_file_date()
        assert len(date_str) == 10
        assert "-" in date_str

    def test_print_report_exists(self):
        """_print_report існує"""
        from documents.pipelines.vc_pipeline import VCPipeline

        pipeline = VCPipeline.__new__(VCPipeline)
        BasePipeline.__init__(pipeline, "test")

        assert hasattr(pipeline, "_print_report")


# ===== VC PIPELINE TESTS =====


class TestVCPipeline:
    """Тести для VCPipeline"""

    def test_vc_pipeline_init(self, tmp_dirs, mock_context_builder):
        """Ініціалізація VCPipeline"""
        template_dir, output_dir = tmp_dirs
        pipeline = VCPipeline(template_dir, output_dir, mock_context_builder)

        assert pipeline.name == "ВЦ документи"
        assert pipeline.context_builder is mock_context_builder
        assert pipeline.zayavka_gen is not None
        assert pipeline.protocol_rozgl_gen is not None
        assert pipeline.perelik_gen is not None
        assert pipeline.reshenya_gen is not None
        assert pipeline.akt_vidbir_gen is not None
        assert pipeline.akt_ident_gen is not None

    @patch("documents.generators.zayavka_generator.ZayavkaGenerator.generate")
    @patch(
        "documents.generators.protocol_rozgl_generator.ProtocolRozglGenerator.generate"
    )
    @patch("documents.generators.perelik_generator.PerelikGenerator.generate")
    @patch("documents.generators.reshenya_generator.ReshenyaGenerator.generate")
    @patch("documents.generators.akt_vidbir_generator.AktVidbirGenerator.generate")
    @patch("documents.generators.akt_ident_generator.AktIdentGenerator.generate")
    def test_vc_pipeline_execute(
        self,
        mock_ident,
        mock_vidbir,
        mock_reshenya,
        mock_perelik,
        mock_protocol,
        mock_zayavka,
        tmp_dirs,
        mock_context_builder,
    ):
        """Виконання VCPipeline"""
        template_dir, output_dir = tmp_dirs
        pipeline = VCPipeline(template_dir, output_dir, mock_context_builder)

        # Налаштування моків
        mock_zayavka.return_value = {"zayavka": 1, "dodatok": 1}
        mock_protocol.return_value = {"protocol": 1}
        mock_perelik.return_value = {"perelik": 1}
        mock_reshenya.return_value = {"reshennya": 1}
        mock_vidbir.return_value = {"akt_vidbir": 1}
        mock_ident.return_value = {"akt_ident": 1}

        app_data = {"app_number": "001", "app_date": "05.04.2026"}
        parties = [
            {"product_name": "Продукт 1", "standards": [1]},
            {"product_name": "Продукт 2", "standards": [2]},
        ]
        folder = output_dir / "test"
        folder.mkdir()

        results = pipeline.execute(app_data, parties, folder)

        # Перевірка результатів
        assert results["zayavka"] == 1
        assert results["dodatok"] == 1
        assert results["protocol"] == 1
        assert results["perelik"] == 2  # 2 партії
        assert results["reshennya"] == 2
        assert results["akt_vidbir"] == 2
        assert results["akt_ident"] == 2

        # Перевірка викликів
        mock_zayavka.assert_called_once()
        mock_protocol.assert_called_once()
        assert mock_perelik.call_count == 2
        assert mock_reshenya.call_count == 2
        assert mock_vidbir.call_count == 2
        assert mock_ident.call_count == 2


# ===== FINAL PIPELINE TESTS =====


class TestFinalPipeline:
    """Тести для FinalPipeline"""

    def test_final_pipeline_init(self, tmp_dirs, mock_context_builder):
        """Ініціалізація FinalPipeline"""
        template_dir, output_dir = tmp_dirs
        pipeline = FinalPipeline(template_dir, output_dir, mock_context_builder)

        assert pipeline.name == "Фінальні документи"
        assert pipeline.context_builder is mock_context_builder
        assert pipeline.sertifikat_gen is not None
        assert pipeline.deklaraciya_gen is not None
        assert pipeline.ugoda_gen is not None
        assert pipeline.reshenya_vidachu_gen is not None
        assert pipeline.protokol_analiz_gen is not None
        assert pipeline.vysnovok_gen is not None

    @patch("documents.generators.sertifikat_generator.SertifikatGenerator.generate")
    @patch("documents.generators.deklaraciya_generator.DeklaraciyaGenerator.generate")
    @patch("documents.generators.ugoda_generator.UgodaGenerator.generate")
    @patch(
        "documents.generators.reshenya_vidachu_generator.ReshenyaVidachuGenerator.generate"
    )
    @patch(
        "documents.generators.protokol_analiz_generator.ProtokolAnalizGenerator.generate"
    )
    @patch("documents.generators.vysnovok_generator.VysnovokGenerator.generate")
    def test_final_pipeline_execute(
        self,
        mock_vysnovok,
        mock_protokol,
        mock_reshenya,
        mock_ugoda,
        mock_deklaraciya,
        mock_sertifikat,
        tmp_dirs,
        mock_context_builder,
    ):
        """Виконання FinalPipeline"""
        template_dir, output_dir = tmp_dirs
        pipeline = FinalPipeline(template_dir, output_dir, mock_context_builder)

        # Налаштування моків
        mock_sertifikat.return_value = {"sertifikat": 1}
        mock_deklaraciya.return_value = {"deklaracija": 1}
        mock_ugoda.return_value = {"ugoda": 1}
        mock_reshenya.return_value = {"rishennya_vidachu": 1}
        mock_protokol.return_value = {"protokol_analiz": 1}
        mock_vysnovok.return_value = {"vysnovok": 1}

        app_data = {"app_number": "001", "app_date": "05.04.2026"}
        party_data = {
            "product_name": "Продукт 1",
            "party_code": "01E",
            "version": "A",
            "cert_number": "CERT-001",
        }
        folder = output_dir / "test"
        folder.mkdir()

        results = pipeline.execute(app_data, party_data, party_id=1, folder=folder)

        # Перевірка результатів
        assert results["sertifikat"] == 1
        assert results["deklaracija"] == 1
        assert results["ugoda"] == 1
        assert results["rishennya_vidachu"] == 1
        assert results["protokol_analiz"] == 1
        assert results["vysnovok"] == 1
        assert results["folder"] == str(folder)

        # Перевірка викликів
        mock_sertifikat.assert_called_once()
        mock_deklaraciya.assert_called_once()
        mock_ugoda.assert_called_once()
        mock_reshenya.assert_called_once()
        mock_protokol.assert_called_once()
        mock_vysnovok.assert_called_once()


# ===== BASE PIPELINE: _print_report =====


class TestBasePipelinePrintReport:
    """Тести для _print_report у BasePipeline"""

    def test_print_report_with_results(self, caplog):
        """Базовий _print_report виводить результати"""

        # Створюємо конкретний підклас тільки для тесту базового методу
        class _TestPipeline(BasePipeline):
            def execute(self, **kwargs):
                return {}

        pipeline = _TestPipeline("Тестовий пайплайн")

        with caplog.at_level("INFO"):
            pipeline._print_report(
                {"doc_a": 1, "doc_b": 2, "folder": "/ignore"},
                folder=Path("/tmp/docs"),
            )

        assert "Тестовий пайплайн" in caplog.text
        assert "doc_a" in caplog.text
        assert "doc_b" in caplog.text
        assert "3 документів" in caplog.text

    def test_print_report_empty(self, caplog):
        """_print_report з порожніми результатами"""

        class _TestPipeline(BasePipeline):
            def execute(self, **kwargs):
                return {}

        pipeline = _TestPipeline("Empty Pipeline")

        with caplog.at_level("INFO"):
            pipeline._print_report({})

        assert "0 документів" in caplog.text


# ===== VC GENERATOR INTEGRATION TESTS =====


class TestVCDocumentGeneratorIntegration:
    """Інтеграційні тести для VCDocumentGenerator"""

    @patch("documents.pipelines.vc_pipeline.VCPipeline.execute")
    def test_generate_vc_documents_delegates_to_pipeline(self, mock_execute, tmp_path):
        """generate_vc_documents делегує VCPipeline"""
        from documents.vc_generator import VCDocumentGenerator
        from services.document_service import DocumentService

        mock_execute.return_value = {"zayavka": 1, "protocol": 1}

        doc_service = DocumentService(":memory:", str(tmp_path), str(tmp_path))
        gen = VCDocumentGenerator(
            str(tmp_path), str(tmp_path), document_service=doc_service
        )

        app_data = {"app_number": "001", "app_date": "05.04.2026"}
        parties = [{"product_name": "Продукт 1", "standards": [1]}]

        result = gen.generate_vc_documents(app_data, parties)

        assert result == {"zayavka": 1, "protocol": 1}
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args.kwargs
        assert call_kwargs["app_data"] == app_data
        assert call_kwargs["parties"] == parties

    @patch("documents.pipelines.final_pipeline.FinalPipeline.execute")
    def test_generate_final_documents_for_party_delegates_to_pipeline(
        self, mock_execute, tmp_path
    ):
        """generate_final_documents_for_party делегує FinalPipeline"""
        from documents.vc_generator import VCDocumentGenerator
        from services.document_service import DocumentService

        mock_execute.return_value = {
            "sertifikat": 1,
            "deklaracija": 1,
            "folder": "",
        }

        doc_service = DocumentService(":memory:", str(tmp_path), str(tmp_path))
        gen = VCDocumentGenerator(
            str(tmp_path), str(tmp_path), document_service=doc_service
        )

        app_data = {"app_number": "001", "app_date": "05.04.2026"}
        party_data = {"product_name": "Продукт 1", "party_code": "01E"}

        result = gen.generate_final_documents_for_party(
            party_data, app_data, party_id=1
        )

        assert result["sertifikat"] == 1
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args.kwargs
        assert call_kwargs["party_data"] == party_data
        assert call_kwargs["app_data"] == app_data
        assert call_kwargs["party_id"] == 1

    def test_generate_final_documents_wrapper(self, tmp_path):
        """generate_final_documents — wrapper для зворотної сумісності"""
        from documents.vc_generator import VCDocumentGenerator
        from services.document_service import DocumentService

        doc_service = DocumentService(":memory:", str(tmp_path), str(tmp_path))
        gen = VCDocumentGenerator(
            str(tmp_path), str(tmp_path), document_service=doc_service
        )

        # Патчимо execute щоб уникнути реальної генерації
        with patch.object(
            gen.final_pipeline, "execute", return_value={"sertifikat": 1}
        ):
            result = gen.generate_final_documents(
                {"product_name": "X"},
                {"app_number": "1", "app_date": "01.01.2026"},
                1,
            )

        assert result["sertifikat"] == 1

    def test_generate_vc_documents_error_handling(self, tmp_path):
        """generate_vc_documents повертає нулі при помилці"""
        from documents.vc_generator import VCDocumentGenerator
        from services.document_service import DocumentService

        doc_service = DocumentService(":memory:", str(tmp_path), str(tmp_path))
        gen = VCDocumentGenerator(
            str(tmp_path), str(tmp_path), document_service=doc_service
        )

        # Викликаємо з некоректними даними — має повернути нулі
        result = gen.generate_vc_documents({}, [])

        assert result["zayavka"] == 0
        assert result["protocol"] == 0

    def test_generate_final_documents_error_handling(self, tmp_path):
        """generate_final_documents_for_party повертає нулі при помилці"""
        from documents.vc_generator import VCDocumentGenerator
        from services.document_service import DocumentService

        doc_service = DocumentService(":memory:", str(tmp_path), str(tmp_path))
        gen = VCDocumentGenerator(
            str(tmp_path), str(tmp_path), document_service=doc_service
        )

        result = gen.generate_final_documents_for_party({}, {}, 0)

        assert result["sertifikat"] == 0
        assert result["folder"] == ""
