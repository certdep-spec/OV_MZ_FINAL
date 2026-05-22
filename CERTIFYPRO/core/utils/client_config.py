"""
Конфігурація клієнта CertifyPro.

Виділено з config.py для зменшення coupling.
Відповідає за:
- ClientConfig dataclass
- init_client_config()
- get_client_config()
- Feature flags
"""

import logging
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    """
    Інсульована конфігурація клієнта — заміна глобальних змінних.

    Використання:
        cfg = get_client_config()
        print(cfg.default_company)
        print(cfg.db_path)
    """

    client_id: str = ""
    default_company: str = ""
    default_company_code: str = ""
    default_director: str = ""
    data_dir: Path = field(default_factory=lambda: Path("."))
    db_path: Path = field(default_factory=lambda: Path("certify.db"))
    documents_dir: Path = field(default_factory=lambda: Path("Documents"))
    templates_dir: Path = field(default_factory=lambda: Path("templates"))
    appearance_mode: str = "dark"
    color_theme: str = "blue"
    date_format: str = "%d.%m.%Y"
    file_date_format: str = "%Y-%m-%d"
    datetime_format: str = "%d.%m.%Y %H:%M"
    font_family: str = "Times New Roman"
    font_size: int = 10
    language: str = "uk"
    max_parties_per_app: int = 100
    min_app_number: int = 1
    max_app_number: int = 999
    _template_suffix: str = "_Д"
    _features: dict = field(default_factory=dict)

    @property
    def template_suffix(self) -> str:
        return self._template_suffix

    def has_feature(self, feature_name: str) -> bool:
        return bool(self._features.get(feature_name, False))

    def get_ugoda_template_count(self) -> int:
        return int(self._features.get("ugoda_templates", 1))


# ===== КОНТЕКСТ КЛІЄНТА =====
_client_config: Optional[ClientConfig] = None
_client_initialized = False


def get_client_config() -> ClientConfig:
    """
    Повернути інкапсульовану конфігурацію поточного клієнта.

    Це рекомендований спосіб доступу до налаштувань клієнта.
    """
    if _client_config is None:
        raise RuntimeError(
            "Клієнтську конфігурацію не ініціалізовано. "
            "Викличте init_client_config(client_id) спочатку."
        )
    return _client_config


def get_template_suffix() -> str:
    """Повернути суффікс шаблонів для поточного клієнта."""
    if _client_config:
        return _client_config.template_suffix
    return "_Д"


def has_feature(feature_name: str) -> bool:
    """Перевірити чи увімкнено функцію для поточного клієнта."""
    if _client_config:
        return _client_config.has_feature(feature_name)
    return feature_name == "import_product"


def init_client_config(
    client_id: str,
    profiles_path: Path,
    app_dir: Path,
    project_root: Path,
    templates_dir: Path,
) -> ClientConfig:
    """
    Ініціалізувати конфігурацію для конкретного клієнта.

    Повертає ClientConfig і оновлює глобальний стан.

    Args:
        client_id: Ідентифікатор клієнта
        profiles_path: Шлях до profiles.yaml
        app_dir: Папка з .exe або корінь проекту
        project_root: Корінь проекту
        templates_dir: Папка шаблонів

    Returns:
        Створений ClientConfig
    """
    global _client_initialized, _client_config

    if _client_initialized and _client_config and _client_config.client_id == client_id:
        logger.warning("Клієнтська конфігурація вже ініціалізована для client_id='%s'", client_id)
        return _client_config

    from client_manager import get_client_manager

    logger.info("init_client_config() викликано з client_id='%s'", client_id)
    logger.info("PROFILES_PATH = %s", profiles_path)
    logger.info("IS_FROZEN = %s", getattr(sys, "frozen", False))

    manager = get_client_manager()
    manager.load_profiles(profiles_path)

    logger.info("Завантажено профілів: %d", len(manager.get_client_ids()))
    logger.info("Доступні клієнти: %s", manager.get_client_ids())

    try:
        profile = manager.select_client(client_id)
        logger.info("Клієнт знайдений у profiles.yaml: %s", profile.display_name)
        logger.info("   company.code = %s", profile.company.code)
    except ValueError:
        logger.warning("Клієнт '%s' НЕ ЗНАЙДЕНО у profiles.yaml!", client_id)
        logger.warning("   Створюю динамічний профіль з порожніми даними...")
        from client_manager import ClientProfile, CompanyConfig, FeaturesConfig

        profile = ClientProfile(
            client_id=client_id,
            name=client_id,
            display_name=client_id,
            template_suffix="_Д",
            launcher_mapping=client_id,
            company=CompanyConfig(name=client_id, code="", director=""),
            features=FeaturesConfig(),
            data_dir=f"data/{client_id}",
            description="Динамічний клієнт",
        )
        manager._profiles[client_id] = profile
        manager._current_client = profile
        logger.warning(
            "   Динамічний профіль створено. Поля компанії будуть порожніми!"
        )

        data_dir_check = (
            app_dir / profile.data_dir
            if getattr(sys, "frozen", False)
            else project_root.parent / profile.data_dir
        )
        _ensure_dynamic_client_infrastructure(data_dir_check, client_id)

    gconf = manager.global_config

    if getattr(sys, "frozen", False):
        data_dir = app_dir / profile.data_dir
    else:
        data_dir = project_root / profile.data_dir

        if not (data_dir / "certify.db").exists():
            if "data/" in profile.data_dir:
                alt_dir = profile.data_dir.replace("data/", "") + "/data"
            else:
                alt_dir = "data/" + profile.data_dir.replace("/data", "")

            data_dir_alt = project_root / alt_dir
            if (data_dir_alt / "certify.db").exists():
                data_dir = data_dir_alt
                logger.info("Базу знайдено через альтернативний шлях: %s", data_dir)

    # У frozen режимі шаблони беруться з data/{client}/templates/
    # замість _internal/resources/templates/
    if getattr(sys, "frozen", False):
        templates_dir = data_dir / "templates"
        _deploy_templates_for_client(templates_dir)
        logger.info("Шаблони для клієнта: %s", templates_dir)

    _client_config = ClientConfig(
        client_id=client_id,
        default_company=profile.company.name,
        default_company_code=profile.company.code,
        default_director=profile.company.director,
        data_dir=data_dir,
        db_path=data_dir / "certify.db",
        documents_dir=data_dir / "Documents",
        templates_dir=templates_dir,
        appearance_mode=gconf.appearance_mode,
        color_theme=gconf.color_theme,
        date_format=gconf.date_format,
        file_date_format=gconf.file_date_format,
        datetime_format=gconf.datetime_format,
        font_family=gconf.font_family,
        font_size=gconf.font_size,
        language=gconf.language,
        max_parties_per_app=gconf.max_parties_per_app,
        min_app_number=gconf.min_app_number,
        max_app_number=gconf.max_app_number,
        _template_suffix=profile.template_suffix or "_Д",
        _features={
            "import_product": profile.features.import_product,
            "ugoda_templates": profile.features.ugoda_templates,
        },
    )

    logger.info(
        "ClientConfig створено: client_id=%s, code=%s, data_dir=%s",
        _client_config.client_id,
        _client_config.default_company_code,
        _client_config.data_dir,
    )

    data_dir.mkdir(parents=True, exist_ok=True)
    _client_config.documents_dir.mkdir(parents=True, exist_ok=True)

    _client_initialized = True
    logger.info(
        "Ініціалізовано конфігурацію для клієнта: %s", profile.display_name
    )

    return _client_config


def _deploy_templates_for_client(client_templates_dir: Path) -> None:
    """
    Копіює шаблони з _internal/resources/templates/ у data/{client}/templates/
    ТІЛЬКИ якщо папка шаблонів ще не існує або порожня.

    Якщо шаблони вже є — НЕ чіпає їх, щоб зберегти редагування користувача.
    """
    if not getattr(sys, "frozen", False):
        return

    if client_templates_dir.exists() and any(client_templates_dir.iterdir()):
        logger.info("Шаблони вже існують: %s — використовуються файли користувача", client_templates_dir)
        return

    src_templates = Path(sys._MEIPASS) / "resources" / "templates"
    if not src_templates.exists():
        logger.warning("Вихідні шаблони не знайдено: %s", src_templates)
        return

    client_templates_dir.mkdir(parents=True, exist_ok=True)
    for template_file in src_templates.iterdir():
        if template_file.is_file():
            shutil.copy2(str(template_file), str(client_templates_dir / template_file.name))
    logger.info("Розгорнуто шаблони: %s -> %s", src_templates, client_templates_dir)


def _ensure_dynamic_client_infrastructure(data_dir: Path, client_id: str) -> None:
    """Створити мінімальну інфраструктуру для динамічного клієнта."""
    import sqlite3

    try:
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "Documents").mkdir(parents=True, exist_ok=True)
            logger.info("Створено папку для динамічного клієнта: %s", data_dir)

        db_path = data_dir / "certify.db"
        if not db_path.exists():
            logger.info("Створюю БД для динамічного клієнта: %s", db_path)

            from utils.app_paths import BASE_DIR

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
                    "db_schema.sql не знайдено, використовується fallback"
                )
                from di import _init_database

                _init_database(db_path)

    except Exception as e:
        logger.error("Помилка створення інфраструктури для %s: %s", client_id, e)
