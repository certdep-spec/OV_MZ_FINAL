"""
Утиліти для завантаження конфігурації з різних джерел.
"""

import configparser
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_app_settings(config_path: Path) -> dict:
    """
    Завантажити налаштування програми з config.ini.

    Повертає словник з ключами: company_name, company_code, director.
    Якщо файл не існує або ключі відсутні, повертає пустий словник.
    """
    settings = {}
    if config_path.exists():
        parser = configparser.ConfigParser()
        try:
            parser.read(config_path, encoding="utf-8")
            if "company" in parser:
                company_section = parser["company"]
                settings["company_name"] = company_section.get("name", "")
                settings["company_code"] = company_section.get("code", "")
                settings["director_name"] = company_section.get("director", "")
                logger.info(f"Налаштування компанії завантажено з {config_path}")
        except Exception as e:
            logger.error(f"Помилка читання config.ini: {e}")
    return settings


def save_app_settings(
    config_path: Path,
    company_name: str = "",
    company_code: str = "",
    director_name: str = "",
):
    """
    Зберегти налаштування компанії у config.ini.
    """
    parser = configparser.ConfigParser()
    if config_path.exists():
        try:
            parser.read(config_path, encoding="utf-8")
        except Exception:
            pass  # Створимо новий

    if "company" not in parser:
        parser["company"] = {}

    parser["company"]["name"] = company_name
    parser["company"]["code"] = company_code
    parser["company"]["director"] = director_name

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            parser.write(f)
        logger.info(f"Налаштування компанії збережено у {config_path}")
    except Exception as e:
        logger.error(f"Помилка збереження config.ini: {e}")
        raise
