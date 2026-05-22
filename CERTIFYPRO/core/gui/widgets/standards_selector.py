"""
Віджет вибору стандартів
"""

import logging
from typing import Dict, List

import customtkinter as ctk

import config

logger = logging.getLogger(__name__)


class StandardsSelectorWidget(ctk.CTkFrame):
    """
    Віджет для вибору стандартів (НД) для випробувань
    Використовується у формі створення заявки та діалозі партій
    """

    def __init__(self, parent, dict_service, allow_multiple: bool = True):
        super().__init__(parent)

        self.dict_service = dict_service
        self.allow_multiple = allow_multiple
        self.selected_standards: List[int] = []

        self._create_widgets()

    def _create_widgets(self):
        """Створення елементів віджета"""
        # Заголовок
        self.lbl_title = ctk.CTkLabel(
            self,
            text="📋 Стандарти для випробувань",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.lbl_title.pack(anchor="w", pady=5)

        # Поле відображення вибраних стандартів
        display_frame = ctk.CTkFrame(self)
        display_frame.pack(fill="x", pady=5)

        self.entry_display = ctk.CTkEntry(
            display_frame,
            width=400,
            state="disabled",
            placeholder_text="Стандарти не обрані",
        )
        self.entry_display.pack(side="left", padx=5)

        self.btn_select = ctk.CTkButton(
            display_frame,
            text="📋 Обрати",
            width=100,
            command=self._open_selection_dialog,
        )
        self.btn_select.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(
            display_frame,
            text="❌",
            width=40,
            fg_color="gray",
            command=self.clear_selection,
        )
        self.btn_clear.pack(side="left", padx=5)

        # Мітка з кількістю вибраних стандартів
        self.lbl_count = ctk.CTkLabel(
            self,
            text="❌ Стандарти не обрано",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.lbl_count.pack(anchor="w", pady=2)

    def _open_selection_dialog(self):
        """Відкриття діалогу вибору стандартів"""
        from gui.widgets.standards_selection_dialog import (
            StandardsSelectionDialog,
        )

        dialog = StandardsSelectionDialog(self, self.dict_service)
        self.wait_window(dialog)

        if dialog.selected_standards:
            self._set_selected_standards(dialog.selected_standards)

    def _set_selected_standards(self, standards: List[int]):
        """Встановлення вибраних стандартів"""
        self.selected_standards = standards

        # Формуємо список ID стандартів
        std_ids = [str(s) for s in standards]
        std_text = ", ".join(std_ids)

        self.entry_display.configure(state="normal")
        self.entry_display.delete(0, "end")
        self.entry_display.insert(0, std_text)
        self.entry_display.configure(state="disabled")

        count_text = f"✅ Обрано стандартів: {len(standards)} ({std_text})"
        self.lbl_count.configure(text=count_text, text_color=config.COLORS["success"])

    def clear_selection(self):
        """Очищення вибору"""
        self.selected_standards = []

        self.entry_display.configure(state="normal")
        self.entry_display.delete(0, "end")
        self.entry_display.configure(state="disabled")

        self.lbl_count.configure(text="❌ Стандарти не обрано", text_color="gray")

    def get_selected_standards(self) -> List[Dict]:
        """Отримання вибраних стандартів"""
        return self.selected_standards

    def get_standard_ids(self) -> List[int]:
        """Отримання ID вибраних стандартів"""
        return self.selected_standards

    def set_standards(self, standards: List[int]):
        """Програмне встановлення стандартів"""
        self._set_selected_standards(standards)
