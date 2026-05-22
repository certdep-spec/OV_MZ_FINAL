"""
Діалогове вікно вибору стандартів (НД)
"""

import logging
from tkinter import messagebox, ttk

import customtkinter as ctk

import config
from gui.client_badge import add_client_badge
from gui.gui_utils import restore_window_geometry, save_window_geometry

logger = logging.getLogger(__name__)


class StandardsSelectionDialog(ctk.CTkToplevel):
    """Діалогове вікно вибору стандартів (НД)"""

    def __init__(self, parent, dict_service):
        super().__init__(parent)

        self.title("📋 Вибір Стандартів для Випробувань")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()

        self.dict_service = dict_service
        self.selected_standards = []

        self.create_widgets()
        self.load_standards()

        # Восстанавливаем сохраненную геометрию
        self.after(
            100,
            lambda: restore_window_geometry(self, "StandardsSelectionDialog", 800, 600),
        )

        # Привязываем функцию сохранения геометрии при закрытии
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📋 Оберіть Стандарти для Випробувань",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=15)

        # Інструкція
        ctk.CTkLabel(
            self,
            text="Оберіть один або кілька стандартів (Ctrl+клік для множинного вибору)",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=5)

        # Таблиця стандартів
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("№", "Стандарт")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            selectmode="extended",
        )

        self.tree.heading("№", text="№")
        self.tree.heading("Стандарт", text="Стандарт")

        self.tree.column("№", width=50)
        self.tree.column("Стандарт", width=700)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

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

    def load_standards(self):
        """Завантаження стандартів через DictionaryService"""
        try:
            standards = (
                self.dict_service.get_all_standards() if self.dict_service else []
            )
            logger.info(f"📊 Стандартів в базі: {len(standards)}")

            if not standards:
                ctk.CTkLabel(
                    self,
                    text="⚠️ Стандарти не знайдено! Спочатку імпортуйте дані з Excel.",
                    font=ctk.CTkFont(size=12),
                    text_color="red",
                ).pack(pady=10)
                return

            print(f"✅ Завантажено {len(standards)} стандартів")

            for std in standards:
                # std є StandardDTO
                std_id = std.id
                description = std.description
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        std_id,
                        description[:100] + ("..." if len(description) > 100 else ""),
                    ),
                )
        except Exception as e:
            logger.error("Помилка завантаження стандартів", exc_info=True)
            print(f"❌ Помилка завантаження стандартів: {e}")
            ctk.CTkLabel(
                self,
                text=f"❌ Помилка: {str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red",
            ).pack(pady=10)

    def on_closing(self):
        """Сохранение геометрии перед закрытием"""
        save_window_geometry(self, "StandardsSelectionDialog")
        self.destroy()

    def on_select(self):
        """Обробка вибору стандартів"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть хоча б один стандарт!")
            return

        # Збираємо вибрані стандарти (тільки ID як int)
        self.selected_standards = []
        for item in selected:
            values = self.tree.item(item)["values"]
            try:
                self.selected_standards.append(int(values[0]))
            except (ValueError, TypeError, IndexError):
                continue

        print(f"✅ Обрано стандартів: {len(self.selected_standards)}")
        self.on_closing()
