"""
Тести для documents/registry.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from documents.registry import GeneratorRegistry, create_default_registry

# ===== FIXTURES =====


@pytest.fixture
def tmp_dirs():
    """Тимчасові директорії для шаблонів та виводу"""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "templates"
        output_dir = Path(temp_dir) / "output"
        template_dir.mkdir()
        output_dir.mkdir()
        yield template_dir, output_dir


@pytest.fixture
def mock_context_builder():
    """Мок context_builder"""
    builder = MagicMock()
    builder.collect_all_standards.return_value = {}
    builder.collect_party_standards.return_value = {}
    builder.get_par_certificates.return_value = ""
    builder.get_ingredients_with_version.return_value = []
    return builder


# ===== TESTS: GeneratorRegistry =====


class TestGeneratorRegistry:
    """Тести для GeneratorRegistry"""

    def test_register_and_create(self):
        """Реєстрація та створення генератора"""
        registry = GeneratorRegistry()
        mock_factory = MagicMock(return_value="my_generator")

        registry.register("test_gen", mock_factory)
        result = registry.create("test_gen", arg1=1)

        assert result == "my_generator"
        mock_factory.assert_called_once_with(arg1=1)

    def test_has(self):
        """Перевірка наявності генератора"""
        registry = GeneratorRegistry()
        registry.register("gen1", MagicMock())

        assert registry.has("gen1") is True
        assert registry.has("gen2") is False

    def test_list_names(self):
        """Список зареєстрованих імен"""
        registry = GeneratorRegistry()
        registry.register("a", MagicMock())
        registry.register("b", MagicMock())
        registry.register("c", MagicMock())

        names = registry.list_names()
        assert len(names) == 3
        assert set(names) == {"a", "b", "c"}

    def test_count(self):
        """Кількість генераторів"""
        registry = GeneratorRegistry()
        assert registry.count() == 0

        registry.register("a", MagicMock())
        assert registry.count() == 1

        registry.register("b", MagicMock())
        assert registry.count() == 2

    def test_unregister(self):
        """Видалення генератора"""
        registry = GeneratorRegistry()
        registry.register("gen1", MagicMock())
        assert registry.has("gen1") is True

        registry.unregister("gen1")
        assert registry.has("gen1") is False

    def test_unregister_nonexistent(self):
        """Видалення неіснуючого генератора — не викидає помилку"""
        registry = GeneratorRegistry()
        registry.unregister("nonexistent")  # не повинно викинути
        assert registry.count() == 0

    def test_create_unregistered_raises_keyerror(self):
        """Створення незареєстрованого генератора викидає KeyError"""
        registry = GeneratorRegistry()

        with pytest.raises(KeyError) as exc_info:
            registry.create("nonexistent")

        assert "не зареєстровано" in str(exc_info.value)

    def test_register_duplicate_warns(self, caplog):
        """Реєстрація дублікату логує попередження"""
        registry = GeneratorRegistry()
        factory1 = MagicMock()
        factory2 = MagicMock()

        with caplog.at_level("WARNING"):
            registry.register("gen", factory1)
            registry.register("gen", factory2)

        assert "вже зареєстровано" in caplog.text

    def test_create_passes_args_and_kwargs(self):
        """Аргументи передаються у фабрику"""
        registry = GeneratorRegistry()
        mock_factory = MagicMock(return_value="result")

        registry.register("gen", mock_factory)
        result = registry.create("gen", "pos1", "pos2", key1="val1")

        assert result == "result"
        mock_factory.assert_called_once_with("pos1", "pos2", key1="val1")


# ===== TESTS: create_default_registry =====


class TestCreateDefaultRegistry:
    """Тести для create_default_registry"""

    def test_creates_all_generators(self, tmp_dirs, mock_context_builder):
        """Реєстр містить всі 12 генераторів"""
        template_dir, output_dir = tmp_dirs
        registry = create_default_registry(template_dir, output_dir, mock_context_builder)

        expected = [
            "zayavka",
            "protocol_rozgl",
            "perelik",
            "reshenya",
            "akt_vidbir",
            "akt_ident",
            "sertifikat",
            "deklaraciya",
            "ugoda",
            "reshenya_vidachu",
            "protokol_analiz",
            "vysnovok",
        ]

        assert registry.count() == 12
        for name in expected:
            assert registry.has(name), f"Генератор '{name}' відсутній"

    def test_creates_actual_instances(self, tmp_dirs, mock_context_builder):
        """Створені реальні екземпляри генераторів"""
        template_dir, output_dir = tmp_dirs
        registry = create_default_registry(template_dir, output_dir, mock_context_builder)

        zayavka = registry.create("zayavka")
        assert zayavka is not None
        assert hasattr(zayavka, "generate")

        protocol = registry.create("protocol_rozgl")
        assert protocol is not None
        assert hasattr(protocol, "generate")

    def test_zayavka_gets_context_builder(self, tmp_dirs, mock_context_builder):
        """ZayavkaGenerator отримує context_builder як data_service"""
        template_dir, output_dir = tmp_dirs
        registry = create_default_registry(template_dir, output_dir, mock_context_builder)

        zayavka = registry.create("zayavka")
        assert zayavka.data_service is mock_context_builder

    def test_other_generators_dont_need_context_builder(self, tmp_dirs, mock_context_builder):
        """Інші генератори працюють без context_builder"""
        template_dir, output_dir = tmp_dirs
        registry = create_default_registry(template_dir, output_dir, mock_context_builder)

        # Ці генератори не потребують context_builder
        for name in ["protocol_rozgl", "perelik", "reshenya", "sertifikat"]:
            gen = registry.create(name)
            assert gen is not None
            assert hasattr(gen, "generate")
