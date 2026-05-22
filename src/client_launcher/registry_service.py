"""
Сервіс формування загального реєстру заявок.

Збирає дані з БД усіх заявників (кожен у своїй папці).
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    relativedelta = None

logger = logging.getLogger(__name__)


@dataclass
class RegistryEntry:
    """Один запис реєстру (одна партія однієї заявки)"""


    app_number_formatted: str = ""
    app_date: str = ""
    applicant_name: str = ""
    applicant_address: str = ""
    applicant_edrpou: str = ""
    product_name: str = ""
    manufacturer_name: str = ""
    manufacturer_address: str = ""
    protocol_number: str = ""
    protocol_date: str = ""
    cert_info: str = ""
    ugoda_number: str = ""
    _app_number_raw: str = ""
    _app_date: str = ""
    row_number: int = 0


class RegistryService:
    """Збір даних для реєстру заявок"""

    def __init__(self, root_dir: Path, data_dirs: Optional[List[Path]] = None):
        """
        Args:
            root_dir: Коренева директорія проекту (C:\\FINAL)
            data_dirs: Список директорій, що містять data/ (якщо None — використовується root_dir/data/)
        """
        self.root_dir = root_dir
        self.data_dirs = data_dirs if data_dirs else [root_dir]

    def collect_all_entries(self) -> List[RegistryEntry]:
        """Зібрати всі записи реєстру з усіх БД заявників"""
        from client_launcher.applicants_db import ApplicantsDB

        # Отримуємо всіх заявників
        launcher_db = ApplicantsDB()
        applicants = launcher_db.get_all_applicants()

        all_entries = []

        for applicant in applicants:
            entries = self._collect_from_applicant(applicant)
            all_entries.extend(entries)

        # Сортування: за номером заявки → за датою
        all_entries.sort(
            key=lambda e: (e._app_number_raw.zfill(5), self._parse_date(e._app_date))
        )

        # Пронумеруємо
        for i, entry in enumerate(all_entries, 1):
            entry.row_number = i

        return all_entries

    def _collect_from_applicant(self, applicant) -> List[RegistryEntry]:
        """Зібрати записи з БД одного заявника"""
        entries = []

        # Шукаємо БД заявника в кількох директоріях
        db_path = self._find_db_for_applicant(applicant.papka_proektu)

        if db_path is None:
            return entries

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Отримуємо всі заявки
            cursor.execute("""
                SELECT id, app_number, app_date, company_name, production_address
                FROM applications
                ORDER BY app_number
            """)
            applications = cursor.fetchall()

            for app in applications:
                app_id = app["id"]
                app_number = app["app_number"]
                app_date = app["app_date"]
                app["company_name"]
                production_address = app["production_address"]

                # Отримуємо партії цієї заявки
                cursor.execute(
                    """
                    SELECT p.id, p.party_number, p.product_name, p.party_code,
                           p.party_date, p.mfg_date, p.quantity, p.unit,
                           p.protocol_number, p.protocol_date,
                           p.cert_number, p.cert_date, p.shelf_life_months, p.version
                    FROM parties p
                    WHERE p.application_id = ?
                    ORDER BY p.party_number
                """,
                    (app_id,),
                )
                parties = cursor.fetchall()

                # Отримуємо виробника за адресою
                manufacturer_name = ""
                manufacturer_address = production_address or ""

                if production_address:
                    cursor.execute(
                        """
                        SELECT company_name, address
                        FROM production_facilities
                        WHERE address = ?
                    """,
                        (production_address,),
                    )
                    facility = cursor.fetchone()
                    if facility:
                        manufacturer_name = facility["company_name"] or ""
                        # Якщо назва порожня, спробуємо витягнути щось з адреси
                        if not manufacturer_name:
                             # Можливо перша частина адреси до коми це назва?
                             parts = manufacturer_address.split(',')
                             if parts:
                                 manufacturer_name = parts[0].strip()
                    else:
                        # Якщо в довіднику немає — беремо адресу як назву (fallback)
                        parts = manufacturer_address.split(',')
                        manufacturer_name = parts[0].strip() if parts else manufacturer_address

                # Форматуємо номер заявки: 114/0XXX ТРП
                app_number_formatted = self._format_app_number(app_number)

                # Форматуємо номер угоди: 114/XXX-ГГ від ДД.ММ.РРРР
                ugoda_number = self._format_ugoda_number(app_number, app_date)

                for party in parties:
                    # Формуємо інформацію про сертифікат
                    cert_number = party["cert_number"] or ""
                    cert_date = party["cert_date"] or ""
                    shelf_life = party["shelf_life_months"] or 36

                    cert_info = ""
                    if cert_number:
                        cert_info = f"№ {cert_number}"
                        if cert_date:
                            cert_info += f" від {cert_date}"
                        # Рассчитаем expiry из mfg_date + shelf_life_months
                        mfg = party["mfg_date"] or ""
                        if mfg and relativedelta:
                            try:
                                dt_mfg = datetime.strptime(mfg.strip(), "%d.%m.%Y")
                                dt_expiry = dt_mfg + relativedelta(months=shelf_life)
                                cert_info += (
                                    f", діє до {dt_expiry.strftime('%d.%m.%Y')}"
                                )
                            except Exception:
                                pass

                    entry = RegistryEntry(
                        app_number_formatted=app_number_formatted,
                        app_date=app_date,
                        applicant_name=applicant.nazva_pidpryyemstva,
                        applicant_address=applicant.adresa_pidpryyemstva,
                        applicant_edrpou=applicant.kod_edrpou,
                        product_name=party["product_name"] or "",
                        manufacturer_name=manufacturer_name,
                        manufacturer_address=manufacturer_address,
                        protocol_number=party["protocol_number"] or "",
                        protocol_date=party["protocol_date"] or "",
                        cert_info=cert_info,
                        ugoda_number=ugoda_number,
                        _app_number_raw=app_number,
                        _app_date=app_date,
                    )
                    entries.append(entry)

            conn.close()

        except Exception as e:
            logger.error(
                f"Помилка збору даних для {applicant.nazva_pidpryyemstva}: {e}"
            )

        return entries

    def _find_db_for_applicant(self, papka_proektu: str) -> Optional[Path]:
        """
        Знайти БД certify.db для даного заявника в кількох директоріях.

        Шукає: {base_dir}/data/{papka_proektu}/certify.db
        """
        for base_dir in self.data_dirs:
            # 1. Пробуємо стандартний шлях: data/АФІНА/certify.db
            path_standard = base_dir / "data" / papka_proektu / "certify.db"
            
            # 2. Пробуємо застарілий шлях: АФІНА/data/certify.db
            path_legacy = base_dir / papka_proektu / "data" / "certify.db"

            # Логіка як у config.py: якщо стандартної НЕМАЄ, але є стара — беремо стару.
            # Якщо є обидві — стандартна має пріоритет.
            if path_standard.exists():
                return path_standard
            if path_legacy.exists():
                return path_legacy
        return None

    def _format_app_number(self, app_number: str) -> str:
        """Форматування номера заявки: 038 → 114/0038 ТРП"""
        # Забезпечуємо 3 цифри
        num = app_number.strip()
        try:
            num_int = int(num)
            formatted_num = str(num_int).zfill(4)
        except ValueError:
            formatted_num = num

        return f"114/{formatted_num} ТРП"

    def _format_ugoda_number(self, app_number: str, app_date: str) -> str:
        """Форматування номера угоди: 114/XXX-ГГ від ДД.ММ.РРРР"""
        num = app_number.strip()
        try:
            num_int = int(num)
            formatted_num = str(num_int)
        except ValueError:
            formatted_num = num

        # Рік з дати заявки
        year_short = ""
        if app_date:
            try:
                dt = datetime.strptime(app_date.strip(), "%d.%m.%Y")
                year_short = str(dt.year)[-2:]
            except ValueError:
                year_short = "XX"

        ugoda_base = f"114/{formatted_num}-{year_short}"

        if app_date:
            return f"{ugoda_base} від {app_date}"
        return ugoda_base

    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг дати для сортування"""
        try:
            return datetime.strptime(date_str.strip(), "%d.%m.%Y")
        except (ValueError, AttributeError):
            return datetime.min
