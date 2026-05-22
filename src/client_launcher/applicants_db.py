"""
База даних реєстру заявників (клієнтів).

Міститься ЗА межами папок клієнтів — спільна для всіх.
"""

import logging
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Визначаємо шлях до БД:
# - у режимі .exe: папка де лежить launcher.exe (стала між запусками)
# - у режимі Python: папка client_launcher/data/ (як раніше)
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).parent

DB_PATH = _BASE_DIR / "data" / "applicants.db"

# Валідація ЄДРПОУ: 8 цифр для юросіб, 10 для ФОП
_EDRPOU_PATTERN = re.compile(r"^\d{8,10}$")


@dataclass
class ApplicantDTO:
    """DTO заявника (клієнта)"""

    id: int = 0
    nazva_pidpryyemstva: str = ""
    adresa_pidpryyemstva: str = ""
    kod_edrpou: str = ""
    kerivnik: str = ""
    papka_proektu: str = ""  # Відносний або абсолютний шлях до папки проекту
    template_suffix: str = "_Д"  # Суфікс для шаблонів (напр. _А, _Д, _П)


class ApplicantsDB:
    """Робота з БД реєстру заявників"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Створення таблиці та міграції"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Створюємо таблицю з UNIQUE constraint на kod_edrpou
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zayavniky (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazva_pidpryyemstva TEXT NOT NULL,
                adresa_pidpryyemstva TEXT NOT NULL,
                kod_edrpou TEXT NOT NULL UNIQUE,
                kerivnik TEXT NOT NULL,
                papka_proektu TEXT NOT NULL,
                template_suffix TEXT DEFAULT '_Д'
            )
        """)

        # Міграція: додаємо UNIQUE constraint для існуючих БД
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_zayavniky_edrpou
            ON zayavniky(kod_edrpou)
        """)

        # Міграція: додаємо колонку template_suffix якщо її немає
        try:
            cursor.execute("ALTER TABLE zayavniky ADD COLUMN template_suffix TEXT DEFAULT '_Д'")
            logger.info("✅ Міграція: додано колонку template_suffix в таблицю zayavniky")
        except sqlite3.OperationalError:
            # Колонка вже існує
            pass

        conn.commit()

        # Перевіряємо чи є вже дані
        cursor.execute("SELECT COUNT(*) FROM zayavniky")
        count = cursor.fetchone()[0]

        if count == 0:
            # Додаємо заявників за замовчуванням
            default_applicants = [
                (
                    "ТОВ «АФІНА-ГРУП»",
                    "Запорізьке шосе, буд. 37, м. Дніпро, ДНІПРОПЕТРОВСЬКА ОБЛ., 49000, Україна",
                    "33324489",
                    "А. О. Жован",
                    "АФІНА",
                ),
                (
                    'ТОВ "СК ДЖОНСОН»',
                    "Україна, 04073, м. Київ, пр-т Степана Бандери, 19-Б",
                    "00146137",
                    "К.Я. Шевчук",
                    "ДЖОНСОН",
                ),
            ]

            cursor.executemany(
                """INSERT INTO zayavniky
                   (nazva_pidpryyemstva, adresa_pidpryyemstva, kod_edrpou, 
                    kerivnik, papka_proektu, template_suffix)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (a[0], a[1], a[2], a[3], a[4], "_А" if "АФІНА" in a[0] else "_Д")
                    for a in default_applicants
                ],
            )

        conn.commit()
        conn.close()

    @staticmethod
    def validate_edrpou(code: str) -> Tuple[bool, str]:
        """
        Валідація коду ЄДРПОУ.

        Args:
            code: Код для перевірки

        Returns:
            (True, "") якщо валідний, (False, "причина") якщо ні
        """
        if not code:
            return False, "Код ЄДРПОУ порожній"

        if not _EDRPOU_PATTERN.match(code):
            return False, "ЄДРПОУ має містити 8 цифр (юрособа) або 10 цифр (ФОП)"

        return True, ""

    def get_all_applicants(self) -> List[ApplicantDTO]:
        """Отримати всіх заявників"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM zayavniky ORDER BY nazva_pidpryyemstva")
        rows = cursor.fetchall()

        result = [
            ApplicantDTO(
                id=row["id"],
                nazva_pidpryyemstva=row["nazva_pidpryyemstva"],
                adresa_pidpryyemstva=row["adresa_pidpryyemstva"],
                kod_edrpou=row["kod_edrpou"],
                kerivnik=row["kerivnik"],
                papka_proektu=row["papka_proektu"],
                template_suffix=row["template_suffix"] if "template_suffix" in row.keys() else "_Д",
            )
            for row in rows
        ]

        conn.close()
        return result

    def get_applicant_by_id(self, applicant_id: int) -> Optional[ApplicantDTO]:
        """Отримати заявника за ID"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM zayavniky WHERE id = ?", (applicant_id,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return None

        result = ApplicantDTO(
            id=row["id"],
            nazva_pidpryyemstva=row["nazva_pidpryyemstva"],
            adresa_pidpryyemstva=row["adresa_pidpryyemstva"],
            kod_edrpou=row["kod_edrpou"],
            kerivnik=row["kerivnik"],
            papka_proektu=row["papka_proektu"],
            template_suffix=row["template_suffix"] if "template_suffix" in row.keys() else "_Д",
        )

        conn.close()
        return result

    def add_applicant(
        self, applicant: ApplicantDTO, auto_provision: bool = True
    ) -> int:
        """
        Додати нового заявника.

        Args:
            applicant: Дані заявника
            auto_provision: Якщо True — автоматично створити інфраструктуру
                           (папки, БД, реєстрація в profiles.yaml)

        Returns:
            ID нового заявника

        Raises:
            sqlite3.IntegrityError: якщо ЄДРПОУ вже існує
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute(
                """INSERT INTO zayavniky
                   (nazva_pidpryyemstva, adresa_pidpryyemstva, kod_edrpou, 
                    kerivnik, papka_proektu, template_suffix)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    applicant.nazva_pidpryyemstva,
                    applicant.adresa_pidpryyemstva,
                    applicant.kod_edrpou,
                    applicant.kerivnik,
                    applicant.papka_proektu,
                    applicant.template_suffix or "_Д",
                ),
            )

            applicant_id = cursor.lastrowid
            conn.commit()
            logger.info(
                f"Додано заявника: {applicant.nazva_pidpryyemstva} (ID={applicant_id})"
            )

            # ─── Автоматична ініціалізація інфраструктури клієнта ───
            if auto_provision:
                self._provision_client_infrastructure(
                    papka_proektu=applicant.papka_proektu,
                    company_name=applicant.nazva_pidpryyemstva,
                    company_code=applicant.kod_edrpou,
                    director=applicant.kerivnik,
                    applicant_id=applicant_id,
                    template_suffix=applicant.template_suffix,
                )

            return applicant_id

        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint" in str(e) or "idx_zayavniky_edrpou" in str(e):
                raise sqlite3.IntegrityError(
                    f"Заявник з ЄДРПОУ '{applicant.kod_edrpou}' вже існує"
                ) from e
            raise

        finally:
            conn.close()

    def _provision_client_infrastructure(
        self,
        papka_proektu: str,
        company_name: str,
        company_code: str,
        director: str,
        applicant_id: int,
        template_suffix: str = "_Д",
    ) -> None:
        """
        Створити інфраструктуру нового клієнта (папки, БД, profiles.yaml).

        При помилці — видаляє запис з applicants.db (відкат).
        """
        from client_launcher.client_provisioner import provision_new_client

        logger.info(f"🔧 Ініціалізація інфраструктури для клієнта: {papka_proektu}")

        result = provision_new_client(
            papka_proektu=papka_proektu,
            company_name=company_name,
            company_code=company_code,
            director=director,
            template_suffix=template_suffix,
        )

        if not result.success:
            # Відкат: видаляємо запис з БД заявників
            logger.error(
                f"❌ Помилка ініціалізації інфраструктури: {result.errors}. "
                f"Відкат — видалення заявника ID={applicant_id}"
            )
            self.delete_applicant(applicant_id)

            raise RuntimeError(
                f"Не вдалося створити інфраструктуру для '{papka_proektu}':\n"
                + "\n".join(f"  • {e}" for e in result.errors)
            )

        if result.warnings:
            for warn in result.warnings:
                logger.warning(f"⚠️ {warn}")

        logger.info(
            f"✅ Інфраструктура створена: {result.data_dir}, БД: {result.db_path}"
        )

    def update_applicant(self, applicant: ApplicantDTO) -> bool:
        """Оновити дані заявника"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE zayavniky SET
                nazva_pidpryyemstva = ?,
                adresa_pidpryyemstva = ?,
                kod_edrpou = ?,
                kerivnik = ?,
                papka_proektu = ?,
                template_suffix = ?
               WHERE id = ?""",
            (
                applicant.nazva_pidpryyemstva,
                applicant.adresa_pidpryyemstva,
                applicant.kod_edrpou,
                applicant.kerivnik,
                applicant.papka_proektu,
                applicant.template_suffix or "_Д",
                applicant.id,
            ),
        )

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_applicant(self, applicant_id: int, delete_folder: bool = False) -> bool:
        """
        Видалити заявника.

        Args:
            applicant_id: ID заявника
            delete_folder: Якщо True — також видаляє папку проекту

        Returns:
            True якщо видалено
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Спочатку читаємо papka_proektu якщо потрібно видалити папку
            papka_proektu = None
            if delete_folder:
                cursor.execute(
                    "SELECT papka_proektu FROM zayavniky WHERE id = ?", (applicant_id,)
                )
                row = cursor.fetchone()
                if row:
                    papka_proektu = row["papka_proektu"]

            # Видаляємо запис
            cursor.execute("DELETE FROM zayavniky WHERE id = ?", (applicant_id,))
            affected = cursor.rowcount
            conn.commit()

            # Видаляємо папку проекту якщо потрібно
            if delete_folder and papka_proektu and affected > 0:
                self._delete_client_folder(papka_proektu)

            return affected > 0

        finally:
            conn.close()

    def _delete_client_folder(self, papka_proektu: str) -> None:
        """
        Видалити папку проекту клієнта.

        Шукає папку:
        1. Поруч з launcher.exe (у frozen режимі)
        2. У корені проекту (у режимі розробки)
        """
        import shutil

        # Визначаємо базову директорію
        if getattr(sys, "frozen", False):
            # Режим .exe: папка поруч з launcher.exe
            base_dir = Path(sys.executable).parent
        else:
            # Режим вихідного коду: корінь проекту
            base_dir = Path(__file__).parent.parent

        client_dir = base_dir / papka_proektu

        if client_dir.exists():
            try:
                shutil.rmtree(str(client_dir))
                logger.info(f"🗑️ Видалено папку клієнта: {client_dir}")
            except Exception as e:
                logger.error(f"❌ Не вдалося видалити папку {client_dir}: {e}")
        else:
            logger.warning(f"⚠️ Папка клієнта не знайдена: {client_dir}")
