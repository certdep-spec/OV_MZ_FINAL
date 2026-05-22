"""
Unit-тести для utils/path_utils.py
"""

import tempfile
import unittest
from pathlib import Path

from utils.path_utils import (
    MONTHS_UA,
    create_structured_path,
    format_app_number,
)


class TestFormatAppNumber(unittest.TestCase):
    """Тести для format_app_number"""

    def test_format_simple_number(self):
        self.assertEqual(format_app_number("1"), "001")
        self.assertEqual(format_app_number("12"), "012")
        self.assertEqual(format_app_number("123"), "123")
        self.assertEqual(format_app_number("1234"), "1234")

    def test_format_with_non_digits(self):
        self.assertEqual(format_app_number("001"), "001")
        self.assertEqual(format_app_number("Заявка 5"), "005")
        self.assertEqual(format_app_number("№ 45"), "045")

    def test_format_invalid(self):
        self.assertEqual(format_app_number(""), "")
        self.assertEqual(format_app_number("abc"), "abc")

    def test_format_int(self):
        self.assertEqual(format_app_number(1), "001")
        self.assertEqual(format_app_number(42), "042")
        self.assertEqual(format_app_number(123), "123")


class TestCreateStructuredPath(unittest.TestCase):
    """Тести для create_structured_path"""

    def setUp(self):
        """Створення тимчасової директорії для тестів"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "documents"

    def tearDown(self):
        """Очищення тимчасових файлів"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_create_path_structure(self):
        """Тест створення правильної структури папок"""
        result = create_structured_path(self.output_dir, "001", "05.04.2026")

        # Перевіряємо шлях
        expected_path = self.output_dir / "2026" / "04_Квітень" / "Заявка_001"
        self.assertEqual(result, expected_path)
        self.assertTrue(result.exists())
        self.assertTrue(result.is_dir())

    def test_create_path_different_month(self):
        """Тест для іншого місяця"""
        result = create_structured_path(self.output_dir, "10", "15.01.2025")
        expected_path = self.output_dir / "2025" / "01_Січень" / "Заявка_010"
        self.assertEqual(result, expected_path)

    def test_create_path_invalid_date(self):
        """Тест з невірним форматом дати - повинен використати поточну дату"""
        result = create_structured_path(self.output_dir, "5", "invalid-date")
        # Шлях повинен містити поточний рік і місяць
        self.assertTrue(str(result).startswith(str(self.output_dir)))
        self.assertTrue(result.exists())

    def test_create_path_parents_created(self):
        """Тест що всі батьківські папки створені"""
        create_structured_path(self.output_dir, "1", "01.01.2025")
        self.assertTrue((self.output_dir / "2025").exists())
        self.assertTrue((self.output_dir / "2025" / "01_Січень").exists())


class TestMonthsUA(unittest.TestCase):
    """Тести для словника місяців"""

    def test_all_months_present(self):
        """Перевірка що всі 12 місяців є"""
        self.assertEqual(len(MONTHS_UA), 12)
        for i in range(1, 13):
            month_key = f"{i:02d}"
            self.assertIn(month_key, MONTHS_UA)

    def test_month_names_format(self):
        """Перевірка формату імен місяців (має починатися з цифри і підкреслення)"""
        for key, value in MONTHS_UA.items():
            self.assertTrue(value.startswith(f"{key}_"))
            self.assertNotIn("\n", value)
            self.assertGreater(len(value), 3)  # Мінімум "00_"


if __name__ == "__main__":
    unittest.main()
