"""
Константи тегів для шаблонів документів.

Замість магічних рядків на кшталт "[B1]", "[C10]", "[FIN]" —
використовуйте іменовані константи з цього модуля.

Приклад:
    from documents.tags import APP_NUMBER, COMPANY_NAME, PRODUCT_NAME

    context = {
        APP_NUMBER: formatted_num,
        COMPANY_NAME: app_data["company_name"],
        PRODUCT_NAME: party_data["product_name"],
    }
"""

# ===== Заявник (Applicant) =====
APP_NUMBER = "[B1]"
APP_DATE = "[B2]"
COMPANY_NAME = "[B3]"
COMPANY_CODE = "[B4]"
PRODUCTION_ADDRESS = "[B5]"
TU_CODE = "[B6]"
DIRECTOR_NAME = "[B7]"

# ===== Партія (Party) =====
PRODUCT_NAME = "[B10]"
PARTY_CODE = "[C10]"
PARTY_DATE = "[C11]"
MFG_DATE = "[D10]"
EXPIRY_DATE = "[E10]"
FIN_DATE = "[FIN]"
QUANTITY_UNIT = "[F10]"
UNIT = "[UNIT]"
PROTOCOL = "[G10]"
CERT_NUMBER = "[H10]"
CERT_DATE = "[I10]"

# ===== Ідентифікація =====
PARTY_ID = "[A1]"
PARTY_ID_2 = "[A10]"

# ===== Сертифікати ПАР =====
PAR_CERTIFICATES = "[3F2]"

# ===== Реєстрація =====
REG_NUMBER = "[REG_NUM]"
REG_DATE = "[REG_DATE]"
REG_FORMATTED = "[REG_FORMATTED_NUM]"

# ===== Стандарти НД =====
STANDARD_1 = "[1]"
STANDARD_2 = "[2]"
STANDARD_3 = "[3]"
STANDARD_4 = "[4]"
STANDARD_5 = "[5]"
STANDARD_6 = "[6]"
STANDARD_7 = "[7]"
STANDARD_8 = "[8]"
STANDARD_9 = "[9]"
STANDARD_10 = "[10]"
STANDARD_11 = "[11]"
STANDARD_12 = "[12]"


def all_tags() -> dict[str, str]:
    """
    Повернути словник усіх тегів {ім'я: значення}.

    Корисно для логування або валідації шаблонів.
    """
    return {
        k: v for k, v in globals().items() if isinstance(v, str) and v.startswith("[")
    }


def strip_brackets(tag: str) -> str:
    """
    Видалити дужки з тегу для docxtpl контексту.

    Приклад:
        strip_brackets("[B1]")  → "B1"
        strip_brackets("[REG_NUM]")  → "REG_NUM"
    """
    return tag.strip("[]")


def tag_variants(tag: str) -> list[str]:
    """
    Повернути всі варіанти тегу: [X], {{X}}, {X}.

    Приклад:
        tag_variants("[B1]")
        # → ["[B1]", "{{B1}}", "{B1}"]
    """
    inner = tag.strip("[]")
    return [
        f"[{inner}]",
        f"{{{{{inner}}}}}",
        f"{{{inner}}}",
    ]
