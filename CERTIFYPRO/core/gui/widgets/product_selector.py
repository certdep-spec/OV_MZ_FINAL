"""
Віджет вибору продукції
"""

import logging
from typing import Callable, Dict, Optional

import customtkinter as ctk

import config

logger = logging.getLogger(__name__)


class ProductSelectorWidget(ctk.CTkFrame):
    """
    Віджет для вибору продукції з довідника
    Використовується у формі створення заявки
    """

    def __init__(
        self,
        parent,
        dict_service,
        on_product_selected: Optional[Callable] = None,
    ):
        super().__init__(parent)

        self.dict_service = dict_service
        self.on_product_selected = on_product_selected
        self.selected_product: Optional[Dict] = None

        self._create_widgets()

    def _create_widgets(self):
        """Створення елементів віджета"""
        # Заголовок
        self.lbl_title = ctk.CTkLabel(
            self, text="📦 Продукція", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_title.pack(anchor="w", pady=5)

        # Поле вибору продукції
        selection_frame = ctk.CTkFrame(self)
        selection_frame.pack(fill="x", pady=5)

        self.entry_product = ctk.CTkEntry(
            selection_frame,
            width=400,
            state="disabled",
            placeholder_text="Оберіть продукцію...",
        )
        self.entry_product.pack(side="left", padx=5)

        self.btn_select = ctk.CTkButton(
            selection_frame,
            text="🔍 Обрати",
            width=100,
            command=self._open_selection_dialog,
        )
        self.btn_select.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(
            selection_frame,
            text="❌",
            width=40,
            fg_color="gray",
            command=self.clear_selection,
        )
        self.btn_clear.pack(side="left", padx=5)

        # Інформаційна панель
        self.info_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        self.info_frame.pack(fill="x", pady=5)

        self.lbl_product_info = ctk.CTkLabel(
            self.info_frame,
            text="Продукція не обрана",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
        )
        self.lbl_product_info.pack(pady=5, padx=5)

    def _open_selection_dialog(self):
        """Відкриття діалогу вибору продукції"""
        from gui.app_form import ProductSelectionDialog

        dialog = ProductSelectionDialog(self, self.dict_service)
        self.wait_window(dialog)

        if dialog.selected_product:
            self._set_selected_product(dialog.selected_product)

    def _set_selected_product(self, product: Dict):
        """Встановлення вибраної продукції"""
        self.selected_product = product

        self.entry_product.configure(state="normal")
        self.entry_product.delete(0, "end")
        self.entry_product.insert(0, product["name"])
        self.entry_product.configure(state="disabled")

        # Відображення інформації
        info_text = f"ТУ: {product.get('tu', 'Н/Д')} | Термін зберігання: {product.get('shelf_life', 36)} міс."
        self.lbl_product_info.configure(
            text=info_text, text_color=config.COLORS["success"]
        )

        if self.on_product_selected:
            self.on_product_selected(product)

    def clear_selection(self):
        """Очищення вибору"""
        self.selected_product = None

        self.entry_product.configure(state="normal")
        self.entry_product.delete(0, "end")
        self.entry_product.configure(state="disabled")

        self.lbl_product_info.configure(text="Продукція не обрана", text_color="gray")

    def get_selected_product(self) -> Optional[Dict]:
        """Отримання вибраної продукції"""
        return self.selected_product

    def set_product(self, product: Dict):
        """Програмне встановлення продукції"""
        self._set_selected_product(product)
