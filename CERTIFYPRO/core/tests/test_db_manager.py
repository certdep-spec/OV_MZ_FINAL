"""
Тесты менеджера базы данных CertifyPro
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Создание временной базы данных для тестов"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Очистка
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db_manager(temp_db):
    """Фикстура менеджера БД"""
    return DatabaseManager(temp_db)


def test_database_created(temp_db):
    """Проверка создания базы данных"""
    assert os.path.exists(temp_db)


def test_tables_exist(db_manager):
    """Проверка создания таблиц"""
    conn = sqlite3.connect(db_manager.db_path)
    cursor = conn.cursor()

    # Проверяем все основные таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    assert "products" in tables
    assert "standards" in tables
    assert "applications" in tables
    assert "parties" in tables
    assert "ingredients" in tables
    assert "production_facilities" in tables

    conn.close()


def test_add_product(db_manager):
    """Тест добавления продукта"""
    db_manager.add_product(
        {
            "name": "Тестовый продукт",
            "tu_code": "ТУ 123",
            "shelf_life_months": 24,
        }
    )

    products = db_manager.get_products()
    product_names = [p[0] for p in products]
    assert "Тестовый продукт" in product_names


def test_get_products_empty(db_manager):
    """Тест получения продуктов из пустой БД"""
    products = db_manager.get_products()
    assert isinstance(products, list)


def test_add_standard(db_manager):
    """Тест добавления стандарта"""
    db_manager.add_standard({"id": 1, "description": "Тестовый стандарт"})

    standards = db_manager.get_standards()
    assert len(standards) > 0


def test_add_facility(db_manager):
    """Тест добавления мощности"""
    db_manager.add_facility("Тестовый адрес")

    facilities = db_manager.get_facilities()
    assert "Тестовый адрес" in facilities


def test_save_application(db_manager):
    """Тест сохранения заявки"""
    app_id = db_manager.save_application(
        {
            "app_number": "001",
            "app_date": "01.01.2024",
            "company_name": "Тестовая компания",
            "company_code": "12345678",
            "company_address": "ул. Тестовая 1",
            "director_name": "Иванов И.И.",
            "tu_code": "ТУ 123",
            "production_address": "ул. Производственная 1",
        }
    )

    assert app_id > 0


def test_get_application(db_manager):
    """Тест получения заявки"""
    db_manager.save_application(
        {
            "app_number": "002",
            "app_date": "01.01.2024",
            "company_name": "Тестовая компания 2",
            "company_code": "87654321",
            "company_address": "ул. Тестовая 2",
            "director_name": "Петров П.П.",
            "tu_code": "ТУ 456",
            "production_address": "ул. Производственная 2",
        }
    )

    app = db_manager.get_application("002")
    assert app is not None
    assert app["company_name"] == "Тестовая компания 2"


def test_save_and_get_parties(db_manager):
    """Тест сохранения и получения партий"""
    app_id = db_manager.save_application(
        {
            "app_number": "003",
            "app_date": "01.01.2024",
            "company_name": "Тестовая компания 3",
            "company_code": "11111111",
            "company_address": "ул. Тестовая 3",
            "director_name": "Сидоров С.С.",
            "tu_code": "ТУ 789",
            "production_address": "ул. Производственная 3",
        }
    )

    parties = [
        {
            "party_number": 1,
            "product_name": "Тестовый продукт",
            "party_code": "П001",
            "party_date": "01.01.2024",
            "quantity": 100,
            "unit": "шт",
            "standards": [1, 2],
        }
    ]

    party_ids = db_manager.save_parties(app_id, parties)
    assert len(party_ids) == 1

    saved_parties = db_manager.get_parties(app_id)
    assert len(saved_parties) == 1
    assert saved_parties[0]["product_name"] == "Тестовый продукт"


def test_delete_application(db_manager):
    """Тест удаления заявки"""
    app_id = db_manager.save_application(
        {
            "app_number": "004",
            "app_date": "01.01.2024",
            "company_name": "Тестовая компания для удаления",
            "company_code": "99999999",
            "company_address": "ул. Тестовая 4",
            "director_name": "Удалов У.У.",
            "tu_code": "ТУ 000",
            "production_address": "ул. Производственная 4",
        }
    )

    db_manager.delete_application(app_id)

    app = db_manager.get_application_by_id(app_id)
    assert app is None


def test_get_all_applications(db_manager):
    """Тест получения всех заявок"""
    # Добавляем несколько заявок
    for i in range(5):
        db_manager.save_application(
            {
                "app_number": f"00{i + 1}",
                "app_date": "01.01.2024",
                "company_name": f"Компания {i + 1}",
                "company_code": f"{10000000 + i}",
                "company_address": f"ул. Тестовая {i + 1}",
                "director_name": f"Директор {i + 1}",
                "tu_code": f"ТУ {i + 1}",
                "production_address": f"ул. Производственная {i + 1}",
            }
        )

    apps = db_manager.get_all_applications()
    assert len(apps) == 5


def test_close(db_manager):
    """Тест закрытия менеджера БД"""
    db_manager.close()
    # Метод должен выполниться без ошибок
    assert True


def test_db_migrations(temp_db):
    """Тест автоматической миграции БД с версии v1 на v3"""
    from database.db_migrations import migrate_db
    
    # 1. Создаем "старую" БД версии v1 вручную
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Создаем таблицу products
    cursor.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)")
    
    # Создаем таблицу parties без колонки is_import
    cursor.execute("""
        CREATE TABLE parties (
            id INTEGER PRIMARY KEY,
            application_id INTEGER,
            product_name TEXT,
            party_code TEXT
        )
    """)
    
    # Создаем таблицу ingredients без UNIQUE ограничения и с дубликатами
    cursor.execute("""
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            version TEXT,
            chemical_name TEXT
        )
    """)
    
    # Вставляем дубликаты
    cursor.execute("INSERT INTO products (name) VALUES ('Продукт 1')")
    cursor.execute("INSERT INTO ingredients (product_name, version, chemical_name) VALUES ('Продукт 1', 'v1', 'Ингр 1')")
    cursor.execute("INSERT INTO ingredients (product_name, version, chemical_name) VALUES ('Продукт 1', 'v1', 'Ингр 1')") # Дубликат!
    cursor.execute("INSERT INTO ingredients (product_name, version, chemical_name) VALUES ('Продукт 1', 'v1', 'Ингр 2')")
    
    conn.commit()
    conn.close()
    
    # 2. Запускаем миграцию
    migrate_db(Path(temp_db))
    
    # 3. Проверяем результаты
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # А. Проверяем версию схемы
    cursor.execute("SELECT version FROM schema_version LIMIT 1")
    version = cursor.fetchone()[0]
    assert version == 3
    
    # Б. Проверяем, что колонка is_import добавлена в parties
    cursor.execute("PRAGMA table_info(parties)")
    cols = [col[1] for col in cursor.fetchall()]
    assert "is_import" in cols
    
    # В. Проверяем, что дубликат ингредиента удален
    cursor.execute("SELECT * FROM ingredients")
    ings = cursor.fetchall()
    assert len(ings) == 2
    
    # Г. Проверяем UNIQUE constraint (попытка вставить дубликат должна вызвать IntegrityError)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO ingredients (product_name, version, chemical_name) VALUES ('Продукт 1', 'v1', 'Ингр 1')")
        conn.commit()
        
    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
