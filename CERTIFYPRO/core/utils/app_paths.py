"""
Шляхи та ініціалізація додатку CertifyPro.

Виділено з config.py для зменшення coupling.
Цей модуль відповідає за:
- Визначення шляхів (dev / PyInstaller)
- Створення директорій
- Деплой БД при першому запуску .exe
- Ініціалізацію інфраструктури динамічних клієнтів
"""

import logging
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# ===== Додаємо core/ в PYTHONPATH для коректних імпортів =====
_CORE_DIR = Path(__file__).parent.parent
if str(_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_DIR))

# Завантажуємо .env файл якщо є
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from utils.path_provider import (
    get_launcher_root,
    get_profiles_path,
    get_project_root,
    get_templates_dir,
)

logger = logging.getLogger(__name__)

# ===== БАЗОВІ ШЛЯХИ =====
BASE_DIR = get_project_root()
APP_DIR = get_launcher_root()
PROJECT_ROOT = APP_DIR

DATA_DIR = APP_DIR / "data"
LOGS_DIR = APP_DIR / "logs"
TEMPLATES_DIR = get_templates_dir()
PROFILES_PATH = get_profiles_path()

# Ці шляхи будуть динамічно уточнені в init_client_config
DB_PATH = DATA_DIR / "certify.db"
DOCUMENTS_DIR = DATA_DIR / "Documents"


def ensure_dirs() -> None:
    """Створити необхідні директорії."""
    for d in [DATA_DIR, DOCUMENTS_DIR, TEMPLATES_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def deploy_databases() -> None:
    """
    Розгорнути бази даних при першому запуску .exe.

    Копіює certify.db з _MEIPASS/data/КЛІЄНТ/ у APP_DIR/data/КЛІЄНТ/
    якщо їх ще немає.
    """
    if not getattr(sys, "frozen", False):
        return

    clients = ["АФІНА", "ДЖОНСОН", "PROCTER"]

    for client_name in clients:
        src_db = BASE_DIR / "data" / client_name / "certify.db"
        target_dir = APP_DIR / "data" / client_name
        target_db = target_dir / "certify.db"

        target_dir.mkdir(parents=True, exist_ok=True)

        if target_db.exists():
            logger.info("БД вже існує: %s", target_db)
        elif src_db.exists():
            shutil.copy2(str(src_db), str(target_db))
            logger.info("Розгорнуто БД для %s: %s -> %s", client_name, src_db, target_db)
        else:
            logger.warning("БД для %s не знайдено в пакеті: %s", client_name, src_db)

    for client_name in clients:
        (APP_DIR / "data" / client_name / "Documents").mkdir(
            parents=True, exist_ok=True
        )

    (APP_DIR / "logs").mkdir(parents=True, exist_ok=True)


_app_initialized = False


def initialize_app() -> None:
    """
    Ініціалізувати додаток: створити директорії, розгорнути БД.

    Викликати з entrypoint (main.py) ПЕРЕД init_client_config().
    Не викликається автоматично при імпорті — уникаємо side-effects.
    """
    global _app_initialized
    if _app_initialized:
        return

    ensure_dirs()
    deploy_databases()
    _app_initialized = True


def ensure_dynamic_client_infrastructure(data_dir: Path, client_id: str) -> None:
    """
    Перевірити та створити мінімальну інфраструктуру для динамічного клієнта.

    Викликається коли клієнта немає в profiles.yaml (доданий через лаунчер).
    Створює папки та порожню БД якщо їх ще немає.
    """
    try:
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "Documents").mkdir(parents=True, exist_ok=True)
            logger.info("Створено папку для динамічного клієнта: %s", data_dir)

        db_path = data_dir / "certify.db"
        if not db_path.exists():
            logger.info("Створюю БД для динамічного клієнта: %s", db_path)

            schema_path = BASE_DIR / "CERTIFYPRO" / "core" / "database" / "db_schema.sql"
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()

                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.executescript(schema_sql)
                conn.commit()
                conn.close()
                logger.info("БД створено: %s", db_path)
            else:
                logger.warning(
                    "db_schema.sql не знайдено, використовується fallback ініціалізація"
                )
                from di import _init_database

                _init_database(db_path)

    except Exception as e:
        logger.error("Помилка створення інфраструктури для %s: %s", client_id, e)
