"""
Конфігурація системи CertifyPro (Мультиклієнтська версія)
Версія: 3.0.0

Цей файл — facade для делегованих модулів:
- utils/app_paths — шляхи та ініціалізація
- utils/logging_config — логування
- utils/client_config — конфігурація клієнта

Зберігає зворотну сумісність: всі старі імпорти працюють.
"""

import os
import sys
from pathlib import Path

# ===== Додаємо core/ в PYTHONPATH =====
_CORE_DIR = Path(__file__).parent
if str(_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_DIR))

# ===== ШЛЯХИ =====
from utils.app_paths import (
    APP_DIR,
    BASE_DIR,
    DATA_DIR,
    DB_PATH,
    DOCUMENTS_DIR,
    LOGS_DIR,
    PROFILES_PATH,
    PROJECT_ROOT,
    TEMPLATES_DIR,
    ensure_dynamic_client_infrastructure,
    initialize_app,
)

# ===== ВЕРСІЯ =====
VERSION = "3.0.0"
APP_NAME = "CertifyPro"

# ===== ЛОГУВАННЯ =====
from utils.logging_config import setup_logging

LOG_LEVEL = os.getenv("CERTIFYPRO_LOG_LEVEL", "INFO")
setup_logging(LOGS_DIR, LOG_LEVEL)

# ===== КЛІЄНТ-КОНФІГУРАЦІЯ =====
from utils.client_config import (
    ClientConfig,
    get_client_config,
    get_template_suffix,
    has_feature,
    init_client_config as _init_client_config,
)

# ===== КОНСТАНТИ (legacy globals) =====
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"
DATE_FORMAT = "%d.%m.%Y"
FILE_DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
FONT_FAMILY = "Times New Roman"
FONT_SIZE = 10
LANGUAGE = "uk"
MAX_PARTIES_PER_APP = 100
MIN_APP_NUMBER = 1
MAX_APP_NUMBER = 999

DEFAULT_COMPANY = None
DEFAULT_COMPANY_CODE = None
DEFAULT_DIRECTOR = None

COLORS = {
    "primary": "#2B7CB9",
    "primary_hover": "#1A5F8A",
    "success": "#2E8B57",
    "warning": "#DAA520",
    "error": "#DC143C",
    "info": "#4682B4",
}


def init_client_config(client_id: str) -> None:
    """
    Ініціалізувати конфігурацію для конкретного клієнта.

    Оновлює глобальні змінні для зворотної сумісності.
    Рекомендований спосіб доступу: get_client_config()
    """
    import logging
    
    # Оновлюємо глобальні змінні (зворотна сумісність)
    global DEFAULT_COMPANY, DEFAULT_COMPANY_CODE, DEFAULT_DIRECTOR
    global DATA_DIR, DB_PATH, DOCUMENTS_DIR, TEMPLATES_DIR
    global APPEARANCE_MODE, COLOR_THEME, DATE_FORMAT, FILE_DATE_FORMAT
    global DATETIME_FORMAT, FONT_FAMILY, FONT_SIZE, LANGUAGE
    global MAX_PARTIES_PER_APP, MIN_APP_NUMBER, MAX_APP_NUMBER

    cfg = _init_client_config(
        client_id=client_id,
        profiles_path=PROFILES_PATH,
        app_dir=APP_DIR,
        project_root=PROJECT_ROOT,
        templates_dir=TEMPLATES_DIR,
    )

    DEFAULT_COMPANY = cfg.default_company
    DEFAULT_COMPANY_CODE = cfg.default_company_code
    DEFAULT_DIRECTOR = cfg.default_director
    DATA_DIR = cfg.data_dir
    DB_PATH = cfg.db_path
    DOCUMENTS_DIR = cfg.documents_dir
    TEMPLATES_DIR = cfg.templates_dir
    APPEARANCE_MODE = cfg.appearance_mode
    COLOR_THEME = cfg.color_theme
    DATE_FORMAT = cfg.date_format
    FILE_DATE_FORMAT = cfg.file_date_format
    DATETIME_FORMAT = cfg.datetime_format
    FONT_FAMILY = cfg.font_family
    FONT_SIZE = cfg.font_size
    LANGUAGE = cfg.language
    MAX_PARTIES_PER_APP = cfg.max_parties_per_app
    MIN_APP_NUMBER = cfg.min_app_number
    MAX_APP_NUMBER = cfg.max_app_number

    logging.getLogger(__name__).info(
        "Ініціалізовано конфігурацію для клієнта: %s", cfg.default_company
    )
