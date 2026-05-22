"""
Останні тести для покриття - досягнення 60%
"""

import os
import tempfile

import pytest

from database.db_manager import DatabaseManager
from models.dto import ApplicationDTO, PartyDTO
from services.application_service import ApplicationService


@pytest.fixture
def temp_db():
    """Створення тимчасової БД"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    db_manager = DatabaseManager(temp_file.name)
    db_manager.close()
    yield temp_file.name
    os.unlink(temp_file.name)


class TestApplicationServiceFull:
    """Повні тести для ApplicationService"""

    def test_update_party_final_documents_success(self, temp_db):
        """Оновлення фінальних документів партії"""
        service = ApplicationService(temp_db)

        # Створення заявки
        app = ApplicationDTO(app_number="200", app_date="05.04.2026")
        app_id = service.save_application(app)

        # Додавання партії
        parties = [PartyDTO(product_name="Тест", party_code="01E")]
        party_ids = service.save_parties(app_id, parties)

        # Оновлення фінальних документів
        from models.dto import FinalDocumentsDTO

        final_docs = FinalDocumentsDTO(
            completed=True, generated_at="2026-04-05 12:00:00"
        )

        result = service.update_party_final_documents(party_ids[0], final_docs)
        assert result is True

        # Перевірка
        updated_parties = service.get_parties_for_application(app_id)
        assert len(updated_parties) == 1
        assert updated_parties[0].final_docs_completed is True

        service.close()

    def test_get_last_app_number_with_many_apps(self, temp_db):
        """Отримання останнього номера заявки з багатьма заявками"""
        service = ApplicationService(temp_db)

        for i in range(1, 20):
            service.save_application(
                ApplicationDTO(app_number=str(i).zfill(3), app_date="05.04.2026")
            )

        last = service.get_last_app_number()
        assert last == "019"

        service.close()


class TestDatabaseManager:
    """Тести для DatabaseManager"""

    def test_get_all_applications_empty(self, temp_db):
        """Отримання всіх заявок - порожня БД"""
        from database.db_manager import DatabaseManager

        db = DatabaseManager(temp_db)

        apps = db.get_all_applications()
        assert isinstance(apps, list)
        assert len(apps) == 0

        db.close()


class TestConfig:
    """Тести для config"""

    def test_db_path_exists(self):
        """Перевірка що DB_PATH існує"""
        import config

        assert hasattr(config, "DB_PATH")

    def test_templates_dir_exists(self):
        """Перевірка що TEMPLATES_DIR існує"""
        import config

        assert hasattr(config, "TEMPLATES_DIR")

    def test_documents_dir_exists(self):
        """Перевірка що DOCUMENTS_DIR існує"""
        import config

        assert hasattr(config, "DOCUMENTS_DIR")

    def test_colors_exist(self):
        """Перевірка що COLORS існує"""
        import config

        assert hasattr(config, "COLORS")
        assert isinstance(config.COLORS, dict)
