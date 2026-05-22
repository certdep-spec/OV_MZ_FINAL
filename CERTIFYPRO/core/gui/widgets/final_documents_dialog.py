"""
Діалогове вікно для введення даних фінальних документів (Сертифікат, Протокол)
"""

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

import config
from gui.client_badge import add_client_badge
from gui.gui_utils import (
    add_context_menu,
    restore_window_geometry,
    save_window_geometry,
)


class FinalDocumentsDialog(ctk.CTkToplevel):
    """Діалогове вікно для введення даних фінальних документів (Сертифікат, Протокол)"""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("📜 Фінальні документи")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()

        self.after(
            100,
            lambda: restore_window_geometry(self, "FinalDocumentsDialog", 500, 400),
        )
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

        self.final_data = None

        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📜 Дані Фінальних Документів",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=15)

        # Інструкція
        ctk.CTkLabel(
            self,
            text="Заповніть дані про сертифікацію:",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=5)

        # Прокрутка
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Поля введення
        form_frame = ctk.CTkFrame(self.scroll_frame)
        form_frame.pack(fill="x", pady=10)

        # Номер сертифіката
        ctk.CTkLabel(form_frame, text="Номер сертифіката:").grid(
            row=0, column=0, sticky="w", pady=8, padx=5
        )
        self.entry_cert_number = ctk.CTkEntry(form_frame, width=300)
        self.entry_cert_number.grid(row=0, column=1, pady=8, padx=5)
        self.entry_cert_number.insert(0, "UA.")

        # Дата сертифіката
        ctk.CTkLabel(form_frame, text="Дата сертифіката:").grid(
            row=1, column=0, sticky="w", pady=8, padx=5
        )
        self.entry_cert_date = ctk.CTkEntry(form_frame, width=300)
        self.entry_cert_date.grid(row=1, column=1, pady=8, padx=5)
        self.entry_cert_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        # Номер протоколу випробувань
        ctk.CTkLabel(form_frame, text="Номер протоколу випробувань:").grid(
            row=2, column=0, sticky="w", pady=8, padx=5
        )
        self.entry_protocol_number = ctk.CTkEntry(form_frame, width=300)
        self.entry_protocol_number.grid(row=2, column=1, pady=8, padx=5)
        self.entry_protocol_number.insert(0, "0")

        # Дата протоколу
        ctk.CTkLabel(form_frame, text="Дата протоколу:").grid(
            row=3, column=0, sticky="w", pady=8, padx=5
        )
        self.entry_protocol_date = ctk.CTkEntry(form_frame, width=300)
        self.entry_protocol_date.grid(row=3, column=1, pady=8, padx=5)
        self.entry_protocol_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        # Примітка
        note_frame = ctk.CTkFrame(self.scroll_frame)
        note_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            note_frame,
            text="💡 Примітка: буде згенеровано 5 документів:\n"
            + "• Сертифікат відповідності\n"
            + "• Декларація відповідності\n"
            + "• Угода\n"
            + "• Рішення на видачу\n"
            + "• Протокол аналізування",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left",
        ).pack(anchor="w", pady=10)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ Згенерувати",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.on_generate,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=10)

        # Додаємо контекстне меню до всіх полів
        for widget in [
            self.entry_cert_number,
            self.entry_cert_date,
            self.entry_protocol_number,
            self.entry_protocol_date,
        ]:
            add_context_menu(widget, self)

    def on_generate(self):
        """Перевірка даних та повернення результату"""
        cert_number = self.entry_cert_number.get().strip()
        cert_date = self.entry_cert_date.get().strip()
        protocol_number = self.entry_protocol_number.get().strip()
        protocol_date = self.entry_protocol_date.get().strip()

        # Перевірка обов'язкових полів
        if not cert_number:
            messagebox.showerror("Помилка", "Введіть номер сертифіката!")
            return

        if not cert_date:
            messagebox.showerror("Помилка", "Введіть дату сертифіката!")
            return

        if not protocol_number:
            messagebox.showerror("Помилка", "Введіть номер протоколу випробувань!")
            return

        if not protocol_date:
            messagebox.showerror("Помилка", "Введіть дату протоколу!")
            return

        # Валідація формату дат
        for date_str in [cert_date, protocol_date]:
            try:
                datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                messagebox.showerror(
                    "Помилка",
                    f"Некоректний формат дати: {date_str}\nВикористовуйте формат: дд.мм.рррр",
                )
                return

        # Зберігаємо дані
        self.final_data = {
            "cert_number": cert_number,
            "cert_date": cert_date,
            "protocol_number": protocol_number,
            "protocol_date": protocol_date,
        }

        save_window_geometry(self, "FinalDocumentsDialog")
        self.destroy()

    def on_closing(self):
        """Закриття вікна через хрестик"""
        save_window_geometry(self, "FinalDocumentsDialog")
        self.destroy()
