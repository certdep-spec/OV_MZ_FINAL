"""
Менеджер бази даних SQLite
Чистий шар доступу до даних (Repository)

v2.0: Бізнес-логіку винесено до services/
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple

from models.dto import (
    ProductDTO,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Менеджер бази даних

    ПРИМІТКА: Для нової бізнес-логіки використовуйте сервіси з packages/services/
    Цей клас зберігається для зворотної сумісності з існуючим кодом
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def _connect(self):
        """Створити з'єднання з БД з увімкненими FK."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ===== ІНІЦІАЛІЗАЦІЯ =====

    def init_db(self):
        """Створення таблиць БД та запуск міграцій"""
        from pathlib import Path
        from database.db_migrations import migrate_db
        
        db_path = Path(self.db_path)
        is_new = not db_path.exists() or db_path.stat().st_size == 0
        
        if is_new:
            # Створюємо батьківську папку, якщо її немає
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Шукаємо схему в тій же директорії
            schema_path = Path(__file__).parent / "db_schema.sql"
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn = sqlite3.connect(self.db_path)
                conn.executescript(schema_sql)
                conn.commit()
                conn.close()
                logger.info("БД ініціалізовано за допомогою db_schema.sql (db_manager)")
            else:
                logger.warning(f"Файл схеми {schema_path} не знайдено для ініціалізації!")
                
        # Запускаємо автоматичні міграції
        try:
            migrate_db(db_path)
        except Exception as e:
            logger.error(f"Помилка при виконанні міграції БД в db_manager: {e}")

    # ===== СТАРІ МЕТОДИ (для зворотної сумісності) =====
    # ПРИМІТКА: Новий код має використовувати сервіси з services/

    def get_products(self) -> List[Tuple]:
        """Отримати всі продукти"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, tu_code, shelf_life_months FROM products ORDER BY name"
        )
        products = cursor.fetchall()
        conn.close()
        return products

    def get_standards(self) -> List[Tuple]:
        """Отримати всі активні стандарти"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, description FROM standards WHERE active = 1 ORDER BY id"
        )
        standards = cursor.fetchall()
        conn.close()
        return standards

    def get_facilities(self) -> List[str]:
        """Отримати всі адреси потужностей"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT address FROM production_facilities ORDER BY address")
        facilities = [row[0] for row in cursor.fetchall()]
        conn.close()
        return facilities

    # CRUD ДЛЯ ДОДАТКОВИХ ДОВІДНИКІВ

    def add_product(self, data: Dict):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO products (name, tu_code, shelf_life_months)
            VALUES (?, ?, ?)
        """,
            (
                data["name"],
                data.get("tu_code", ""),
                data.get("shelf_life_months", 36),
            ),
        )
        conn.commit()
        conn.close()

    def update_product(self, old_name: str, data: Dict):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE products SET name=?, tu_code=?, shelf_life_months=?
            WHERE name=?
        """,
            (
                data["name"],
                data.get("tu_code", ""),
                data.get("shelf_life_months", 36),
                old_name,
            ),
        )
        conn.commit()
        conn.close()

    def delete_product(self, name: str):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE name=?", (name,))
        conn.commit()
        conn.close()

    def add_standard(self, data: Dict):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO standards (id, description) VALUES (?, ?)",
            (data["id"], data["description"]),
        )
        conn.commit()
        conn.close()

    def update_standard(self, old_id: int, data: Dict):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE standards SET id=?, description=? WHERE id=?",
            (data["id"], data["description"], old_id),
        )
        conn.commit()
        conn.close()

    def delete_standard(self, std_id: int):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM standards WHERE id=?", (std_id,))
        conn.commit()
        conn.close()

    def add_facility(self, address: str):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO production_facilities (address) VALUES (?)",
            (address,),
        )
        conn.commit()
        conn.close()

    def update_facility(self, old_address: str, new_address: str):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE production_facilities SET address=? WHERE address=?",
            (new_address, old_address),
        )
        conn.commit()
        conn.close()

    def delete_facility(self, address: str):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM production_facilities WHERE address=?", (address,))
        conn.commit()
        conn.close()

    def get_ingredients(self) -> List[Tuple]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, product_name, version, chemical_name, trade_mark, cas_number, certificate FROM ingredients ORDER BY product_name"
        )
        res = cursor.fetchall()
        conn.close()
        return res

    def add_ingredient(self, data: Dict):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ingredients (product_name, version, chemical_name, trade_mark, cas_number, certificate)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                data["product_name"],
                data.get("version", ""),
                data.get("chemical_name", ""),
                data.get("trade_mark", ""),
                data.get("cas_number", ""),
                data.get("certificate", ""),
            ),
        )
        conn.commit()
        conn.close()

    def update_ingredient(self, item_id: int, data: Dict):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE ingredients SET product_name=?, version=?, chemical_name=?, trade_mark=?, cas_number=?, certificate=?
            WHERE id=?
        """,
            (
                data["product_name"],
                data.get("version", ""),
                data.get("chemical_name", ""),
                data.get("trade_mark", ""),
                data.get("cas_number", ""),
                data.get("certificate", ""),
                item_id,
            ),
        )
        conn.commit()
        conn.close()

    def delete_ingredient(self, item_id: int):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ingredients WHERE id=?", (item_id,))
        conn.commit()
        conn.close()

    def get_last_app_number(self) -> str:
        """Отримати останній номер заявки"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT app_number FROM applications ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "001"

    def save_application(self, data: Dict) -> int:
        """Зберегти заявку"""
        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO applications
                (app_number, app_date, company_name, company_code, company_address,
                 director_name, tu_code, production_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["app_number"],
                    data["app_date"],
                    data["company_name"],
                    data["company_code"],
                    data["company_address"],
                    data["director_name"],
                    data["tu_code"],
                    data["production_address"],
                ),
            )
            app_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return app_id
        except sqlite3.IntegrityError:
            cursor.execute(
                """
                UPDATE applications SET
                app_date = ?, company_name = ?, company_code = ?, company_address = ?,
                director_name = ?, tu_code = ?, production_address = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE app_number = ?
            """,
                (
                    data["app_date"],
                    data["company_name"],
                    data["company_code"],
                    data["company_address"],
                    data["director_name"],
                    data["tu_code"],
                    data["production_address"],
                    data["app_number"],
                ),
            )
            conn.commit()
            cursor.execute(
                "SELECT id FROM applications WHERE app_number = ?",
                (data["app_number"],),
            )
            app_id = cursor.fetchone()[0]
            conn.close()
            return app_id
        except Exception:
            conn.close()
            raise

    def save_parties(self, app_id: int, parties: List[Dict]) -> List[int]:
        """Зберегти партії для заявки та вернути їх ID"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM parties WHERE application_id = ?", (app_id,))

        party_ids = []

        for party in parties:
            standards_json = json.dumps(party.get("standards", []), ensure_ascii=False)

            # is_import: nullable - для АФІНА завжди None, для ДЖОНСОН може бути 0/1
            is_import_val = party.get("is_import")
            if is_import_val is None:
                is_import_val = 0  # За замовчуванням вітчизняна

            cursor.execute(
                """
                INSERT INTO parties
                (application_id, party_number, product_name, party_code, party_date,
                 mfg_date, quantity, unit, protocol_number, cert_number, cert_date, shelf_life_months, standards_data, is_import)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    app_id,
                    party.get("party_number", 0),
                    party["product_name"],
                    party.get("party_code", ""),
                    party.get("party_date", ""),
                    party.get("mfg_date", ""),
                    party.get("quantity", 0),
                    party.get("unit", "шт"),
                    party.get("protocol_number", ""),
                    party.get("cert_number", ""),
                    party.get("cert_date", ""),
                    party.get("shelf_life_months", 36),
                    standards_json,
                    is_import_val,
                ),
            )

            party_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        return party_ids

    def get_application(self, app_number: str) -> Optional[Dict]:
        """Отримати заявку за номером"""
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE app_number = ?", (app_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_application_by_id(self, app_id: int) -> Optional[Dict]:
        """Отримати заявку за ID"""
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        conn.close()
        result = dict(row) if row else None
        logger.debug(
            f"get_application_by_id({app_id}) -> type={type(result)}, keys={result.keys() if result else None}"
        )
        return result

    def get_parties(self, app_id: int) -> List[Dict]:
        """Отримати партії для заявки"""
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM parties WHERE application_id = ? ORDER BY party_number",
            (app_id,),
        )
        parties = []
        for row in cursor.fetchall():
            party_dict = dict(row)
            if party_dict.get("standards_data"):
                try:
                    party_dict["standards"] = json.loads(party_dict["standards_data"])
                except json.JSONDecodeError:
                    party_dict["standards"] = []
            else:
                party_dict["standards"] = []
            parties.append(party_dict)
        conn.close()
        logger.debug(
            f"get_parties({app_id}) -> {len(parties)} parties, first party keys: {parties[0].keys() if parties else 'N/A'}"
        )
        return parties

    def get_all_applications(self) -> List[Dict]:
        """Отримати всі заявки"""
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")
        applications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return applications

    def delete_application(self, app_id: int):
        """Видалити заявку та всі її партії (Cascade)"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
            conn.commit()
        finally:
            conn.close()

    def get_standards_text_dict(self, standard_ids: List[int]) -> Dict[str, str]:
        """Отримати тексти стандартів за їхніми ID"""
        result = {f"STD{i}": "" for i in range(1, 7)}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                for std_id in standard_ids:
                    cur.execute(
                        "SELECT description FROM standards WHERE id = ?",
                        (std_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        result[f"STD{std_id}"] = row[0]
        except Exception as e:
            logger.error(f"Помилка отримання стандартів: {e}", exc_info=True)
        return result

    def get_ingredients_for_product(self, product_name: str) -> List[Dict]:
        """Отримати унікальні інгредієнти для продукту"""
        result = []
        seen = set()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT DISTINCT chemical_name, trade_mark, cas_number, certificate
                    FROM ingredients
                    WHERE product_name = ?
                    ORDER BY id
                """,
                    (product_name,),
                )

                for row in cur.fetchall():
                    key = (
                        row["chemical_name"],
                        row["trade_mark"],
                        row["cas_number"],
                        row["certificate"],
                    )
                    if key not in seen:
                        seen.add(key)
                        result.append(dict(row))
        except Exception as e:
            logger.warning(f"Помилка отримання інгредієнтів: {e}")
        return result

    # ===== МЕТОДИ ДЛЯ РОБОТИ З ФІНАЛЬНИМИ ДОКУМЕНТАМИ =====

    def update_party_final_documents(self, party_id: int, final_data: Dict) -> bool:
        """Зберегти дані фінальних документів для партії"""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE parties
                SET
                    protocol_number = ?,
                    protocol_date = ?,
                    cert_number = ?,
                    cert_date = ?,
                    final_docs_completed = 1,
                    final_docs_generated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (
                    final_data.get("protocol_number", ""),
                    final_data.get("protocol_date", ""),
                    final_data.get("cert_number", ""),
                    final_data.get("cert_date", ""),
                    party_id,
                ),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Помилка при збереженні фінальних даних: {e}", exc_info=True)
            return False

    def get_party_final_documents(self, party_id: int) -> Optional[Dict]:
        """Отримати дані фінальних документів для партії"""
        try:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    protocol_number,
                    protocol_date,
                    cert_number,
                    cert_date,
                    final_docs_completed,
                    final_docs_generated_at
                FROM parties
                WHERE id = ?
            """,
                (party_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "protocol_number": row["protocol_number"] or "",
                    "protocol_date": row["protocol_date"] or "",
                    "cert_number": row["cert_number"] or "",
                    "cert_date": row["cert_date"] or "",
                    "completed": bool(row["final_docs_completed"]),
                    "generated_at": row["final_docs_generated_at"],
                }
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні фінальних даних: {e}", exc_info=True)
            return None

    def get_party_with_app_data(self, party_id: int) -> Optional[Dict]:
        """Отримати дані партії разом з даними заявки"""
        try:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    p.*,
                    a.app_number,
                    a.app_date,
                    a.company_name,
                    a.company_code,
                    a.director_name,
                    a.tu_code,
                    a.production_address
                FROM parties p
                JOIN applications a ON p.application_id = a.id
                WHERE p.id = ?
            """,
                (party_id,),
            )

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Помилка при отриманні даних партії: {e}", exc_info=True)
            return None

    def get_available_versions(self, product_name: str) -> List[str]:
        """Отримати список доступних версій (складів) для продукту"""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT version FROM ingredients
                WHERE product_name = ? AND version IS NOT NULL AND version != ''
                ORDER BY version
            """,
                (product_name,),
            )

            versions = [row[0] for row in cursor.fetchall()]
            conn.close()

            return versions if versions else []

        except Exception as e:
            logger.error(f"Помилка при отриманні версій продукту: {e}", exc_info=True)
            return []

    def get_par_certificates(self, product_name: str, version: str = "") -> str:
        """Отримати список сертифікатів ПАР для продукту та версії"""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            if version:
                cursor.execute(
                    """
                    SELECT certificate FROM ingredients
                    WHERE product_name = ? AND version = ? AND certificate IS NOT NULL AND certificate != ''
                    ORDER BY id
                """,
                    (product_name, version),
                )
            else:
                cursor.execute(
                    """
                    SELECT certificate FROM ingredients
                    WHERE product_name = ? AND certificate IS NOT NULL AND certificate != ''
                    ORDER BY id
                """,
                    (product_name,),
                )

            certificates = [row[0] for row in cursor.fetchall()]
            conn.close()

            return ", ".join(certificates) if certificates else ""

        except Exception as e:
            logger.error(f"Помилка при отриманні сертифікатів ПАР: {e}", exc_info=True)
            return ""

    # ===== НОВІ МЕТОДИ З DTO (для інтеграції з сервісами) =====

    def get_product_dto(self, name: str) -> Optional[ProductDTO]:
        """Отримати продукт як DTO"""
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, tu_code, shelf_life_months, dkpp_code, uktzed_code, created_at "
            "FROM products WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return ProductDTO(
            id=row["id"],
            name=row["name"],
            tu_code=row["tu_code"] or "",
            shelf_life_months=row["shelf_life_months"] or 36,
            dkpp_code=row["dkpp_code"] or "20.41.32-50.00",
            uktzed_code=row["uktzed_code"] or "3402",
            created_at=row["created_at"],
        )

    def get_ingredients_with_version(
        self, product_name: str, version: str
    ) -> List[Dict]:
        """Отримати інгредієнти для продукту з фільтрацією за версією"""
        result = []
        seen = set()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT chemical_name, trade_mark, cas_number, certificate, version
                    FROM ingredients
                    WHERE product_name = ? AND version = ?
                    ORDER BY id
                """,
                    (product_name, version),
                )

                for row in cur.fetchall():
                    key = (
                        row["chemical_name"],
                        row["trade_mark"],
                        row["cas_number"],
                    )
                    if key not in seen:
                        seen.add(key)
                        result.append(dict(row))
        except Exception as e:
            logger.warning(f"Помилка отримання інгредієнтів: {e}")
        return result

    def close(self):
        """Метод закриття (для сумісності з GUI)"""
        return
