"""
Сервіс імпорту даних з Excel
Відповідає за читання Excel-файлів та запис даних в БД
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore

try:
    from config import get_client_config

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    get_client_config = None

from exceptions import DatabaseError, DataImportError
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class ImportService(BaseService):
    """
    Сервіс для імпорту даних з Excel-файлів.

    Очікує аркуші:
    - ДОВІДНИК_ПРОДУКЦІЯ
    - НД (стандарти)
    - ДОВІДНИК_ПОТУЖНОСТІ
    - ДОВІДНИК_СКЛАД
    - ЗАЯВКА (включає ID клієнта в рядку 8, колонці B)
    """

    # Назви аркушів
    SHEET_PRODUCTS = "ДОВІДНИК_ПРОДУКЦІЯ"
    SHEET_STANDARDS = "НД"
    SHEET_FACILITIES = "ДОВІДНИК_ПОТУЖНОСТІ"
    SHEET_INGREDIENTS = "ДОВІДНИК_СКЛАД"
    SHEET_APPLICATION = "ЗАЯВКА"

    # Рядок та колонка для ID клієнта в аркуші ЗАЯВКА (0-індекс)
    CLIENT_ID_ROW = 7
    CLIENT_ID_COL = 1

    def __init__(self, db_path):
        super().__init__(db_path)
        if not PANDAS_AVAILABLE:
            logger.warning(
                "⚠️ Модуль pandas не встановлено. Імпорт з Excel буде недоступний. "
                "Встановіть: pip install pandas openpyxl"
            )

    def import_from_excel(self, excel_path: str) -> Dict[str, int]:
        """
        Імпорт даних з Excel-файлу.

        Args:
            excel_path: Шлях до Excel-файлу

        Returns:
            Словник статистики: products, standards, facilities, ingredients, errors

        Raises:
            DataImportError: Якщо файл не знайдено або помилка читання
        """
        if not PANDAS_AVAILABLE:
            raise DataImportError(
                "Імпорт з Excel недоступний. Встановіть модуль pandas: pip install pandas openpyxl"
            )

        stats = {
            "products": 0,
            "standards": 0,
            "facilities": 0,
            "ingredients": 0,
            "applications": 0,
            "parties": 0,
            "errors": 0,
        }

        # Перевірка існування файлу
        file_path = Path(excel_path)
        if not file_path.exists():
            raise DataImportError(f"Файл не знайдено: {excel_path}")

        # Отримуємо існуючі дані для інгредієнтів (для дедуплікації в коді)
        existing_ingredients = self._get_existing_ingredients_keys()

        # Відкриваємо файл один раз щоб перевірити наявні аркуші
        try:
            with pd.ExcelFile(excel_path) as xls:
                available_sheets = xls.sheet_names
                logger.info(f"📁 Доступні аркуші у файлі: {available_sheets}")
        except Exception as e:
            logger.error(f"❌ Помилка відкриття Excel файлу: {e}")
            raise DataImportError(f"Помилка відкриття файлу {excel_path}: {e}")

        # Перевірка відповідності клієнта
        if CONFIG_AVAILABLE and get_client_config is not None:
            try:
                current_client = get_client_config().client_id
                if current_client:
                    excel_client = self._get_client_id_from_excel(excel_path)
                    if excel_client:
                        if excel_client != current_client:
                            raise DataImportError(
                                f"Помилка: Невідповідність клієнта!\n\n"
                                f"Поточний клієнт: {current_client}\n"
                                f"Клієнт у файлі Excel: {excel_client}\n\n"
                                f"Будь ласка, переключіться на клієнта '{excel_client}' "
                                f"або виберіть правильний файл Excel."
                            )
                        else:
                            logger.info(f"✅ Клієнт перевірено: {current_client}")
                    else:
                        logger.warning(
                            f"⚠️ У файлі Excel не вказано клієнта. "
                            f"Очікувалося: {current_client}.\n"
                            f"Додайте ID клієнта в аркуш '{self.SHEET_APPLICATION}' "
                            f"(рядок {self.CLIENT_ID_ROW + 1}, колонка {self.CLIENT_ID_COL + 1})."
                        )
            except Exception as e:
                if isinstance(e, DataImportError):
                    raise
                logger.warning(f"Помилка перевірки клієнта: {e}")

        # Очищення довідників перед імпортом
        self._clear_dictionaries()

        # Іморт продукції
        stats["products"] = self._import_products(excel_path)

        # Імпорт стандартів
        stats["standards"] = self._import_standards(excel_path)

        # Імпорт потужностей
        stats["facilities"] = self._import_facilities(excel_path)

        # Імпорт складу
        stats["ingredients"] = self._import_ingredients(excel_path, existing_ingredients)

        # Імпорт заявки та партій
        app_data, parties_count = self._import_application(excel_path)
        if app_data:
            stats["applications"] = 1
            stats["parties"] = parties_count

        logger.info(
            f"✅ Імпорт завершено: "
            f"Продуктів: {stats['products']}, "
            f"Стандартів: {stats['standards']}, "
            f"Потужностей: {stats['facilities']}, "
            f"Складу: {stats['ingredients']}, "
            f"Заявок: {stats['applications']}, "
            f"Партій: {stats['parties']}, "
            f"Помилок: {stats['errors']}"
        )

        # Очищуємо кеші довідників після завершення імпорту
        try:
            from services.dictionary_service import DictionaryService
            DictionaryService.clear_all_caches()
        except Exception as e:
            logger.warning(f"Не вдалося очистити кеші після завершення імпорту: {e}")

        return stats

    def _get_client_id_from_excel(self, excel_path: str) -> Optional[str]:
        """
        Зчитати ID клієнта з Excel-файлу.
        Очікує ID в аркуші 'ЗАЯВКА', рядок 8 (індекс 7), колонка B (індекс 1).
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=self.SHEET_APPLICATION, header=None)
            if len(df) > self.CLIENT_ID_ROW:
                client_id = df.iloc[self.CLIENT_ID_ROW, self.CLIENT_ID_COL]
                if pd.notna(client_id):
                    return str(client_id).strip()
        except Exception as e:
            logger.warning(f"Не вдалося прочитати ID клієнта з Excel: {e}")
        return None

    def _get_existing_ingredients_keys(self) -> set:
        """Отримати набір ключів існуючих інгредієнтів для запобігання дублікатів"""
        keys = set()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT product_name, version, chemical_name, trade_mark, cas_number FROM ingredients"
                )
                for row in cursor.fetchall():
                    keys.add(tuple(row))
        except Exception as e:
            logger.warning(f"Помилка отримання існуючих інгредієнтів: {e}")
        return keys

    def _clear_dictionaries(self) -> None:
        """Очищення довідників перед імпортом"""
        tables = [
            "ingredients",
            "products",
            "standards",
            "production_facilities",
        ]
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                logger.info("🧹 Довідники очищено")

            # Також очищуємо кеші DictionaryService, оскільки дані в БД було видалено
            try:
                from services.dictionary_service import DictionaryService
                DictionaryService.clear_all_caches()
            except Exception as e:
                logger.warning(f"Не вдалося очистити кеші після очищення довідників: {e}")
        except DatabaseError:
            raise
        except Exception as e:
            raise DataImportError(f"Помилка очищення довідників: {e}") from e

    def _import_products(self, excel_path: str) -> int:
        """
        Іморт продукції з аркуша ДОВІДНИК_ПРОДУКЦІЯ.

        Args:
            excel_path: Шлях до Excel-файлу

        Returns:
            Кількість імпортованих продуктів
        """
        count = 0
        try:
            df = pd.read_excel(excel_path, sheet_name=self.SHEET_PRODUCTS, header=None)
            logger.info(f"📖 Знайдено аркуш '{self.SHEET_PRODUCTS}', рядків: {len(df)}")
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for i, row in df.iterrows():
                    try:
                        name = (
                            str(row.iloc[0]).strip()
                            if len(row) > 0 and pd.notna(row.iloc[0])
                            else ""
                        )
                        if not name or name.lower() == "nan":
                            continue

                        tu_code = (
                            str(row.iloc[1]).strip()
                            if len(row) > 1 and pd.notna(row.iloc[1])
                            else ""
                        )
                        shelf_life = (
                            int(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 36
                        )

                        cursor.execute(
                            "INSERT OR REPLACE INTO products (name, tu_code, shelf_life_months) VALUES (?, ?, ?)",
                            (name, tu_code, shelf_life),
                        )
                        if cursor.rowcount > 0:
                            count += 1
                    except Exception:
                        pass  # Рахуємо помилки окремо
        except Exception as e:
            logger.warning(f"Аркуш '{self.SHEET_PRODUCTS}' не знайдено: {e}")

        logger.info(f"📦 Імпортовано продуктів: {count}")
        return count

    def _import_standards(self, excel_path: str) -> int:
        """
        Імпорт стандартів з аркуша НД.

        Args:
            excel_path: Шлях до Excel-файлу

        Returns:
            Кількість імпортованих стандартів
        """
        count = 0
        try:
            df = pd.read_excel(excel_path, sheet_name=self.SHEET_STANDARDS, header=None)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    try:
                        if len(row) < 1 or pd.isna(row.iloc[0]):
                            continue

                        std_id = int(row.iloc[0])
                        description = (
                            str(row.iloc[1]).strip()
                            if len(row) > 1 and pd.notna(row.iloc[1])
                            else ""
                        )
                        if not description or description.lower() == "nan":
                            continue

                        cursor.execute(
                            "INSERT OR REPLACE INTO standards (id, description) VALUES (?, ?)",
                            (std_id, description),
                        )
                        if cursor.rowcount > 0:
                            count += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Аркуш '{self.SHEET_STANDARDS}' не знайдено: {e}")

        logger.info(f"📋 Імпортовано стандартів: {count}")
        return count

    def _import_facilities(self, excel_path: str) -> int:
        """
        Імпорт потужностей з аркуша ДОВІДНИК_ПОТУЖНОСТІ.

        Args:
            excel_path: Шлях до Excel-файлу

        Returns:
            Кількість імпортованих потужностей
        """
        count = 0
        try:
            df = pd.read_excel(excel_path, sheet_name=self.SHEET_FACILITIES, header=None)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    try:
                        address = (
                            str(row.iloc[0]).strip()
                            if len(row) > 0 and pd.notna(row.iloc[0])
                            else ""
                        )
                        if not address or address.lower() == "nan":
                            continue

                        cursor.execute(
                            "INSERT OR REPLACE INTO production_facilities (address) VALUES (?)",
                            (address,),
                        )
                        if cursor.rowcount > 0:
                            count += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Аркуш '{self.SHEET_FACILITIES}' не знайдено: {e}")

        logger.info(f"🏭 Імпортовано потужностей: {count}")
        return count

    def _import_ingredients(self, excel_path: str, existing_ingredients: set) -> int:
        """
        Імпорт складу з аркуша ДОВІДНИК_СКЛАД.

        Args:
            excel_path: Шлях до Excel-файлу

        Returns:
            Кількість імпортованих інгредієнтів
        """
        count = 0
        try:
            df = pd.read_excel(excel_path, sheet_name=self.SHEET_INGREDIENTS, header=None)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    try:
                        product_name = (
                            str(row.iloc[0]).strip()
                            if len(row) > 0 and pd.notna(row.iloc[0])
                            else ""
                        )
                        if not product_name or product_name.lower() == "nan":
                            continue

                        version = (
                            str(row.iloc[1]).strip()
                            if len(row) > 1 and pd.notna(row.iloc[1])
                            else ""
                        )
                        if version.lower() in ("none", "nan"):
                            version = ""

                        chemical_name = (
                            str(row.iloc[2]).strip()
                            if len(row) > 2 and pd.notna(row.iloc[2])
                            else ""
                        )
                        trade_mark = (
                            str(row.iloc[3]).strip()
                            if len(row) > 3 and pd.notna(row.iloc[3])
                            else ""
                        )
                        cas_number = (
                            str(row.iloc[4]).strip()
                            if len(row) > 4 and pd.notna(row.iloc[4])
                            else ""
                        )
                        certificate = (
                            str(row.iloc[5]).strip()
                            if len(row) > 5 and pd.notna(row.iloc[5])
                            else ""
                        )

                        # Створюємо ключ для перевірки дублікатів
                        key = (
                            product_name,
                            version,
                            chemical_name,
                            trade_mark,
                            cas_number,
                        )
                        if key in existing_ingredients:
                            continue

                        cursor.execute(
                            """
                            INSERT INTO ingredients
                            (product_name, version, chemical_name, trade_mark, cas_number, certificate)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                product_name,
                                version,
                                chemical_name,
                                trade_mark,
                                cas_number,
                                certificate,
                            ),
                        )
                        count += 1
                        existing_ingredients.add(key)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Аркуш '{self.SHEET_INGREDIENTS}' не знайдено: {e}")

        logger.info(f"🧪 Імпортовано інгредієнтів: {count}")
        return count

    def _parse_date(self, value) -> str:
        """Парсинг дати з Excel в рядок DD.MM.YYYY"""
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ""
            # Спробуємо розпарсити
            try:
                dt = datetime.strptime(value.split()[0], "%Y-%m-%d")
                return dt.strftime("%d.%m.%Y")
            except Exception:
                pass
            # Якщо формат "06.04.2026 р." -> "06.04.2026"
            match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
            if match:
                return f"{int(match.group(1)):02d}.{int(match.group(2)):02d}.{match.group(3)}"
            return value
        return str(value)

    def _parse_protocol_number(self, value: str) -> tuple[str, str]:
        """Розпарсити номер протоколу та дату з рядка '30157 від 06.04.2026 р.'"""
        if not value:
            return "", ""
        value = value.strip()
        # Шаблон: "30157 від 06.04.2026 р."
        # Дозволяємо дефіси та букви в номері (напр. 30137-26)
        match = re.match(r"([^від]+)\s*від\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
        if match:
            protocol_number = match.group(1)
            protocol_date = f"{int(match.group(2)):02d}.{int(match.group(3)):02d}.{match.group(4)}"
            return protocol_number, protocol_date
        return value, ""

    def _import_application(self, excel_path: str) -> tuple[dict, int]:
        """
        Імпорт заявки з аркуша ЗАЯВКА.

        Returns:
            (app_data, parties_count) - дані заявки та кількість партій
        """
        app_data = {}
        parties_count = 0

        try:
            df = pd.read_excel(excel_path, sheet_name=self.SHEET_APPLICATION, header=None)

            # Зчитуємо дані заявки
            # Row 1 (index 0): Номер заявки
            app_number = ""
            if len(df) > 0 and pd.notna(df.iloc[0, 1]):
                app_number = str(df.iloc[0, 1]).strip()

            # Row 2: Дата заявки
            app_date = ""
            if len(df) > 1 and pd.notna(df.iloc[1, 1]):
                app_date = self._parse_date(df.iloc[1, 1])

            # Row 3: Компания (колонки 0-6)
            company_name = ""
            company_address = ""
            if len(df) > 2:
                parts = []
                for col in range(7):
                    if pd.notna(df.iloc[2, col]):
                        parts.append(str(df.iloc[2, col]).strip())

                # Фільтруємо шаблонний текст
                template_texts = [
                    "назва підприємства",
                    "назвапідприємства",
                    "enterprise name",
                ]
                name_found = False
                for i, part in enumerate(parts):
                    if part.lower() not in template_texts:
                        company_name = part
                        company_address = ", ".join(parts[i + 1 :]) if len(parts) > i + 1 else ""
                        name_found = True
                        break

                if not name_found and parts:
                    company_name = parts[0]
                    company_address = ", ".join(parts[1:]) if len(parts) > 1 else ""

            # Row 4: ЄДРПОУ
            company_code = ""
            if len(df) > 3 and pd.notna(df.iloc[3, 1]):
                company_code = str(df.iloc[3, 1]).strip()

            # Row 5: Адреса потужностей
            production_address = ""
            if len(df) > 4:
                parts = []
                for col in range(7):
                    if pd.notna(df.iloc[4, col]):
                        parts.append(str(df.iloc[4, col]).strip())

                # Прибираємо шаблонні фрази з адреси
                address_templates = [
                    "адреса потужностей виробництва",
                    "адреса потужностей",
                    "production address",
                ]
                if parts and parts[0].lower() in address_templates:
                    production_address = ", ".join(parts[1:]) if len(parts) > 1 else ""
                else:
                    production_address = ", ".join(parts) if parts else ""

            # Row 6: ТУ
            tu_code = ""
            if len(df) > 5 and pd.notna(df.iloc[5, 1]):
                tu_code = str(df.iloc[5, 1]).strip()

            # Row 7: Директор + стандарти (колонка 4) — може бути кілька через кому
            director_name = ""
            standards = []
            if len(df) > 6:
                if pd.notna(df.iloc[6, 1]):
                    director_name = str(df.iloc[6, 1]).strip()
                # Колонка 4 може містити один або кілька номерів стандартів через кому
                if pd.notna(df.iloc[6, 4]):
                    std_raw = str(df.iloc[6, 4]).strip()
                    for part in std_raw.replace(";", ",").split(","):
                        part = part.strip()
                        if part.isdigit():
                            standards.append(int(part))

            app_data = {
                "app_number": app_number,
                "app_date": app_date,
                "company_name": company_name,
                "company_code": company_code,
                "company_address": company_address,
                "director_name": director_name,
                "tu_code": tu_code,
                "production_address": production_address,
                "standards": standards,
            }

            # Зчитуємо партії (рядки від 10)
            parties = []
            start_row = 9  # Row 9 - заголовки, дані від 10
            skipped_rows = 0

            for idx in range(start_row, len(df)):
                row = df.iloc[idx]
                try:
                    product_name = (
                        str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                    )

                    # Якщо немає назви продукції — це кінець списку або порожній рядок
                    if not product_name or product_name.lower() == "nan":
                        continue

                    # Колонка 2: № партії (якщо порожньо — ставимо "б/н")
                    party_num = row.iloc[2] if len(row) > 2 and pd.notna(row.iloc[2]) else "б/н"

                    party_code = str(party_num).strip()
                    party_date = self._parse_date(row.iloc[3]) if len(row) > 3 else ""
                    mfg_date = self._parse_date(row.iloc[4]) if len(row) > 4 else ""
                    # Колонка 5: Кількість (беремо як текст)
                    quantity = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else "0"

                    # Колонка 6: Протокол + Дата (напр. "30159 від 08.04.2026")
                    protocol_info = str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else ""
                    protocol_number, protocol_date = self._parse_protocol_number(protocol_info)

                    # Колонка 7: Версія складу (H)
                    version = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else ""
                    if version.lower() in ("none", "nan"):
                        version = ""

                    cert_number = (
                        str(row.iloc[8]).strip() if len(row) > 8 and pd.notna(row.iloc[8]) else ""
                    )
                    # Колонка 9: Дата сертифіката
                    cert_date = self._parse_date(row.iloc[9]) if len(row) > 9 else ""

                    parties.append(
                        {
                            "product_name": product_name,
                            "party_code": party_code,
                            "party_date": party_date,
                            "mfg_date": mfg_date,
                            "quantity": quantity,
                            "protocol_number": protocol_number,
                            "protocol_date": protocol_date,
                            "version": version,
                            "cert_number": cert_number,
                            "cert_date": cert_date,
                        }
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Помилка зчитування рядка {idx + 1}: {e}")
                    continue

            parties_count = len(parties)

            # Зберігаємо заявку та партії в БД
            if app_number and app_date:
                self._save_application_with_parties(app_data, parties)
                logger.info(f"✅ Імпортовано заявку {app_number} з {len(parties)} партіями")

            logger.info(f"📝 Імпортовано заявку {app_number} з {parties_count} партіями")

        except Exception as e:
            logger.warning(f"Аркуш '{self.SHEET_APPLICATION}' не знайдено або помилка: {e}")

        return app_data, parties_count

    def _save_application_with_parties(self, app_data: dict, parties: list) -> bool:
        """Зберегти заявку та партії в БД"""
        from models.dto import ApplicationDTO, PartyDTO

        app = ApplicationDTO(
            app_number=app_data["app_number"],
            app_date=app_data["app_date"],
            company_name=app_data["company_name"],
            company_code=app_data["company_code"],
            company_address=app_data["company_address"],
            director_name=app_data["director_name"],
            tu_code=app_data["tu_code"],
            production_address=app_data["production_address"],
        )

        # Стандарти беруться з заявки і прив'язуються до кожної партії
        app_standards = app_data.get("standards", [])

        party_dtos = []
        for p in parties:
            party = PartyDTO(
                product_name=p["product_name"],
                party_code=p["party_code"],
                party_date=p["party_date"],
                mfg_date=p["mfg_date"],
                quantity=p["quantity"],
                protocol_number=p["protocol_number"],
                protocol_date=p["protocol_date"],
                cert_number=p["cert_number"],
                cert_date=p["cert_date"],
                version=p.get("version", ""),
                standards=list(app_standards),  # передаємо стандарти заявки
            )
            party_dtos.append(party)

        # Використовуємо ApplicationService для збереження
        from services.application_service import ApplicationService

        app_service = ApplicationService(self.db_path)
        app_service.save_application_with_parties(app, party_dtos)

        logger.info(f"✅ Збережено заявку {app.app_number} та {len(party_dtos)} партій")
        return True
