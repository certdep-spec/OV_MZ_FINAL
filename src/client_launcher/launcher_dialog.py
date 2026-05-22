"""
Діалог вибору заявника (клієнта).

Показує випадаючий список заявників з БД.
При виборі — повертає об'єкт ApplicantDTO.
"""

import queue
import threading
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk
from client_launcher.applicants_db import ApplicantDTO, ApplicantsDB
from client_launcher.applicants_manager_dialog import ApplicantsManagerDialog
from client_launcher.geometry_manager import save_window_geometry


class ClientSelectorDialog(ctk.CTkToplevel):
    """Діалог вибору клієнта-заявника"""

    def __init__(self, parent=None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)

        self.title("🏢 Вибір заявника")
        self.geometry("650x340")
        self.resizable(False, False)

        if parent:
            self.transient(parent)
            self.grab_set()

        self.db = ApplicantsDB()
        self.selected_applicant: Optional[ApplicantDTO] = None

        self._create_widgets()

        # Черга для міжпотокової взаємодії
        self.queue = queue.Queue()
        self._check_queue()

        self._load_applicants()

        # Відновлення геометрії
        self.after(100, self._center_window)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _check_queue(self):
        """Перевірка черги на наявність повідомлень від фонових потоків"""
        if not self.winfo_exists():
            return

        try:
            while True:
                callback = self.queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._check_queue)

    def _center_window(self):
        """Центрування вікна на екрані"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        ctk.CTkLabel(
            self,
            text="🏢 CertifyPro — Вибір заявника",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            self,
            text="Оберіть підприємство зі списку:",
            font=ctk.CTkFont(size=14),
        ).pack(pady=(0, 5))

        # Випадаючий список
        self.combo_applicants = ctk.CTkComboBox(
            self,
            values=[],
            width=400,
            font=ctk.CTkFont(size=14),
            state="readonly",
            command=self._on_applicant_selected,
        )
        self.combo_applicants.pack(pady=5)

        # Індикатор завантаження
        self.lbl_loading = ctk.CTkLabel(
            self,
            text="⏳ Завантаження даних...",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray",
        )

        # Інформаційна рамка
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(pady=(5, 10), padx=20, fill="x")

        self.lbl_address = ctk.CTkLabel(
            self.info_frame,
            text="Адреса: —",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.lbl_address.pack(pady=3, padx=10, anchor="w")

        self.lbl_edrpou = ctk.CTkLabel(
            self.info_frame,
            text="ЄДРПОУ: —",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.lbl_edrpou.pack(pady=3, padx=10, anchor="w")

        self.lbl_director = ctk.CTkLabel(
            self.info_frame,
            text="Керівник: —",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.lbl_director.pack(pady=3, padx=10, anchor="w")

        # Змінна для збереження списку
        self._applicants_list = []

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=(10, 15))

        self.btn_registry = ctk.CTkButton(
            btn_frame,
            text="📋 Реєстр заявок",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self._on_registry,
        )
        self.btn_registry.pack(side="left", padx=10)

        self.btn_launch = ctk.CTkButton(
            btn_frame,
            text="🚀 Запустити проект",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2B7CB9",
            hover_color="#1A5F8A",
            command=self._on_launch,
            state="disabled",
        )
        self.btn_launch.pack(side="left", padx=10)

        self.btn_manage = ctk.CTkButton(
            btn_frame,
            text="⚙️ Керувати заявниками",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#2E8B57",
            hover_color="#236B43",
            command=self._on_manage,
        )
        self.btn_manage.pack(side="left", padx=10)

        self.btn_exit = ctk.CTkButton(
            btn_frame,
            text="❌ Вихід",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="#555",
            command=self._on_exit,
        )
        self.btn_exit.pack(side="left", padx=10)

    def _load_applicants(self):
        """Завантаження заявників з БД у фоновому режимі"""
        self.lbl_loading.pack(pady=5)
        self.combo_applicants.configure(state="disabled")

        def _bg_load():
            try:
                applicants = self.db.get_all_applicants()
                self.queue.put(lambda: self._on_applicants_loaded(applicants))
            except Exception:
                self.queue.put(
                    lambda: messagebox.showerror(
                        "Помилка", f"Помилка завантаження: {e}"
                    )
                )

        threading.Thread(target=_bg_load, daemon=True).start()

    def _on_applicants_loaded(self, applicants):
        """Викликається коли дані завантажені"""
        self.lbl_loading.pack_forget()
        self.combo_applicants.configure(state="readonly")

        if not applicants:
            messagebox.showwarning(
                "Увага",
                "Немає зареєстрованих заявників.\nНатисніть 'Керувати заявниками' щоб додати.",
            )
            return

        self._applicants_list = applicants
        display_values = [a.nazva_pidpryyemstva for a in applicants]
        self.combo_applicants.configure(values=display_values)
        self.combo_applicants.set(display_values[0])
        self._on_applicant_selected(None)

    def _on_applicant_selected(self, selected_name=None):
        """Обробка вибору заявника"""
        if selected_name is None:
            selected_name = self.combo_applicants.get()

        for applicant in self._applicants_list:
            if applicant.nazva_pidpryyemstva == selected_name:
                self.lbl_address.configure(
                    text=f"📍 Адреса: {applicant.adresa_pidpryyemstva}"
                )
                self.lbl_edrpou.configure(text=f"🔢 ЄДРПОУ: {applicant.kod_edrpou}")
                self.lbl_director.configure(text=f"👤 Керівник: {applicant.kerivnik}")
                self.btn_launch.configure(state="normal")
                break

    def _on_registry(self):
        """Відкрити реєстр заявок (спочатку вибір періоду)"""
        from client_launcher.date_range_dialog import DateRangeDialog
        from client_launcher.registry_dialog import RegistryDialog

        # Діалог вибору періоду
        date_dialog = DateRangeDialog(self)
        self.wait_window(date_dialog)

        if date_dialog.date_from is None:
            return  # Скасовано

        # Відкриваємо реєстр з фільтром
        dialog = RegistryDialog(
            self,
            date_from=date_dialog.date_from,
            date_to=date_dialog.date_to,
        )
        self.wait_window(dialog)

    def _on_launch(self):
        """Запуск проекту обраного заявника"""
        selected_name = self.combo_applicants.get()

        for applicant in self._applicants_list:
            if applicant.nazva_pidpryyemstva == selected_name:
                self.selected_applicant = applicant
                self.destroy()
                return

    def _on_manage(self):
        """Відкрити управління заявниками"""
        dialog = ApplicantsManagerDialog(self)
        self.wait_window(dialog)

        # Перезавантажуємо список після редагування
        self._load_applicants()

    def _on_exit(self):
        """Вихід"""
        self.selected_applicant = None
        self._on_close()

    def _on_close(self):
        """Збереження геометрії перед закриттям"""
        save_window_geometry(self, "ClientSelectorDialog")
        self.destroy()
