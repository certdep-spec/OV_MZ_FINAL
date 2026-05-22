"""
Утиліта для отримання суфіксу шаблонів з конфігурації клієнта.
"""


def get_template_suffix(suffix_type: str = "default") -> str:
    """
    Повернути суффікс шаблону для поточного клієнта.

    Args:
        suffix_type: Тип суфікса ("default", "ugoda", "ugoda_import")

    Returns:
        Суффікс для шаблону (напр. "_А", "_Д")

    Приклад:
        suffix = get_template_suffix()  # "_А" для АФІНА, "_Д" для ДЖОНСОН
        template = f"1_Заявка_бланк{suffix}.docx"
    """
    try:
        from config import get_template_suffix as _get_suffix

        return _get_suffix()
    except Exception:
        # Fallback на ДЖОНСОН якщо конфігурація не ініціалізована
        suffixes = {
            "default": "_Д",
            "ugoda": "_Д",
            "ugoda_import": "_імпорт_Д",
        }
        return suffixes.get(suffix_type, "_Д")


def build_template_name(base_name: str, suffix_type: str = "default") -> str:
    """
    Побудувати повне ім'я шаблону з суфіксом.

    Args:
        base_name: Базове ім'я (напр. "1_Заявка_бланк")
        suffix_type: Тип суфікса

    Returns:
        Повне ім'я шаблону (напр. "1_Заявка_бланк_А.docx")

    Приклад:
        build_template_name("1_Заявка_бланк")  # "1_Заявка_бланк_А.docx"
    """
    suffix = get_template_suffix(suffix_type)
    return f"{base_name}{suffix}.docx"
