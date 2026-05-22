"""
client_provisioner.py — Автоматическая инициализация нового клиента CertifyPro.

При добавлении нового заявителя через лаунчер этот модуль:
  1. Создаёт структуру папок: data/<papka_proektu>/, data/<papka_proektu>/Documents/
  2. Создаёт пустую БД certify.db из единой SQL-схемы
  3. Регистрирует клиента в profiles.yaml
  4. Копирует базовые шаблоны (опционально)
  5. Выполняет откат при ошибке

Использование:
    from client_launcher.client_provisioner import provision_new_client, ProvisionResult

    result = provision_new_client(
        papka_proektu="НОВИЙ_КЛІЄНТ",
        company_name='ТОВ "НОВИЙ"',
        company_code="12345678",
        director="І. І. Іванов",
    )

    if result.success:
        logger.info(f"Клиент создан: {result.db_path}")
    else:
        logger.error(f"Ошибки при создании клиента: {result.errors}")
"""

import logging
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ─── Пути ───────────────────────────────────────────────────────────────
# Визначаємо базову директорію проекту (працює і для .exe, і для Python)
# Це ТА САМА логіка що й у config.py та launcher.py
if getattr(sys, "frozen", False):
    # Режим .exe: використовуємо папку де лежить launcher.exe
    _PROJECT_ROOT = Path(sys.executable).parent
else:
    # Режим вихідного коду: parent папки client_launcher
    _PROJECT_ROOT = Path(__file__).parent.parent

# Профили клиентов
if getattr(sys, "frozen", False):
    _PROFILES_PATH = _PROJECT_ROOT / "resources" / "profiles.yaml"
else:
    _PROFILES_PATH = _PROJECT_ROOT / "CERTIFYPRO" / "resources" / "profiles.yaml"

# SQL-схема БД (у режимі .exe шукаємо в _MEIPASS, інакше — у вихідному коді)
if getattr(sys, "frozen", False):
    _DB_SCHEMA_PATH = (
        Path(sys._MEIPASS) / "CERTIFYPRO" / "core" / "database" / "db_schema.sql"
    )
else:
    _DB_SCHEMA_PATH = (
        _PROJECT_ROOT / "CERTIFYPRO" / "core" / "database" / "db_schema.sql"
    )

# Шаблоны документов
if getattr(sys, "frozen", False):
    _TEMPLATES_SOURCE = Path(sys._MEIPASS) / "resources" / "templates"
else:
    _TEMPLATES_SOURCE = _PROJECT_ROOT / "CERTIFYPRO" / "resources" / "templates"


@dataclass
class ProvisionResult:
    """Результат инициализации клиента."""

    success: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    papka_proektu: str = ""
    data_dir: Optional[Path] = None
    db_path: Optional[Path] = None
    profile_added: bool = False


# ─── Главная функция ─────────────────────────────────────────────────────


def provision_new_client(
    papka_proektu: str,
    company_name: str,
    company_code: str,
    director: str,
    base_dir: Optional[Path] = None,
    template_suffix: str = "_Д",
    import_product: bool = False,
    ugoda_templates: int = 1,
) -> ProvisionResult:
    """
    Полная инициализация нового клиента.

    Args:
        papka_proektu: Имя папки клиента (как в applicants.db)
        company_name: Название компании
        company_code: Код ЕДРПОУ
        director: ФИО руководителя
        base_dir: Базовая директория (по умолчанию = PROJECT_ROOT)
        template_suffix: Суффикс шаблонов ("_А", "_Д")
        import_product: Флаг импортной продукции
        ugoda_templates: Количество шаблонов угоды (1 или 2)

    Returns:
        ProvisionResult с информацией об успехе/ошибках
    """
    result = ProvisionResult(papka_proektu=papka_proektu)

    if base_dir is None:
        base_dir = _PROJECT_ROOT

    logger.info(f"🔧 Начинаю инициализацию клиента: {papka_proektu}")

    try:
        # Шаг 1: Создание папок (data/papka_proektu)
        logger.info(f"📁 Шаг 1: Создание папок в data/{papka_proektu}")
        data_dir = base_dir / "data" / papka_proektu
        _create_client_dirs(data_dir, result)
        if not result.success:
            return result

        # Шаг 2: Инициализация пустой БД
        logger.info(f"💾 Шаг 2: Инициализация БД в {data_dir / 'certify.db'}")
        db_path = data_dir / "certify.db"
        _init_empty_db(db_path, result)
        if not result.success:
            # Откат: удаляем папки
            _rollback_created_dirs(data_dir)
            return result

        # Шаг 3: Регистрация в profiles.yaml
        logger.info(f"📝 Шаг 3: Регистрация {papka_proektu} в profiles.yaml")
        _register_in_profiles(
            papka_proektu,
            company_name,
            company_code,
            director,
            template_suffix,
            import_product,
            ugoda_templates,
            result,
        )
        # Ошибка регистрации — не критичная, не откатываем

        # Шаг 3.1: Копирование шаблонов
        logger.info(f"📄 Шаг 3.1: Копирование шаблонов для {papka_proektu} (суффикс: {template_suffix})")
        _copy_base_templates(data_dir, template_suffix, result)
        # Ошибка копирования — предупреждение, не откатываем

        # Шаг 4: Заполнение справочников данными клиента
        logger.info(f"📚 Шаг 4: Заполнение справочников для {papka_proektu}")
        _populate_client_dictionaries(
            db_path, company_name, company_code, director, result
        )
        # Ошибка заполнения справочников — предупреждение, не откатываем

        result.success = True
        result.data_dir = data_dir
        result.db_path = db_path

        logger.info(f"✅ Клиент '{papka_proektu}' успешно инициализирован")
        logger.info(f"   Папка: {data_dir}")
        logger.info(f"   БД: {db_path}")
        logger.info(f"   Профиль в YAML: {result.profile_added}")

    except Exception as e:
        result.success = False
        result.errors.append(f"Неожиданная ошибка: {str(e)}")
        logger.exception(f"❌ Критическая ошибка при инициализации {papka_proektu}")

    return result


# ─── Шаг 1: Создание папок ───────────────────────────────────────────────


def _create_client_dirs(data_dir: Path, result: ProvisionResult) -> None:
    """
    Создать структуру папок для клиента.

    Структура:
        <papka_proektu>/
        └── data/
            ├── certify.db       (создаётся на шаге 2)
            └── Documents/       (для сгенерированных документов)
    """
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        docs_dir = data_dir / "Documents"
        docs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"✅ Папки созданы: {data_dir}")
        result.data_dir = data_dir
        result.success = True  # ✅ Явно устанавливаем успех!

    except OSError as e:
        result.errors.append(f"Не удалось создать папку {data_dir}: {e}")
        result.success = False
        logger.error(f"❌ Ошибка создания папок: {e}")


def _rollback_created_dirs(data_dir: Path) -> None:
    """
    Откат: удалить созданную структуру папок при ошибке.

    Удаляет всю папку клиента: <papka_proektu>/ (включая data/ и Documents/)
    """
    try:
        client_root = data_dir.parent  # <papka_proektu>/
        if client_root.exists():
            shutil.rmtree(str(client_root))
            logger.info(f"🔄 Откат: удалена папка {client_root}")
    except Exception as e:
        logger.error(f"⚠️ Не удалось выполнить откат папок: {e}")


# ─── Шаг 2: Инициализация пустой БД ──────────────────────────────────────


def _init_empty_db(db_path: Path, result: ProvisionResult) -> None:
    """
    Создать пустую БД certify.db из SQL-схемы.

    Использует единый файл схемы: CERTIFYPRO/core/database/db_schema.sql
    """
    logger.info(f"  🔍 Схема: {_DB_SCHEMA_PATH}")
    logger.info(f"  🔍 Схема существует: {_DB_SCHEMA_PATH.exists()}")
    logger.info(f"  🔍 Целевая БД: {db_path}")
    logger.info(f"  🔍 frozen режим: {getattr(sys, 'frozen', False)}")
    if getattr(sys, "frozen", False):
        logger.info(f"  🔍 _MEIPASS: {sys._MEIPASS}")

    if not _DB_SCHEMA_PATH.exists():
        error_msg = (
            f"Файл SQL-схемы не найден: {_DB_SCHEMA_PATH}. "
            f"Текущая директория: {Path.cwd()}. "
            f"Система ищет в: {_PROJECT_ROOT}. "
            "БД не может быть инициализирована."
        )
        result.errors.append(error_msg)
        result.success = False  # Явно устанавливаем failure
        logger.error(f"❌ {error_msg}")
        return

    try:
        # Читаем SQL-схему
        with open(_DB_SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        logger.info(f"  Схема прочитана: {len(schema_sql)} байт")

        # Создаём БД и выполняем схему
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Включаем внешние ключи
        cursor.execute("PRAGMA foreign_keys = ON")

        # Выполняем весь SQL
        cursor.executescript(schema_sql)

        conn.commit()
        conn.close()

        # Проверяем что таблицы созданы
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        logger.info(f"✅ БД создана. Таблицы: {tables}")
        result.db_path = db_path
        result.success = True  # ✅ Успех!

        if len(tables) < 6:
            result.warnings.append(
                f"БД содержит только {len(tables)} таблиц (ожидалось 6)"
            )

    except sqlite3.Error as e:
        result.errors.append(f"Ошибка инициализации БД: {e}")
        result.success = False
        logger.error(f"❌ Ошибка создания БД: {e}")
        import traceback

        logger.error(traceback.format_exc())
    except OSError as e:
        result.errors.append(f"Не удалось прочитать SQL-схему: {e}")
        result.success = False
        logger.error(f"❌ Ошибка чтения схемы: {e}")
        import traceback

        logger.error(traceback.format_exc())


# ─── Шаг 3: Регистрация в profiles.yaml ──────────────────────────────────


def _register_in_profiles(
    papka_proektu: str,
    company_name: str,
    company_code: str,
    director: str,
    template_suffix: str,
    import_product: bool,
    ugoda_templates: int,
    result: ProvisionResult,
) -> None:
    """
    Добавить нового клиента в profiles.yaml.

    Если файл не существует — создаёт его с нуля.
    Если клиент уже есть — пропускает.
    """
    try:
        import yaml

        logger.info(f"  Профили: {_PROFILES_PATH} (exists={_PROFILES_PATH.exists()})")

        profiles_data = {}

        # Читаем существующий файл
        if _PROFILES_PATH.exists():
            with open(_PROFILES_PATH, "r", encoding="utf-8") as f:
                profiles_data = yaml.safe_load(f) or {}
            logger.info(
                f"  Прочитано profiles.yaml, клиентов: {len(profiles_data.get('clients', {}))}"
            )

        # Убеждаемся что секция clients существует
        if "clients" not in profiles_data:
            profiles_data["clients"] = {}

        # Генерируем client_id из papka_proektu (транслитерация)
        client_id = _transliterate(papka_proektu).lower()
        logger.info(f"  Client ID (транслит): {client_id}")

        # Проверяем что клиента ещё нет
        if client_id in profiles_data["clients"]:
            result.warnings.append(f"Клиент '{client_id}' уже есть в profiles.yaml")
            result.profile_added = False
            return

        # Формируем profile
        profile = {
            "name": papka_proektu,
            "display_name": company_name,
            "template_suffix": template_suffix,
            "launcher_mapping": papka_proektu,
            "company": {
                "name": company_name,
                "code": company_code,
                "director": director,
            },
            "features": {
                "import_product": import_product,
                "ugoda_templates": ugoda_templates,
            },
            "data_dir": f"data/{papka_proektu}",
            "description": f"Клієнт {papka_proektu} (авто-створено)",
        }

        profiles_data["clients"][client_id] = profile
        logger.info(f"  Добавлен профиль для {client_id}")

        # Сохраняем (атомарно: записываем во временный → переименовываем)
        logger.info("  Сохраняю profiles.yaml...")
        _save_yaml_atomic(profiles_data)
        logger.info("  profiles.yaml сохранён")

        result.profile_added = True
        logger.info(f"✅ Клиент '{client_id}' добавлен в profiles.yaml")

    except ImportError:
        result.warnings.append(
            "Модуль PyYAML не установлен. Клиент не зарегистрирован в profiles.yaml. "
            "Установите: pip install pyyaml"
        )
        logger.warning("⚠️ PyYAML недоступен — profiles.yaml не обновлён")
    except Exception as e:
        result.warnings.append(f"Ошибка записи profiles.yaml: {e}")
        logger.error(f"❌ Ошибка записи profiles.yaml: {e}")
        import traceback

        logger.error(traceback.format_exc())


def _save_yaml_atomic(data: dict) -> None:
    """
    Атомарная записи YAML: сначала во временный файл, потом переименование.

    Это предотвращает повреждение файла при сбое записи.
    """
    import yaml

    tmp_path = _PROFILES_PATH.with_suffix(".yaml.tmp")

    # Записываем во временный файл
    with open(tmp_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    # Атомарне перейменування (os.replace працює атомарно на Windows)
    import os

    os.replace(tmp_path, _PROFILES_PATH)


# ─── Шаг 3.1: Копирование шаблонов ───────────────────────────────────────


def _copy_base_templates(data_dir: Path, template_suffix: str, result: ProvisionResult) -> None:
    """
    Скопировать базовые шаблоны из центральной папки и переименовать под суффикс клиента.
    """
    try:
        dest_templates_dir = data_dir / "templates"
        dest_templates_dir.mkdir(parents=True, exist_ok=True)

        if not _TEMPLATES_SOURCE.exists():
            result.warnings.append(f"Центральна папка шаблонів не знайдена: {_TEMPLATES_SOURCE}")
            return

        # Ищем шаблоны с суффиксом _Д (базовые)
        base_suffix = "_Д"
        copied_count = 0

        for src_file in _TEMPLATES_SOURCE.glob(f"*{base_suffix}.doc*"):
            # Формируем новое имя: заменяем _Д на новый суффикс
            new_name = src_file.name.replace(base_suffix, template_suffix)
            dest_file = dest_templates_dir / new_name

            shutil.copy2(src_file, dest_file)
            copied_count += 1

        logger.info(f"✅ Скопійовано {copied_count} шаблонів у {dest_templates_dir}")
        if copied_count == 0:
            result.warnings.append(f"Не знайдено базових шаблонів (з {base_suffix}) для копіювання")

    except Exception as e:
        result.warnings.append(f"Помилка копіювання шаблонів: {e}")
        logger.warning(f"⚠️ Помилка копіювання шаблонів: {e}")


# ─── Шаг 4: Заполнение справочников ───────────────────────────────────────


def _populate_client_dictionaries(
    db_path: Path,
    company_name: str,
    company_code: str,
    director: str,
    result: ProvisionResult,
) -> None:
    """
    Заполнить справочники certify.db начальными данными клиента.

    Добавляет:
    - Адрес компании в production_facilities
    - Пустую запись продукта чтобы ТУ не был пустым
    """
    try:
        import sqlite3

        logger.info(f"  Заполняю справочники в {db_path}")

        if not db_path.exists():
            result.warnings.append(
                "БД certify.db не найдена для заполнения справочников"
            )
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 1. Добавляем адрес компании в production_facilities
        # Используем название компании как адрес (можно потом редактировать)
        cursor.execute(
            "INSERT OR IGNORE INTO production_facilities (address, company_name) VALUES (?, ?)",
            (company_name, company_name),
        )
        logger.info(f"  Добавлен адрес в потужности: {company_name}")

        # 2. Добавляем пример продукта если таблица пустая
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        if product_count == 0:
            # Вставляем пустную запись чтобы пользователь понимал структуру
            cursor.execute(
                "INSERT INTO products (name, tu_code, shelf_life_months) VALUES (?, ?, ?)",
                ("Приклад продукції", "ТУ 1.0.0", 36),
            )
            logger.info("  Добавлен пример продукта")

        conn.commit()
        conn.close()

        logger.info("✅ Справочники заполнены успешно")

    except Exception as e:
        result.warnings.append(f"Ошибка заполнения справочников: {e}")
        logger.warning(f"⚠️ Ошибка заполнения справочников: {e}")


# ─── Утилиты ─────────────────────────────────────────────────────────────


def _transliterate(text: str) -> str:
    """
    Транслитерация украинского/русского текста в латиницу.

    Пример: "НОВИЙ_КЛІЄНТ" → "NOVYJ_KLIENT"
    """
    translit_map = {
        "А": "A",
        "Б": "B",
        "В": "V",
        "Г": "H",
        "Ґ": "G",
        "Д": "D",
        "Е": "E",
        "Є": "YE",
        "Ж": "ZH",
        "З": "Z",
        "И": "Y",
        "І": "I",
        "Ї": "YI",
        "Й": "Y",
        "К": "K",
        "Л": "L",
        "М": "M",
        "Н": "N",
        "О": "O",
        "П": "P",
        "Р": "R",
        "С": "S",
        "Т": "T",
        "У": "U",
        "Ф": "F",
        "Х": "KH",
        "Ц": "TS",
        "Ч": "CH",
        "Ш": "SH",
        "Щ": "SHCH",
        "Ь": "",
        "Ю": "YU",
        "Я": "YA",
        "Ы": "Y",
        "Э": "E",
        "Ъ": "",
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "h",
        "ґ": "g",
        "д": "d",
        "е": "e",
        "є": "ye",
        "ж": "zh",
        "з": "z",
        "и": "y",
        "і": "i",
        "ї": "yi",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ь": "",
        "ю": "yu",
        "я": "ya",
        "ы": "y",
        "э": "e",
        "ъ": "",
        '"': "",
        "«": "",
        "»": "",
        " ": "_",
        "/": "_",
        "\\": "_",
    }

    result = []
    for char in text:
        result.append(translit_map.get(char, char))

    # Уданяем подряд идущие подчёркивания
    transliterated = "".join(result)
    while "__" in transliterated:
        transliterated = transliterated.replace("__", "_")
    transliterated = transliterated.strip("_")

    return transliterated


def check_client_provisioned(
    papka_proektu: str, base_dir: Optional[Path] = None
) -> dict:
    """
    Проверить состояние инициализации клиента.

    Returns:
        {
            "dir_exists": True/False,
            "db_exists": True/False,
            "db_tables": [...],
            "in_profiles": True/False,
            "client_id": "...",
        }
    """
    if base_dir is None:
        base_dir = _PROJECT_ROOT

    data_dir = base_dir / papka_proektu / "data"
    db_path = data_dir / "certify.db"

    info = {
        "dir_exists": data_dir.exists(),
        "db_exists": db_path.exists(),
        "db_tables": [],
        "in_profiles": False,
        "client_id": _transliterate(papka_proektu).lower(),
    }

    # Проверяем таблицы в БД
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            info["db_tables"] = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception:
            pass

    # Проверяем profiles.yaml
    try:
        import yaml

        if _PROFILES_PATH.exists():
            with open(_PROFILES_PATH, "r", encoding="utf-8") as f:
                profiles = yaml.safe_load(f) or {}
            info["in_profiles"] = info["client_id"] in profiles.get("clients", {})
    except Exception:
        pass

    return info


# ─── CLI: Запуск из командной строки ─────────────────────────────────────

if __name__ == "__main__":
    # Пример использования
    logger.info("Использование:")
    print(
        "  python client_provisioner.py <папка_проекта> <название> <ЕДРПОУ> <руководитель>"
    )
    print()
    print("Пример:")
    print(
        '  python client_provisioner.py "МІЙ_КЛІЄНТ" \'ТОВ "МІЙ"\' "12345678" "І. І. Іванов"'
    )
    sys.exit(1)

    papka = sys.argv[1]
    name = sys.argv[2]
    code = sys.argv[3]
    director = sys.argv[4]

    logger.info(f"🔧 Инициализация клиента: {papka}")
    logger.info(f"   Название: {name}")
    logger.info(f"   ЕДРПОУ: {code}")
    logger.info(f"   Руководитель: {director}")
    logger.info("")

    result = provision_new_client(papka, name, code, director)

    logger.info("")
    if result.success:
        logger.info("✅ УСПЕХ!")
        logger.info(f"   Папка: {result.data_dir}")
        logger.info(f"   БД: {result.db_path}")
        logger.info(f"   Профиль YAML: {result.profile_added}")
    else:
        logger.error("❌ ОШИБКА!")
        for err in result.errors:
            logger.error(f"   - {err}")

    if result.warnings:
        print("⚠️ ПРЕДУПРЕЖДЕНИЯ:")
        for warn in result.warnings:
            print(f"   - {warn}")

    # Проверка
    print()
    print("📊 Проверка состояния:")
    info = check_client_provisioned(papka)
    print(f"   Папка: {'✅' if info['dir_exists'] else '❌'}")
    print(f"   БД: {'✅' if info['db_exists'] else '❌'}")
    print(f"   Таблицы: {', '.join(info['db_tables']) if info['db_tables'] else '—'}")
    print(f"   В profiles.yaml: {'✅' if info['in_profiles'] else '❌'}")
