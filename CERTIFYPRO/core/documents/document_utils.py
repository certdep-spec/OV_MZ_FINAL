"""
Утиліти для роботи з документами
Форматування, дати, реєстраційні номери
"""

import calendar
from datetime import datetime
from typing import Dict


def format_app_number(app_number: str) -> str:
    """
    Форматує номер заявки на 3 цифри з нулями попереду.

    Args:
        app_number: Номер заявки (наприклад, "1")

    Returns:
        Відформатований номер (наприклад, "001")
    """
    try:
        return str(int(app_number)).zfill(3)
    except (ValueError, TypeError):
        return str(app_number)


def calculate_expiry_date(mfg_date: str, shelf_life_months: int) -> str:
    """
    Розрахунок терміну придатності.

    Args:
        mfg_date: Дата виробництва (формат: "дд.мм.рррр")
        shelf_life_months: Термін зберігання у місяцях

    Returns:
        Дата закінчення терміну (формат: "дд.мм.рррр") або порожній рядок
    """
    try:
        mfg = datetime.strptime(mfg_date, "%d.%m.%Y")
        # Розрахувати цільовий рік і місяць
        total_months = mfg.month + shelf_life_months
        target_year = mfg.year + (total_months - 1) // 12
        target_month = (total_months - 1) % 12 + 1
        # Визначити останній день цільового місяця
        last_day_of_target_month = calendar.monthrange(target_year, target_month)[1]
        # Використовувати мінімум з поточного дня та останнього дня місяця
        target_day = min(mfg.day, last_day_of_target_month)
        expiry = datetime(target_year, target_month, target_day)
        return expiry.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return ""


def get_month_name_ua(month_num: str) -> str:
    """
    Отримати назву місяця українською.

    Args:
        month_num: Номер місяця ("01"-"12")

    Returns:
        Назва місяця українською
    """
    months = {
        "01": "січня",
        "02": "лютого",
        "03": "березня",
        "04": "квітня",
        "05": "травня",
        "06": "червня",
        "07": "липня",
        "08": "серпня",
        "09": "вересня",
        "10": "жовтня",
        "11": "листопада",
        "12": "грудня",
    }
    return months.get(month_num, month_num)


def format_registration_data(app_number: str, app_date: str) -> Dict[str, str]:
    """
    Формує реєстраційні дані для заявки.

    Args:
        app_number: Номер заявки
        app_date: Дата заявки

    Returns:
        Словник з reg_number та reg_date
    """
    formatted_num = app_number.zfill(3) if app_number.isdigit() else app_number
    reg_number = f"114/{formatted_num}ТРП"

    try:
        date_obj = datetime.strptime(app_date, "%d.%m.%Y")
        day = date_obj.strftime("%d")
        month = get_month_name_ua(date_obj.strftime("%m"))
        year = date_obj.strftime("%Y")
        reg_date = f"«{day}» {month} {year} р."
    except (ValueError, TypeError):
        today = datetime.now()
        day = today.strftime("%d")
        month = get_month_name_ua(today.strftime("%m"))
        year = today.strftime("%Y")
        reg_date = f"«{day}» {month} {year} р."

    return {
        "reg_number": reg_number,
        "reg_date": reg_date,
        "reg_formatted_num": formatted_num,
    }


def get_file_date() -> str:
    """
    Отримати поточну дату для імені файлу.

    Returns:
        Дата у форматі YYYY-MM-DD
    """
    return datetime.now().strftime("%Y-%m-%d")


def format_quantity(value) -> str:
    """
    Форматує кількість: прибирає зайві нулі після коми.

    Args:
        value: Кількість (int, float або str)

    Returns:
        Відформатований рядок
    """
    if value is None:
        return ""
    try:
        num = float(value)
        if num == int(num):
            return str(int(num))
        return str(num).rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(value)


def format_units(unit: str) -> str:
    """
    Форматує одиницю виміру.

    Args:
        unit: Одиниця виміру

    Returns:
        Відформатована одиниця
    """
    unit_map = {
        "шт": "шт.",
        "кг": "кг",
        "т": "т",
        "л": "л",
        "мл": "мл",
        "г": "г",
    }
    return unit_map.get(unit, unit)


def escape_xml(text: str) -> str:
    """
    Екранує спеціальні символи XML.

    Args:
        text: Вхідний текст

    Returns:
        Текст з екранованими символами
    """
    if not isinstance(text, str):
        return str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text


def sanitize_filename(filename: str) -> str:
    """
    Санітизує ім'я файлу, замінюючи недопустимі символи.

    Args:
        filename: Вхідне ім'я файлу

    Returns:
        Безпечне ім'я файлу
    """
    if not isinstance(filename, str):
        filename = str(filename)
    # Замінюємо недопустимі символи Windows: < > : " / \ | ? *
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, "_")
    # Замінюємо множественні пробіли на один підкреслення
    import re

    filename = re.sub(r"\s+", "_", filename)
    return filename
