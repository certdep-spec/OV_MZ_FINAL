"""
Утиліти для роботи з таблицями в Word документах
"""

from typing import List

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm


def set_table_borders(table) -> None:
    """
    Встановлює рамки для таблиці.

    Args:
        table: Об'єкт таблиці docx
    """
    tbl = table._element

    # Знаходимо або створюємо властивості таблиці (tblPr)
    tblPr = tbl.xpath("w:tblPr")
    if not tblPr:
        tblPr_elem = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr_elem)
    else:
        tblPr_elem = tblPr[0]

    # Видаляємо існуючі рамки
    old_borders = tblPr_elem.xpath("w:tblBorders")
    if old_borders:
        tblPr_elem.remove(old_borders[0])

    tblBorders = OxmlElement("w:tblBorders")

    borders = ["top", "left", "bottom", "right", "insideH", "insideV"]

    for border_name in borders:
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")  # 4 = 1/2 pt
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "000000")
        tblBorders.append(border)

    tblPr_elem.append(tblBorders)


def set_column_widths(table, col_widths: List[Cm]) -> None:
    """
    Встановлює ширину колонок таблиці.

    Args:
        table: Об'єкт таблиці docx
        col_widths: Список ширин колонок
    """
    for col_idx, width in enumerate(col_widths):
        if col_idx < len(table.columns):
            table.columns[col_idx].width = width
