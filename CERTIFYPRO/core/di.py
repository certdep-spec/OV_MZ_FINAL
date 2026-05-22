"""
DI Container для CertifyPro (Мультиклієнтська версія)
Централізує створення та управління залежностями (сервісами).
"""

import sqlite3
from pathlib import Path
from typing import Optional

import config
from services.application_service import ApplicationService
from services.dictionary_service import DictionaryService
from services.document_service import DocumentService

# ImportService — опціональний (залежить від pandas)
try:
    from services.import_service import PANDAS_AVAILABLE, ImportService

    IMPORT_SERVICE_AVAILABLE = PANDAS_AVAILABLE
except (ImportError, ModuleNotFoundError) as e:
    ImportService = None  # type: ignore
    IMPORT_SERVICE_AVAILABLE = False
    import logging

    logging.getLogger(__name__).warning(
        f"⚠️ ImportService недоступний (можливо, відсутній pandas): {e}. "
        f"Імпорт з Excel буде недоступний."
    )


def _init_database(db_path: Path) -> None:
    """Ініціалізує базу даних — створює всі таблиці та запускає міграції."""
    import logging
    import shutil
    from database.db_migrations import migrate_db

    logger = logging.getLogger(__name__)

    # Гарантовано створюємо папку для БД
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # У frozen-режимі: якщо БД поруч з .exe пуста/не існує — копіюємо шаблон з _internal
    if getattr(__import__("sys"), "frozen", False):
        internal_db = Path(__import__("sys")._MEIPASS) / "data" / "certify.db"
        if internal_db.exists() and (
            not db_path.exists() or db_path.stat().st_size == 0
        ):
            logger.info(f"Копіюємо БД з _internal: {internal_db} -> {db_path}")
            shutil.copy2(str(internal_db), str(db_path))

    logger.info(f"Ініціалізація БД: {db_path}")

    # Якщо база даних нова чи пуста, ініціалізуємо її за допомогою db_schema.sql
    is_new = not db_path.exists() or db_path.stat().st_size == 0
    if is_new:
        logger.info("База даних пуста, застосовуємо db_schema.sql...")
        schema_path = Path(__file__).parent / "database" / "db_schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn = sqlite3.connect(str(db_path))
            conn.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("Схему успішно завантажено в нову БД!")
        else:
            logger.warning(f"Файл схеми {schema_path} не знайдено для ініціалізації!")

    # Запускаємо міграції для будь-якої бази (нової чи існуючої)
    try:
        migrate_db(db_path)
    except Exception as e:
        logger.error(f"Помилка при виконанні міграції БД: {e}")

    # Перевірка що таблиці дійсно створені
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"Таблиці в БД: {tables}")
    conn.close()


class DIContainer:
    """
    Контейнер залежностей (Dependency Injection Container).

    Забезпечує єдине місце створення сервісів,
    що спрощує тестування та заміну реалізацій.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or config.DB_PATH
        self._app_service: Optional[ApplicationService] = None
        self._dict_service: Optional[DictionaryService] = None
        self._doc_service: Optional[DocumentService] = None
        self._import_service: Optional[ImportService] = None

        # Ініціалізуємо БД при створенні контейнера
        _init_database(self._db_path)

    @property
    def db_path(self) -> Path:
        return self._db_path

    def get_app_service(self) -> ApplicationService:
        if self._app_service is None:
            self._app_service = ApplicationService(str(self._db_path))
        return self._app_service

    def get_dict_service(self) -> DictionaryService:
        if self._dict_service is None:
            self._dict_service = DictionaryService(str(self._db_path))
        return self._dict_service

    def get_doc_service(
        self,
        templates_dir: Optional[Path] = None,
        documents_dir: Optional[Path] = None,
    ) -> DocumentService:
        if self._doc_service is None:
            self._doc_service = DocumentService(
                str(self._db_path),
                str(templates_dir or config.TEMPLATES_DIR),
                str(documents_dir or config.DOCUMENTS_DIR),
            )
        return self._doc_service

    def get_import_service(self) -> Optional[ImportService]:
        if not IMPORT_SERVICE_AVAILABLE:
            return None
        if self._import_service is None:
            self._import_service = ImportService(str(self._db_path))
        return self._import_service

    def reset(self):
        """Скинути всі кешовані сервіси (корисно для тестів)."""
        self._app_service = None
        self._dict_service = None
        self._doc_service = None
        self._import_service = None
