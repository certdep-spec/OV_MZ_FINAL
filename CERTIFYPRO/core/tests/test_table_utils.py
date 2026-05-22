"""
Unit-тести для documents/table_utils.py
"""

import unittest
from unittest.mock import MagicMock, patch

from docx.shared import Cm

from documents.table_utils import set_column_widths, set_table_borders


class TestSetTableBorders(unittest.TestCase):
    """Тести для set_table_borders"""

    def test_set_table_borders_no_exception(self):
        """Перевірка що функція не викидає виключення на мокованій таблиці"""
        mock_table = MagicMock()
        mock_element = MagicMock()
        mock_table._element = mock_element
        mock_element.xpath.return_value = []  # Немає tblPr

        # Не повинно викинути виняток
        try:
            set_table_borders(mock_table)
        except Exception as e:
            self.fail(f"set_table_borders raised unexpected exception: {e}")

    def test_set_table_borders_removes_old_borders(self):
        """Перевірка видалення існуючих рамок"""
        mock_table = MagicMock()
        mock_element = MagicMock()
        mock_table._element = mock_element

        # Імітуємо існуючий tblPr з tblBorders
        mock_tblPr = MagicMock()
        mock_tblBorders = MagicMock()
        mock_tblPr.xpath.return_value = [MagicMock()]  # tblPr знайдено
        mock_element.xpath.return_value = [mock_tblPr]
        mock_tblPr.xpath.return_value = [mock_tblBorders]  # tblBorders знайдено

        set_table_borders(mock_table)

        # Перевіряємо що старий borders видалено
        mock_tblPr.remove.assert_called_once_with(mock_tblBorders)

    def test_creates_all_border_types(self):
        """Перевірка створення всіх типів рамок"""
        mock_table = MagicMock()
        mock_element = MagicMock()
        mock_table._element = mock_element
        mock_element.xpath.return_value = []

        with patch("documents.table_utils.OxmlElement") as mock_OxmlElement:
            mock_border = MagicMock()
            mock_OxmlElement.return_value = mock_border

            set_table_borders(mock_table)

            # Має бути 8 викликів: 1 для tblPr + 1 для tblBorders + 6 для border types
            self.assertEqual(mock_OxmlElement.call_count, 8)

            # Перевірка атрибутів border
            for call in mock_border.set.call_args_list:
                args, kwargs = call
                # Перевіряємо, що встановлюються атрибути w:val, w:sz, w:space, w:color
                if "w:val" in kwargs:
                    self.assertEqual(kwargs["w:val"], "single")
                if "w:sz" in kwargs:
                    self.assertEqual(kwargs["w:sz"], "4")
                if "w:space" in kwargs:
                    self.assertEqual(kwargs["w:space"], "0")
                if "w:color" in kwargs:
                    self.assertEqual(kwargs["w:color"], "000000")


class TestSetColumnWidths(unittest.TestCase):
    """Тести для set_column_widths"""

    def test_set_widths_all_columns(self):
        """Встановлення ширини для всіх колонок"""
        mock_table = MagicMock()
        mock_columns = [MagicMock() for _ in range(5)]
        mock_table.columns = mock_columns

        widths = [Cm(5), Cm(10), Cm(7.5), Cm(3), Cm(8)]

        set_column_widths(mock_table, widths)

        # Перевіряємо що кожній колонці встановлено ширину
        for i, col in enumerate(mock_columns):
            self.assertEqual(col.width, widths[i])

    def test_set_widths_fewer_widths_than_columns(self):
        """Якщо widths коротший за кількість колонок — встановлюємо тільки для перших"""
        mock_table = MagicMock()
        mock_columns = [MagicMock() for _ in range(5)]
        mock_table.columns = mock_columns

        widths = [Cm(5), Cm(10)]  # Тільки 2 ширини

        set_column_widths(mock_table, widths)

        # Перші 2 колонки повинні мати ширину
        mock_columns[0].width = widths[0]
        mock_columns[1].width = widths[1]
        # Решта не повинні бути змінені
        for i in range(2, 5):
            self.assertFalse(
                hasattr(mock_columns[i], "width") and mock_columns[i].width == widths[0]
            )

    def test_set_widths_more_widths_than_columns(self):
        """Якщо widths довший за columns — ігноруємо зайві"""
        mock_table = MagicMock()
        mock_columns = [MagicMock() for _ in range(2)]
        mock_table.columns = mock_columns

        widths = [Cm(5), Cm(10), Cm(7)]

        set_column_widths(mock_table, widths)

        # Тільки перші 2 колонки
        self.assertEqual(mock_columns[0].width, widths[0])
        self.assertEqual(mock_columns[1].width, widths[1])


if __name__ == "__main__":
    unittest.main()
