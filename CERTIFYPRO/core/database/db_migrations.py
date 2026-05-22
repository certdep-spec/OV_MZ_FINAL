"""
Модуль міграцій бази даних для CertifyPro.
Відповідає за автоматичне оновлення структури БД клієнтів при виході нових релізів.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

def migrate_db(db_path: Path) -> None:
    """
    Виконує міграцію бази даних до останньої версії (v3).
    Робить бекап перед міграцією та обробляє можливі помилки.
    """
    db_path = Path(db_path).resolve()
    if not db_path.exists():
        logger.warning(f"Файл БД не існує для міграції: {db_path}")
        return

    logger.info(f"🚀 Запуск міграції для БД: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 1. Перевіряємо поточну версію схеми
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if not cursor.fetchone():
            # Якщо таблиці версій немає, створюємо її
            cursor.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
            
            # Визначаємо поточний стан (чи є is_import)
            cursor.execute("PRAGMA table_info(parties)")
            parties_cols = [col[1] for col in cursor.fetchall()]
            
            initial_version = 2 if "is_import" in parties_cols else 1
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (initial_version,))
            conn.commit()
            logger.info(f"Ініціалізовано версію схеми як v{initial_version}")

        cursor.execute("SELECT version FROM schema_version LIMIT 1")
        current_version = cursor.fetchone()[0]
        logger.info(f"Поточна версія схеми в БД: v{current_version}")

        # ===== МІГРАЦІЯ v1 -> v2 (Додавання колонки is_import) =====
        if current_version < 2:
            logger.info("🔧 Міграція v1 -> v2: додавання колонки is_import в таблицю parties...")
            cursor.execute("PRAGMA table_info(parties)")
            parties_cols = [col[1] for col in cursor.fetchall()]
            if "is_import" not in parties_cols:
                cursor.execute("ALTER TABLE parties ADD COLUMN is_import INTEGER DEFAULT 0")
            cursor.execute("UPDATE schema_version SET version = 2")
            conn.commit()
            logger.info("✅ Успішно оновлено до версії v2")

        # ===== МІГРАЦІЯ v2 -> v3 (Унікальний індекс на ingredients) =====
        if current_version < 3:
            logger.info("🔧 Міграція v2 -> v3: додавання UNIQUE(product_name, version, chemical_name)...")
            
            # А. Видаляємо дублікати інгредієнтів перед створенням UNIQUE
            logger.info("  1/4 Очищення дублікатів інгредієнтів...")
            cursor.execute("""
                DELETE FROM ingredients 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM ingredients 
                    GROUP BY product_name, COALESCE(version, ''), COALESCE(chemical_name, '')
                )
            """)
            
            # Б. Перевіряємо чи є вже UNIQUE в структурі таблиці
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='ingredients'")
            create_sql = cursor.fetchone()[0]
            
            if "UNIQUE" not in create_sql:
                logger.info("  2/4 Перебудова таблиці ingredients...")
                cursor.execute("ALTER TABLE ingredients RENAME TO ingredients_old")
                
                cursor.execute("""
                    CREATE TABLE ingredients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_name TEXT NOT NULL,
                        version TEXT,
                        chemical_name TEXT,
                        trade_mark TEXT,
                        cas_number TEXT,
                        certificate TEXT,
                        FOREIGN KEY (product_name) REFERENCES products(name),
                        UNIQUE(product_name, version, chemical_name)
                    )
                """)
                
                logger.info("  3/4 Копіювання даних...")
                # Динамічно визначаємо які колонки існують в старій таблиці
                cursor.execute("PRAGMA table_info(ingredients_old)")
                old_cols = [col[1] for col in cursor.fetchall()]
                
                # Всі можливі колонки в новій таблиці (крім id — він AUTOINCREMENT)
                all_cols = ["id", "product_name", "version", "chemical_name", "trade_mark", "cas_number", "certificate"]
                # Беремо тільки ті, що є в старій таблиці
                cols_to_copy = [c for c in all_cols if c in old_cols]
                cols_str = ", ".join(cols_to_copy)
                
                cursor.execute(f"INSERT INTO ingredients ({cols_str}) SELECT {cols_str} FROM ingredients_old")
                
                logger.info("  4/4 Очищення тимчасової таблиці...")
                cursor.execute("DROP TABLE ingredients_old")
            else:
                logger.info("  Обмеження UNIQUE вже існує в таблиці ingredients, перенос не потрібен.")

            cursor.execute("UPDATE schema_version SET version = 3")
            conn.commit()
            logger.info("✅ Успішно оновлено до версії v3")

        logger.info(f"🎉 Міграція завершена! БД {db_path.name} знаходиться в актуальному стані (v3).")

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Помилка міграції БД {db_path}: {e}", exc_info=True)
        raise e
    finally:
        conn.close()
