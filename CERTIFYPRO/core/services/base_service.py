"""
Базовий клас для сервісів

v3.1: Додано:
- WAL mode для надійності SQLite
- Thread-safe підключення (check_same_thread=False)
- Transaction manager для крос-сервісних операцій
- Backup rotation
"""

import logging
import shutil
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from exceptions import DatabaseError

logger = logging.getLogger(__name__)


class TransactionManager:
    """
    Менеджер транзакцій для крос-сервісних бізнес-операцій.

    Забезпечує атомарність операцій що охоплюють кілька сервісів
    або кілька кроків в одному сервісі.

    Використання:
        with TransactionManager(db_path) as txn:
            app_service.save_application(app, txn=txn)
            dict_service.save_products(products, txn=txn)
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is None:
            return
        try:
            if exc_type is not None:
                self._conn.rollback()
                logger.warning("Транзакцію скасовано: %s", exc_val)
            else:
                self._conn.commit()
                logger.info("Транзакцію успішно завершено")
        finally:
            self._conn.close()
            self._conn = None
        return False

    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Повернути активне підключення або None."""
        return self._conn


def create_backup(db_path: str, backup_dir: str, max_backups: int = 5) -> Optional[str]:
    """
    Створити резервну копію БД з ротацією.

    Args:
        db_path: Шлях до БД
        backup_dir: Папка для бекапів
        max_backups: Максимальна кількість бекапів

    Returns:
        Шлях до створеного бекапу або None
    """
    db = Path(db_path)
    if not db.exists():
        logger.warning("БД не існує: %s", db_path)
        return None

    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"{db.stem}_backup_{timestamp}{db.suffix}"

    try:
        shutil.copy2(str(db), str(backup_file))
        logger.info("Бекап створено: %s (%d байт)", backup_file, backup_file.stat().st_size)
    except Exception as e:
        logger.error("Помилка створення бекапу: %s", e)
        return None

    # Ротація — видалити старі бекапи
    existing = sorted(backup_path.glob(f"{db.stem}_backup_*{db.suffix}"))
    while len(existing) > max_backups:
        oldest = existing.pop(0)
        oldest.unlink()
        logger.info("Видалено старий бекап: %s", oldest)

    return str(backup_file)


class BaseService:
    """Базовий клас для всіх сервісів"""

    # Константи для таблиць
    class Tables:
        APPLICATIONS = "applications"
        PARTIES = "parties"
        PRODUCTS = "products"
        STANDARDS = "standards"
        PRODUCTION_FACILITIES = "production_facilities"
        INGREDIENTS = "ingredients"

    # Константи для колонок таблиці applications
    class AppColumns:
        ID = "id"
        APP_NUMBER = "app_number"
        APP_DATE = "app_date"
        COMPANY_NAME = "company_name"
        COMPANY_CODE = "company_code"
        COMPANY_ADDRESS = "company_address"
        DIRECTOR_NAME = "director_name"
        TU_CODE = "tu_code"
        PRODUCTION_ADDRESS = "production_address"
        CREATED_AT = "created_at"
        UPDATED_AT = "updated_at"

    # Константи для колонок таблиці parties
    class PartyColumns:
        ID = "id"
        APPLICATION_ID = "application_id"
        PARTY_NUMBER = "party_number"
        PRODUCT_NAME = "product_name"
        PARTY_CODE = "party_code"
        PARTY_DATE = "party_date"
        MFG_DATE = "mfg_date"
        QUANTITY = "quantity"
        UNIT = "unit"
        PROTOCOL_NUMBER = "protocol_number"
        PROTOCOL_DATE = "protocol_date"
        CERT_NUMBER = "cert_number"
        CERT_DATE = "cert_date"
        SHELF_LIFE_MONTHS = "shelf_life_months"
        STANDARDS_DATA = "standards_data"
        FINAL_DOCS_COMPLETED = "final_docs_completed"
        FINAL_DOCS_GENERATED_AT = "final_docs_generated_at"
        VERSION = "version"
        IS_IMPORT = "is_import"

    # Константи для колонок таблиці products
    class ProductColumns:
        ID = "id"
        NAME = "name"
        TU_CODE = "tu_code"
        SHELF_LIFE_MONTHS = "shelf_life_months"
        DKPP_CODE = "dkpp_code"
        UKTZED_CODE = "uktzed_code"
        CREATED_AT = "created_at"

    # Константи для колонок таблиці standards
    class StandardColumns:
        ID = "id"
        DESCRIPTION = "description"
        ACTIVE = "active"

    # Константи для колонок таблиці production_facilities
    class FacilityColumns:
        ID = "id"
        ADDRESS = "address"
        COMPANY_NAME = "company_name"

    # Константи для колонок таблиці ingredients
    class IngredientColumns:
        ID = "id"
        PRODUCT_NAME = "product_name"
        VERSION = "version"
        CHEMICAL_NAME = "chemical_name"
        TRADE_MARK = "trade_mark"
        CAS_NUMBER = "cas_number"
        CERTIFICATE = "certificate"

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _create_connection(self) -> sqlite3.Connection:
        """Створити нове підключення з WAL mode та thread safety."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-2000")
        return conn

    @contextmanager
    def _get_connection(self, txn: Optional[TransactionManager] = None) -> Generator[sqlite3.Connection, None, None]:
        """
        Контекстний менеджер підключення до БД.

        Якщо передано txn — використовує його підключення (для крос-сервісних транзакцій).
        Інакше створює нове підключення з auto-commit/rollback.

        Args:
            txn: Опціональний TransactionManager для крос-сервісних операцій
        """
        if txn and txn.get_connection():
            yield txn.get_connection()
            return

        conn = self._create_connection()
        try:
            yield conn
            conn.commit()
        except DatabaseError:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Помилка роботи з БД: {e}") from e
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Створити явну транзакцію для бізнес-операції.

        Використовується коли одна бізнес-операція вимагає
        кількох SQL-операцій які мають бути атомарними.

        Приклад:
            with service.transaction() as conn:
                conn.execute("INSERT INTO applications ...")
                conn.execute("INSERT INTO parties ...")
        """
        conn = self._create_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Транзакцію скасовано: %s", e)
            raise DatabaseError(f"Помилка транзакції: {e}") from e
        finally:
            conn.close()

    def _execute_query(self, query: str, params: tuple = (), txn: Optional[TransactionManager] = None) -> list:
        """Виконати SELECT запит"""
        with self._get_connection(txn) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def _execute_command(self, query: str, params: tuple = (), txn: Optional[TransactionManager] = None) -> int:
        """Виконати INSERT/UPDATE/DELETE запит, повернути lastrowid"""
        with self._get_connection(txn) as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid or 0

    def _execute_many(self, query: str, params_list: list, txn: Optional[TransactionManager] = None) -> None:
        """Виконати пакетну операцію INSERT/UPDATE/DELETE"""
        with self._get_connection(txn) as conn:
            conn.executemany(query, params_list)

    def _get_value(self, row: Any, key: str, default: Any = None) -> Any:
        """Безпечне вилучення значення з рядка БД з обробкою NULL"""
        val = row[key]
        return default if val is None else val

    def backup_database(self, backup_dir: str, max_backups: int = 5) -> Optional[str]:
        """Створити резервну копію БД."""
        return create_backup(self.db_path, backup_dir, max_backups)

    def run_integrity_check(self) -> bool:
        """Перевірити цілісність БД."""
        try:
            conn = self._create_connection()
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            if result and result[0] == "ok":
                return True
            logger.warning("Integrity check failed: %s", result)
            return False
        except Exception as e:
            logger.error("Integrity check error: %s", e)
            return False

    def close(self) -> None:
        """Закрити ресурси сервісу (для сумісності)"""
        pass
