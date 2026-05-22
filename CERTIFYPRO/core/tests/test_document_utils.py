"""
Unit-тести для documents/document_utils.py
"""

import unittest

from documents.document_utils import (
    calculate_expiry_date,
    escape_xml,
    format_app_number,
    format_quantity,
    format_registration_data,
    format_units,
    get_month_name_ua,
    sanitize_filename,
)


class TestFormatAppNumber(unittest.TestCase):
    """Тести для format_app_number"""

    def test_valid_numbers(self):
        self.assertEqual(format_app_number("1"), "001")
        self.assertEqual(format_app_number("12"), "012")
        self.assertEqual(format_app_number("123"), "123")

    def test_already_formatted(self):
        self.assertEqual(format_app_number("001"), "001")
        self.assertEqual(format_app_number("045"), "045")

    def test_non_numeric(self):
        self.assertEqual(format_app_number("abc"), "abc")
        self.assertEqual(format_app_number(""), "")


class TestCalculateExpiryDate(unittest.TestCase):
    """Тести для calculate_expiry_date"""

    def test_valid_shelf_life(self):
        """Перевірка правильного розрахунку: 05.04.2026 + 24 місяці = 05.04.2028"""
        result = calculate_expiry_date("05.04.2026", 24)
        self.assertEqual(result, "05.04.2028")

    def test_valid_shelf_life_edge_case(self):
        """Перевірка вихід за межі місяця: 31.01.2026 + 1 місяць = 28/29.02.2026"""
        result = calculate_expiry_date("31.01.2026", 1)
        # 2026 не високосний, тому лютий має 28 днів
        self.assertEqual(result, "28.02.2026")

    def test_leap_year_adjustment(self):
        """Перевірка високосного року: 31.01.2024 + 1 місяць = 29.02.2024"""
        result = calculate_expiry_date("31.01.2024", 1)
        # 2024 високосний, лютий має 29 днів
        self.assertEqual(result, "29.02.2024")

    def test_zero_shelf_life(self):
        result = calculate_expiry_date("05.04.2026", 0)
        self.assertEqual(result, "05.04.2026")

    def test_invalid_date_format(self):
        self.assertEqual(calculate_expiry_date("invalid", 12), "")

    def test_none_inputs(self):
        self.assertEqual(calculate_expiry_date(None, 12), "")
        self.assertEqual(calculate_expiry_date("05.04.2026", None), "")


class TestGetMonthNameUa(unittest.TestCase):
    """Тести для get_month_name_ua"""

    def test_all_months(self):
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
        for num, name in months.items():
            self.assertEqual(get_month_name_ua(num), name)

    def test_invalid_month(self):
        self.assertEqual(get_month_name_ua("13"), "13")
        self.assertEqual(get_month_name_ua("00"), "00")


class TestFormatRegistrationData(unittest.TestCase):
    """Тести для format_registration_data"""

    def test_valid_input(self):
        result = format_registration_data("5", "05.04.2026")
        self.assertEqual(result["reg_number"], "114/005ТРП")
        # reg_date format: «dd» місяць yyyy р.
        self.assertIn("5", result["reg_date"])
        self.assertIn("квітня", result["reg_date"])
        self.assertIn("2026", result["reg_date"])

    def test_long_number(self):
        result = format_registration_data("123", "05.04.2026")
        self.assertEqual(result["reg_number"], "114/123ТРП")

    def test_invalid_date_fallback(self):
        result = format_registration_data("1", "invalid-date")
        # Should use current date
        self.assertIn("reg_number", result)
        self.assertIn("р.", result["reg_date"])


class TestFormatQuantity(unittest.TestCase):
    """Тести для format_quantity"""

    def test_integer(self):
        from documents.document_utils import format_quantity

        self.assertEqual(format_quantity(100), "100")
        self.assertEqual(format_quantity(0), "0")

    def test_float_without_decimal(self):
        self.assertEqual(format_quantity(100.0), "100")

    def test_float_with_decimal(self):
        self.assertEqual(format_quantity(100.5), "100.5")
        self.assertEqual(format_quantity(3.14159), "3.14159")

    def test_string_input(self):
        self.assertEqual(format_quantity("42.5"), "42.5")
        self.assertEqual(format_quantity("100"), "100")

    def test_invalid_input(self):
        self.assertEqual(format_quantity(None), "")
        self.assertEqual(format_quantity("abc"), "abc")


class TestFormatUnits(unittest.TestCase):
    """Тести для format_units"""

    def test_common_units(self):
        from documents.document_utils import format_units

        self.assertEqual(format_units("кг"), "кг")
        self.assertEqual(format_units("шт"), "шт.")
        self.assertEqual(format_units("т"), "т")

    def test_unknown_unit(self):
        self.assertEqual(format_units("unknown"), "unknown")


class TestEscapeXML(unittest.TestCase):
    """Тести для escape_xml"""

    def test_escape_ampersand(self):
        self.assertEqual(escape_xml("A & B"), "A &amp; B")

    def test_escape_lt_gt(self):
        self.assertEqual(escape_xml("1 < 2 > 0"), "1 &lt; 2 &gt; 0")

    def test_escape_quotes(self):
        self.assertEqual(escape_xml('"quoted"'), "&quot;quoted&quot;")
        self.assertEqual(escape_xml("'apostrophe'"), "&apos;apostrophe&apos;")

    def test_escape_multiple(self):
        result = escape_xml("5 & 3 < 10 > 2")
        self.assertIn("&amp;", result)
        self.assertIn("&lt;", result)
        self.assertIn("&gt;", result)

    def test_no_special_chars(self):
        self.assertEqual(escape_xml("normal text"), "normal text")


class TestSanitizeFilename(unittest.TestCase):
    """Тести для sanitize_filename"""

    def test_remove_illegal_chars(self):
        from documents.document_utils import sanitize_filename

        self.assertEqual(sanitize_filename("file:name?.docx"), "file_name_.docx")
        self.assertEqual(sanitize_filename("a/b\\c.txt"), "a_b_c.txt")

    def test_keep_valid_chars(self):
        self.assertEqual(
            sanitize_filename("normal_file-123.docx"), "normal_file-123.docx"
        )

    def test_whitespace_handling(self):
        # Multiple spaces should be replaced with single underscore?
        # Check implementation
        result = sanitize_filename("a  b   c.txt")
        self.assertNotIn("  ", result)
        self.assertNotIn("   ", result)


if __name__ == "__main__":
    unittest.main()
