"""
Діалогове вікно вибору продукції
"""

import logging
from tkinter import messagebox, ttk

import customtkinter as ctk

logger = logging.getLogger(__name__)

import config
from gui.client_badge import add_client_badge
from gui.gui_utils import restore_window_geometry, save_window_geometry


class ProductSelectionDialog(ctk.CTkToplevel):
    """Діалогове вікно вибору продукції"""

    def __init__(self, parent, dict_service, selected_tu=None):
        super().__init__(parent)

        self.title("📦 Вибір Продукції")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()

        self.dict_service = dict_service
        self.db = dict_service  # Для зворотної сумісності
        self.selected_tu = selected_tu
        self.selected_product = None

        self.create_widgets()
        self.load_products()

        # Восстанавливаем сохраненную геометрию
        self.after(
            100,
            lambda: restore_window_geometry(self, "ProductSelectionDialog", 800, 600),
        )

        # Привязываем функцию сохранения геометрии при закрытии
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📦 Оберіть Продукцію",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=15)

        # Фільтр за ТУ
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            filter_frame,
            text=(
                f"📋 ТУ: {self.selected_tu}" if self.selected_tu else "📋 ТУ: Не обрано"
            ),
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=10)

        # Таблиця продукції
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("№", "Назва продукції", "ТУ", "Термін (міс)")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=15
        )

        self.tree.heading("№", text="№")
        self.tree.heading("Назва продукції", text="Назва продукції")
        self.tree.heading("ТУ", text="ТУ")
        self.tree.heading("Термін (міс)", text="Термін (міс)")

        self.tree.column("№", width=50)
        self.tree.column("Назва продукції", width=400)
        self.tree.column("ТУ", width=250)
        self.tree.column("Термін (міс)", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Подвійний клік для вибору
        self.tree.bind("<Double-1>", self.on_select)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ Обрати",
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.on_select,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=10)

    def load_products(self):
        """Завантаження продукції з фільтрацією за ТУ"""
        if not self.dict_service:
            logger.warning("dict_service не ініціалізовано")
            return
        products = self.dict_service.get_all_products()

        logger.info(f"🔍 Знайдено продуктів: {len(products)}")

        for i, product in enumerate(products, 1):
            # product є ProductDTO
            name = product.name
            tu = product.tu_code
            shelf_life = product.shelf_life_months

            # Фільтрація за ТУ (якщо обрано)
            if self.selected_tu and tu != self.selected_tu:
                continue

            self.tree.insert("", "end", values=(i, name, tu, shelf_life))

    def on_closing(self):
        """Сохранение геометрии перед закрытием"""
        save_window_geometry(self, "ProductSelectionDialog")
        self.destroy()

    def on_select(self, event=None):
        """Обробка вибору продукції"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть продукцію зі списку!")
            return

        # Отримуємо дані вибраного рядка
        item = self.tree.item(selected[0])
        values = item["values"]

        # Зберігаємо вибрану продукцію
        self.selected_product = {
            "name": values[1],
            "tu": values[2],
            "shelf_life": values[3],
        }

        self.on_closing()
