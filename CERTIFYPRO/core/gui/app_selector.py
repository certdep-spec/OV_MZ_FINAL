"""
Діалог вибору існуючої заявки з бази даних
"""

import logging
from tkinter import messagebox, ttk

import customtkinter as ctk

import config
from gui.client_badge import add_client_badge
from gui.gui_utils import restore_window_geometry, save_window_geometry

logger = logging.getLogger(__name__)


class AppSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, app_service):
        super().__init__(parent)

        self.title("📂 Відкрити Заявку")
        self.geometry("900x400")
        self.transient(parent)
        self.grab_set()

        self.app_service = app_service
        self.selected_app = None

        self.create_widgets()
        self.load_applications()

        # Відновлюємо збережену геометрію
        self.after(
            100,
            lambda: restore_window_geometry(self, "AppSelectorDialog", 900, 400),
        )
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📂 Відкрити Існуючу Заявку",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=15)

        # Таблиця заявок
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("№", "Дата", "Підприємство", "Кількість партій")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=8
        )

        self.tree.heading("№", text="№ Заявки", command=lambda: self.sort_column("№", False))
        self.tree.heading("Дата", text="Дата", command=lambda: self.sort_column("Дата", False))
        self.tree.heading("Підприємство", text="Підприємство", command=lambda: self.sort_column("Підприємство", False))
        self.tree.heading("Кількість партій", text="Партій", command=lambda: self.sort_column("Кількість партій", False))

        self.tree.column("№", width=60, anchor="center")
        self.tree.column("Дата", width=90, anchor="center")
        self.tree.column("Підприємство", width=550, stretch=True)
        self.tree.column("Кількість партій", width=80, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Подвійний клік для відкриття
        self.tree.bind("<Double-1>", self.on_select)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ Відкрити",
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.on_select,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Видалити",
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="red",
            command=self.on_delete,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            command=self.on_closing,
        ).pack(side="left", padx=10)

    def load_applications(self):
        """Завантаження списку заявок з БД"""
        # Очищення таблиці
        for item in self.tree.get_children():
            self.tree.delete(item)

        apps = self.app_service.get_all_applications()

        if not apps:
            ctk.CTkLabel(
                self,
                text="⚠️ Заявок в базі не знайдено!",
                font=ctk.CTkFont(size=14),
                text_color="red",
            ).pack(pady=10)
            return

        for app in apps:
            parties = self.app_service.get_parties_for_application(app.id)
            party_count = len(parties)

            self.tree.insert(
                "",
                "end",
                values=(
                    app.app_number,
                    app.app_date,
                    app.company_name[:50],
                    party_count,
                ),
                tags=(app.id,),
            )

    def sort_column(self, col, reverse):
        """Сортування таблиці за стовпцем"""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        
        # Визначаємо ключ сортування в залежності від типу даних
        def sort_key(val_tuple):
            val = val_tuple[0]
            if col == "№" or col == "Кількість партій":
                try:
                    return int(val)
                except ValueError:
                    return val
            elif col == "Дата":
                # Конвертуємо DD.MM.YYYY в YYYYMMDD для правильного сортування
                try:
                    parts = val.split('.')
                    if len(parts) == 3:
                        return f"{parts[2]}{parts[1]}{parts[0]}"
                except Exception:
                    pass
                return val
            return val.lower()

        l.sort(key=sort_key, reverse=reverse)

        # Переставляємо елементи
        for index, (val, k) in enumerate(l):
            self.tree.move(k, "", index)

        # Перемикаємо напрямок для наступного кліку
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def on_select(self, event=None):
        """Обробка вибору заявки"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть заявку зі списку!")
            return

        # Отримуємо ID заявки з тегів
        item = self.tree.item(selected[0])
        app_id = int(item["tags"][0]) if item["tags"] else None

        if not app_id:
            messagebox.showerror("Помилка", "Не вдалося отримати ID заявки!")
            return

        # Завантажуємо повні дані заявки
        app_data = self.app_service.get_application_by_id(app_id)
        logger.debug("Завантажено заявку ID=%s, тип=%s", app_id, type(app_data).__name__)
        if not app_data:
            messagebox.showerror("Помилка", "Не вдалося завантажити дані заявки!")
            return

        # Завантажуємо партії
        parties = self.app_service.get_parties_for_application(app_id)

        # Конвертуємо в dict для сумісності зі старим кодом
        app_dict = {
            "id": app_data.id,
            "app_number": app_data.app_number,
            "app_date": app_data.app_date,
            "company_name": app_data.company_name,
            "company_code": app_data.company_code,
            "director_name": app_data.director_name,
            "tu_code": app_data.tu_code,
            "production_address": app_data.production_address,
            "parties": [
                {
                    "id": p.id,
                    "product_name": p.product_name,
                    "party_code": p.party_code,
                    "party_date": p.party_date,
                    "mfg_date": p.mfg_date,
                    "quantity": p.quantity,
                    "unit": p.unit,
                    "standards": p.standards or [],
                    "protocol_number": p.protocol_number,
                    "protocol_date": p.protocol_date,
                    "cert_number": p.cert_number,
                    "cert_date": p.cert_date,
                    "shelf_life_months": p.shelf_life_months,
                    "version": p.version,
                }
                for p in parties
            ],
        }

        self.selected_app = app_dict
        self.on_closing()

    def on_closing(self):
        """Зберігаємо геометрію та закриваємо"""
        save_window_geometry(self, "AppSelectorDialog")
        self.destroy()

    def on_delete(self):
        """Видалення вибраної заявки"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть заявку для видалення!")
            return

        # Отримуємо ID та номер для підтвердження
        item = self.tree.item(selected[0])
        app_number = item["values"][0]
        app_id = int(item["tags"][0]) if item["tags"] else None

        if not app_id:
            messagebox.showerror("Помилка", "Не вдалося отримати ID заявки!")
            return

        confirm = messagebox.askyesno(
            "Підтвердження видалення",
            f"Ви впевнені, що хочете видалити заявку №{app_number}?\n\n"
            "⚠️ Це дію неможливо відмінити! Усі пов'язані партії також будуть видалені.",
        )

        if confirm:
            try:
                self.app_service.delete_application(app_id)
                messagebox.showinfo("Успіх", f"Заявку №{app_number} успішно видалено.")
                self.load_applications()
            except Exception as e:
                messagebox.showerror(
                    "Помилка", f"Не вдалося видалити заявку:\n{str(e)}"
                )
