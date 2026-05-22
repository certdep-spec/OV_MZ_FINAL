"""
Тесты конфигурации CertifyPro
"""

import sys
from pathlib import Path

import pytest

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


def test_version_exists():
    """Проверка что версия указана"""
    assert config.VERSION is not None
    assert config.VERSION != ""


def test_app_name_exists():
    """Проверка что название приложения указано"""
    assert config.APP_NAME is not None
    assert config.APP_NAME == "CertifyPro"


def test_paths_are_valid():
    """Проверка что пути корректны"""
    assert config.BASE_DIR is not None
    assert config.DB_PATH is not None
    assert config.TEMPLATES_DIR is not None
    assert config.DOCUMENTS_DIR is not None


def test_directories_created():
    """Проверка что директории созданы"""
    assert config.DATA_DIR.exists()
    assert config.TEMPLATES_DIR.exists()
    assert config.DOCUMENTS_DIR.exists()
    assert config.LOGS_DIR.exists()


def test_color_theme():
    """Проверка цветовой темы"""
    assert config.COLORS is not None
    assert "primary" in config.COLORS
    assert "success" in config.COLORS
    assert "error" in config.COLORS


def test_date_format():
    """Проверка формата даты"""
    assert config.DATE_FORMAT is not None
    assert config.FILE_DATE_FORMAT is not None
    assert config.DATETIME_FORMAT is not None


def test_limits():
    """Проверка ограничений"""
    assert config.MAX_PARTIES_PER_APP > 0
    assert config.MIN_APP_NUMBER >= 1
    assert config.MAX_APP_NUMBER > config.MIN_APP_NUMBER


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
