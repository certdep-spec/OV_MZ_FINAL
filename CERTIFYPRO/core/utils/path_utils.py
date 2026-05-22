"""
Утилиты для работы с путями файлов
"""

from datetime import datetime
from pathlib import Path
from typing import Union

# Українські місяці для іменування папок
MONTHS_UA = {
    "01": "01_Січень",
    "02": "02_Лютий",
    "03": "03_Березень",
    "04": "04_Квітень",
    "05": "05_Травень",
    "06": "06_Червень",
    "07": "07_Липень",
    "08": "08_Серпень",
    "09": "09_Вересень",
    "10": "10_Жовтень",
    "11": "11_Листопад",
    "12": "12_Грудень",
}


def format_app_number(app_number: Union[str, int]) -> str:
    """Форматування номера заявки у вигляді 3-значного числа"""
    digits = "".join(c for c in str(app_number) if c.isdigit())
    return digits.zfill(3) if digits else str(app_number)


def create_structured_path(
    output_dir: Union[str, Path],
    app_number: Union[str, int],
    app_date: str,
) -> Path:
    """
    Створення структурованої папки для документів.

    Формат: {output_dir}/{рік}/{місяць_ua}/Заявка_{номер}/

    Args:
        output_dir: Базова тека для документів
        app_number: Номер заявки (буде відформатовано до 3 цифр)
        app_date: Дата заявки у форматі дд.мм.рррр

    Returns:
        Path до створеної папки
    """
    output_path = Path(output_dir)

    try:
        date_obj = datetime.strptime(app_date, "%d.%m.%Y")
    except ValueError:
        date_obj = datetime.now()

    year = date_obj.strftime("%Y")
    month_num = date_obj.strftime("%m")
    month_ua = MONTHS_UA.get(month_num, f"{month_num}_Місяць")

    formatted_app_num = format_app_number(app_number)

    folder_path = output_path / year / month_ua / f"Заявка_{formatted_app_num}"
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path
