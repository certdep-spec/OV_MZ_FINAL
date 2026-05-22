"""
Форма створення нової заявки
Підтримує ручне введення та імпорт з Excel
З ВИБОРОМ ПРОДУКЦІЇ та СТАНДАРТІВ для випробувань
"""

import logging
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Dict

import customtkinter as ctk

import config
from gui.client_badge import add_client_badge
from gui.gui_utils import (
    add_context_menu,
    restore_window_geometry,
    save_window_geometry,
)

logger = logging.getLogger(__name__)


from gui.handlers.data_handler import DataPersistenceHandler
from gui.handlers.document_handler import DocumentGenerationHandler
from gui.widgets import (
    PartyDetailsDialog,
    ProductSelectionDialog,
)


class AppFormWindow(ctk.CTkToplevel):
    def __init__(self, parent, app_service, doc_gen, dict_service, app_data=None):
        super().__init__(parent)

        self.title(
            "📝 Нова Заявка"
            if not app_data
            else f"📝 Заявка №{app_data.get('app_number', '')}"
        )
        self.geometry("1000x750")
        self.transient(parent)
        self.grab_set()

        self.after(
            100,
            lambda: restore_window_geometry(self, "AppFormWindow", 1000, 750),
        )
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

        self.app_service = app_service
        self.db = app_service  # Для зворотної сумісності з діалогами
        self.doc_gen = doc_gen
        self.dict_service = dict_service
        self.parties = []
        self.existing_app_data = app_data

        # Ініціалізація хендлерів логіки
        self.data_handler = DataPersistenceHandler(self)
        self.doc_handler = DocumentGenerationHandler(self)

        self.create_widgets()

        # АВТОЗАПОВНЕННЯ: Якщо довідники пусті - додаємо дані з конфігу клієнта
        self._auto_populate_dictionaries_if_empty()

        # Якщо це існуюча заявка - заповнюємо дані
        if app_data:
            self.load_app_data(app_data)

    def load_app_data(self, app_data):
        """Заповнення форми даними існуючої заявки"""
        self.entry_app_number.delete(0, "end")
        self.entry_app_number.insert(0, str(app_data.get("app_number", "")))

        self.entry_app_date.delete(0, "end")
        self.entry_app_date.insert(0, str(app_data.get("app_date", "")))

        self.entry_company.delete(0, "end")
        self.entry_company.insert(0, str(app_data.get("company_name", "")))

        self.entry_code.delete(0, "end")
        self.entry_code.insert(0, str(app_data.get("company_code", "")))

        self.entry_director.delete(0, "end")
        self.entry_director.insert(0, str(app_data.get("director_name", "")))

        self.combo_tu.set(app_data.get("tu_code", ""))
        self.combo_address.set(app_data.get("production_address", ""))

        # Завантажуємо партії
        if app_data.get("parties"):
            self.parties = app_data["parties"]
            self.refresh_parties_table()
        elif app_data.get("id"):
            # Якщо партій у app_data нема, але є ID заявки - загружаємо через сервіс
            app_id = int(app_data["id"])
            db_parties = self.app_service.get_parties_for_application(app_id)
            if db_parties:
                # Конвертуємо DTO у dict для сумісності з UI
                self.parties = [
                    {
                        "id": p.id,
                        "product_name": p.product_name,
                        "party_code": p.party_code,
                        "party_date": p.party_date,
                        "mfg_date": p.mfg_date,
                        "quantity": p.quantity,
                        "unit": p.unit,
                        "shelf_life_months": p.shelf_life_months,
                        "standards": p.standards,
                        "protocol_number": p.protocol_number,
                        "protocol_date": p.protocol_date,
                        "cert_number": p.cert_number,
                        "cert_date": p.cert_date,
                        "version": p.version,
                    }
                    for p in db_parties
                ]
                self.refresh_parties_table()

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📝 Створення Нової Заявки",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=15)

        # Прокрутка
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Поля заявки
        self.create_app_fields()

        # Таблиця партій
        self.create_parties_table()

        # Кнопки
        self.create_buttons()

    def create_app_fields(self):
        """Поля даних заявки з ВИПАДАЮЧИМИ СПИСКАМИ"""
        fields_frame = ctk.CTkFrame(self.scroll_frame)
        fields_frame.pack(fill="x", pady=10)

        # Номер заявки
        ctk.CTkLabel(fields_frame, text="Номер заявки:").grid(
            row=0, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_app_number = ctk.CTkEntry(fields_frame, width=200)
        self.entry_app_number.grid(row=0, column=1, pady=5, padx=5)
        # Отримуємо наступний номер заявки через сервіс
        last_num = self.app_service.get_last_app_number()
        # Інкремент номера
        try:
            next_num = str(int(last_num) + 1).zfill(len(last_num) or 1)
        except ValueError:
            next_num = "1"
        self.entry_app_number.insert(0, next_num)

        # Дата заявки
        ctk.CTkLabel(fields_frame, text="Дата заявки:").grid(
            row=0, column=2, sticky="w", pady=5, padx=5
        )
        self.entry_app_date = ctk.CTkEntry(fields_frame, width=200)
        self.entry_app_date.grid(row=0, column=3, pady=5, padx=5)
        self.entry_app_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        # Підприємство
        ctk.CTkLabel(fields_frame, text="Підприємство:").grid(
            row=1, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_company = ctk.CTkEntry(fields_frame, width=400)
        self.entry_company.grid(
            row=1, column=1, columnspan=3, pady=5, padx=5, sticky="ew"
        )
        self.entry_company.insert(0, config.DEFAULT_COMPANY or "")

        # ЄДРПОУ
        ctk.CTkLabel(fields_frame, text="ЄДРПОУ:").grid(
            row=2, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_code = ctk.CTkEntry(fields_frame, width=200)
        self.entry_code.grid(row=2, column=1, pady=5, padx=5)
        self.entry_code.insert(0, config.DEFAULT_COMPANY_CODE or "")

        # ===== АДРЕСА ПОТУЖНОСТЕЙ (ВИПАДАЮЧИЙ СПИСОК) =====
        ctk.CTkLabel(fields_frame, text="Адреса потужностей:").grid(
            row=3, column=0, sticky="w", pady=5, padx=5
        )

        # Фрейм для комбобокса + кнопки
        address_frame = ctk.CTkFrame(fields_frame)
        address_frame.grid(row=3, column=1, columnspan=3, pady=5, padx=5, sticky="ew")

        facilities = self.dict_service.get_all_facilities()
        facility_values = [f.address for f in facilities] if facilities else [""]

        self.combo_address = ctk.CTkComboBox(
            address_frame, values=facility_values, width=360
        )
        self.combo_address.pack(side="left", fill="x", expand=True, padx=(0, 5))
        if facility_values and facility_values[0]:
            self.combo_address.set(facility_values[0])

        # Кнопка "+" для быстрого добавления адреса
        btn_add_address = ctk.CTkButton(
            address_frame,
            text="+",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self._add_new_facility,
        )
        btn_add_address.pack(side="left")

        # Директор
        ctk.CTkLabel(fields_frame, text="Директор:").grid(
            row=4, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_director = ctk.CTkEntry(fields_frame, width=400)
        self.entry_director.grid(
            row=4, column=1, columnspan=3, pady=5, padx=5, sticky="ew"
        )
        self.entry_director.insert(0, config.DEFAULT_DIRECTOR or "")

        # ===== ТУ (ВИПАДАЮЧИЙ СПИСОК) =====
        ctk.CTkLabel(fields_frame, text="ТУ:").grid(
            row=5, column=0, sticky="w", pady=5, padx=5
        )

        # Фрейм для комбобокса + кнопки
        tu_frame = ctk.CTkFrame(fields_frame)
        tu_frame.grid(row=5, column=1, columnspan=3, pady=5, padx=5, sticky="ew")

        products = self.dict_service.get_all_products() if self.dict_service else []
        tu_codes = (
            list({p.tu_code for p in products if p.tu_code}) if products else set()
        )
        tu_values = sorted(tu_codes) if tu_codes else [""]

        self.combo_tu = ctk.CTkComboBox(
            tu_frame, values=tu_values, width=360, command=self.on_tu_changed
        )
        self.combo_tu.pack(side="left", fill="x", expand=True, padx=(0, 5))
        if tu_values and tu_values[0]:
            self.combo_tu.set(tu_values[0])

        # Кнопка "+" для быстрого добавления нового ТУ
        btn_add_tu = ctk.CTkButton(
            tu_frame,
            text="+",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self._add_new_product,
        )
        btn_add_tu.pack(side="left")

        # Додаємо контекстне меню до всіх полів
        add_context_menu(self.entry_app_number, self)
        add_context_menu(self.entry_app_date, self)
        add_context_menu(self.entry_company, self)
        add_context_menu(self.entry_code, self)
        add_context_menu(self.combo_address, self)
        add_context_menu(self.entry_director, self)
        add_context_menu(self.combo_tu, self)

    def on_tu_changed(self, event=None):
        """Обробка зміни ТУ"""

    def _add_new_facility(self):
        """Швидке додавання нової виробничої потужності (адреси)"""
        # Відкриваємо вікно довідників на вкладці "Потужності"
        from gui.dictionaries_window import DictionariesWindow

        dict_window = DictionariesWindow(self, self.dict_service)
        self.wait_window(dict_window)

        # Після закриття довідника оновлюємо випадаючий список
        facilities = self.dict_service.get_all_facilities()
        facility_values = [f.address for f in facilities]
        self.combo_address.configure(values=facility_values)
        if facility_values:
            self.combo_address.set(facility_values[-1])  # Вибираємо останній доданий

    def _add_new_product(self):
        """Швидке додавання нової продукції (ТУ)"""
        # Відкриваємо вікно довідників на вкладці "Продукція"
        from gui.dictionaries_window import DictionariesWindow

        dict_window = DictionariesWindow(self, self.dict_service)
        self.wait_window(dict_window)

        # Після закриття довідника оновлюємо випадаючий список
        products = self.dict_service.get_all_products() if self.dict_service else []
        tu_codes = list({p.tu_code for p in products if p.tu_code})
        tu_values = sorted(tu_codes)
        self.combo_tu.configure(values=tu_values)
        if tu_values:
            self.combo_tu.set(tu_values[-1])  # Вибираємо останній доданий

    def _auto_populate_dictionaries_if_empty(self):
        """
        Перевірка довідників при відкритті заявки.

        Якщо довідники пусті, пропонуємо користувачу відкрити вікно довідників
        для заповнення необхідних даних.
        """
        try:
            # Перевіряємо чи є потужності
            facilities = self.dict_service.get_all_facilities() if self.dict_service else []
            if not facilities:
                logger.info("⚠️ Довідник потужностей пустий")

            # Перевіряємо чи є продукція
            products = self.dict_service.get_all_products() if self.dict_service else []
            if not products:
                logger.info("⚠️ Довідник продукції пустий")

            # Якщо обидва довідники пусті - пропонуємо відкрити вікно довідників
            if not facilities and not products:
                result = messagebox.askyesno(
                    "Довідники пусті",
                    "⚠️ Довідники потужностей та продукції не заповнено.\n\n"
                    "Бажаєте відкрити вікно управління довідниками\n"
                    "для додавання необхідних даних?",
                    parent=self,
                )

                if result:
                    # Відкриваємо вікно довідників
                    from gui.dictionaries_window import DictionariesWindow

                    dict_window = DictionariesWindow(self, self.dict_service)
                    self.wait_window(dict_window)

                    # Після закриття оновлюємо випадаючі списки
                    self._refresh_dropdown_lists()

        except Exception as e:
            # Не блокуємо форму якщо перевірка не вдалася
            logger.warning(f"⚠️ Помилка перевірки довідників: {e}")

    def _refresh_dropdown_lists(self):
        """Оновити всі випадаючі списки на формі"""
        # Оновлюємо список потужностей
        facilities = self.dict_service.get_all_facilities() if self.dict_service else []
        facility_values = [f.address for f in facilities]
        self.combo_address.configure(values=facility_values)
        if facility_values:
            self.combo_address.set(facility_values[0])

        # Оновлюємо список ТУ
        products = self.dict_service.get_all_products() if self.dict_service else []
        tu_codes = list({p.tu_code for p in products if p.tu_code})
        tu_values = sorted(tu_codes)
        self.combo_tu.configure(values=tu_values)
        if tu_values:
            self.combo_tu.set(tu_values[0])

        logger.info("✅ Випадаючі списки оновлено")

    def _save_application_and_parties(self, app_data: Dict, parties: list) -> dict:
        """Делегування збереження хендлеру"""
        return self.data_handler.save_all(app_data, parties)

    def create_parties_table(self):
        """Таблиця партій"""
        parties_frame = ctk.CTkFrame(self.scroll_frame)
        parties_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            parties_frame,
            text="📦 Партії Продукції",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=5)

        # Кнопки
        btn_frame = ctk.CTkFrame(parties_frame)
        btn_frame.pack(pady=5)

        ctk.CTkButton(btn_frame, text="➕ Додати партію", command=self.add_party).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            btn_frame,
            text="🗑️ Видалити",
            command=self.remove_party,
            fg_color="red",
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame,
            text="✏️ Редагувати",
            command=self.edit_party,
            fg_color=config.COLORS["info"],
        ).pack(side="left", padx=5)

        # Таблиця
        columns = (
            "№",
            "Продукт",
            "Код партії",
            "Версія",
            "Дата партії",
            "Кількість",
            "Одиниця",
            "Стандарти",
        )
        self.tree = ttk.Treeview(
            parties_frame, columns=columns, show="headings", height=8
        )

        self.tree.heading("№", text="№")
        self.tree.heading("Продукт", text="Продукт")
        self.tree.heading("Код партії", text="Код")
        self.tree.heading("Версія", text="Версія")
        self.tree.heading("Дата партії", text="Дата")
        self.tree.heading("Кількість", text="Кількість")
        self.tree.heading("Одиниця", text="Од.")
        self.tree.heading("Стандарти", text="Стандарти")

        self.tree.column("№", width=30, anchor="center")
        self.tree.column("Продукт", width=300, stretch=True)
        self.tree.column("Код партії", width=80, anchor="center")
        self.tree.column("Версія", width=60, anchor="center")
        self.tree.column("Дата партії", width=90, anchor="center")
        self.tree.column("Кількість", width=80, anchor="center")
        self.tree.column("Одиниця", width=40, anchor="center")
        self.tree.column("Стандарти", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, pady=5)

    def create_buttons(self):
        """Кнопки дій"""
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        # ✅ КНОПКА 0: Зберегти зміни
        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Зберегти",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.save_app_now,
        )
        self.btn_save.pack(side="left", padx=10)

        # ✅ КНОПКА 1: Документи для ВЦ (до випробувань)
        self.btn_gen_vc = ctk.CTkButton(
            btn_frame,
            text="📋 Документи для ВЦ",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["info"],
            command=self.generate_vc_now,
        )
        self.btn_gen_vc.pack(side="left", padx=10)

        # ✅ КНОПКА 2: Фінальні документи (після випробувань) - ЗАГОТОВКА
        self.btn_gen_final = ctk.CTkButton(
            btn_frame,
            text="✅ Фінальні документи",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.generate_final_documents,
        )
        self.btn_gen_final.pack(side="left", padx=10)

        # Кнопка "Скасувати"
        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            command=self._on_close,
        ).pack(side="left", padx=10)

    def save_app_now(self):
        """Зберегти поточний стан заявки в БД"""
        app_number = self.entry_app_number.get().strip()
        if not app_number:
            messagebox.showerror("Помилка", "Заповніть номер заявки!")
            return False

        app_data = {
            "app_number": app_number,
            "app_date": self.entry_app_date.get(),
            "company_name": self.entry_company.get(),
            "company_code": self.entry_code.get(),
            "company_address": self.combo_address.get(),
            "director_name": self.entry_director.get(),
            "tu_code": self.combo_tu.get(),
            "production_address": self.combo_address.get(),
        }

        # Якщо ми редагуємо існуючу заявку, додаємо її ID
        if self.existing_app_data and self.existing_app_data.get("id"):
            app_data["id"] = self.existing_app_data["id"]

        try:
            self._save_application_and_parties(app_data, self.parties)
            messagebox.showinfo("Успіх", "✅ Зміни збережено в базу даних!")
            return True
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти дані: {str(e)}")
            return False

    def _on_close(self):
        """Збереження геометрії та закриття вікна (з перевіркою змін)"""
        # Перевірка чи хоче користувач зберегти зміни
        if self.parties:
            resp = messagebox.askyesnocancel(
                "Збереження", "Бажаєте зберегти зміни перед закриттям?", parent=self
            )
            if resp is True:  # Yes
                if not self.save_app_now():
                    return  # Не закриваємо якщо помилка збереження
            elif resp is None:  # Cancel
                return

        save_window_geometry(self, "AppFormWindow")
        self.destroy()

    def generate_vc_now(self):
        """Делегування генерації ВЦ хендлеру"""
        app_number = self.entry_app_number.get().strip()
        if not app_number:
            messagebox.showerror("Помилка", "Заповніть номер заявки!")
            return

        if not self.parties:
            messagebox.showerror("Помилка", "Додайте хоча б одну партію!")
            return

        app_data = {
            "app_number": app_number,
            "app_date": self.entry_app_date.get(),
            "company_name": self.entry_company.get(),
            "company_code": self.entry_code.get(),
            "company_address": self.combo_address.get(),
            "director_name": self.entry_director.get(),
            "tu_code": self.combo_tu.get(),
            "production_address": self.combo_address.get(),
        }

        self.doc_handler.generate_vc(app_data, self.parties)

    def generate_final_documents(self):
        """Делегування генерації фінальних документів хендлеру"""
        app_number = self.entry_app_number.get().strip()
        if not app_number:
            messagebox.showerror("Помилка", "Заповніть номер заявки!")
            return

        if not self.parties:
            messagebox.showerror("Помилка", "Додайте хоча б одну партію!")
            return

        app_data = {
            "app_number": app_number,
            "app_date": self.entry_app_date.get(),
            "company_name": self.entry_company.get(),
            "company_code": self.entry_code.get(),
            "company_address": self.combo_address.get(),
            "director_name": self.entry_director.get(),
            "tu_code": self.combo_tu.get(),
            "production_address": self.combo_address.get(),
        }

        try:
            # Делегуємо всю логіку збереження та генерації хендлеру
            self.doc_handler.generate_final(app_data, self.parties)

        except Exception as e:
            logger.error(f"Помилка підготовки фінальних документів: {e}", exc_info=True)
            messagebox.showerror("Помилка", str(e))

    def add_party(self):
        """Додати партію з ВИБОРОМ ПРОДУКЦІЇ та СТАНДАРТІВ"""
        # Крок 1: Вибір продукції
        selected_tu = self.combo_tu.get()
        dialog = ProductSelectionDialog(self, self.dict_service, selected_tu)
        self.wait_window(dialog)

        if dialog.selected_product is None:
            return  # Користувач скасував вибір

        # Крок 2: Введення деталей партії (з вибором стандартів)
        party_dialog = PartyDetailsDialog(
            self, self.dict_service, dialog.selected_product["name"]
        )
        self.wait_window(party_dialog)

        if party_dialog.party_data is None:
            return  # Користувач скасував введення

        # Додаємо партію з даними
        self.parties.append(
            {
                "product_name": party_dialog.party_data["product_name"],
                "party_code": party_dialog.party_data["party_code"],
                "party_date": party_dialog.party_data["party_date"],
                "mfg_date": party_dialog.party_data["mfg_date"],
                "quantity": party_dialog.party_data["quantity"],
                "unit": party_dialog.party_data.get("unit", "шт"),
                "version": party_dialog.party_data.get("version", ""),
                "shelf_life_months": dialog.selected_product["shelf_life"],
                "standards": party_dialog.party_data.get("standards", []),
            }
        )
        self.refresh_parties_table()

    def edit_party(self):
        """Редагувати вибрану партію"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть партію для редагування!")
            return

        index = self.tree.index(selected[0])
        if not (0 <= index < len(self.parties)):
            return

        party = self.parties[index]

        # Відкриваємо діалог редагування
        dialog = PartyDetailsDialog(self, self.dict_service, party["product_name"])

        # Заповнюємо існуючими даними
        dialog.entry_party_code.delete(0, "end")
        dialog.entry_party_code.insert(0, str(party["party_code"]))
        dialog.entry_party_date.delete(0, "end")
        dialog.entry_party_date.insert(0, str(party["party_date"]))
        dialog.entry_mfg_date.delete(0, "end")
        dialog.entry_mfg_date.insert(0, str(party["mfg_date"]))
        dialog.entry_quantity.delete(0, "end")
        # Форматуємо кількість: якщо ціле – без .0
        quantity = party["quantity"]
        if isinstance(quantity, (int, float)) and float(quantity).is_integer():
            quantity_str = str(int(quantity))
        else:
            quantity_str = str(quantity)
        dialog.entry_quantity.insert(0, quantity_str)
        if "unit" in party:
            dialog.combo_unit.set(str(party["unit"]))
        if "version" in party and party["version"]:
            dialog.combo_version.set(str(party["version"]))

        # Заповнюємо стандарти
        if party.get("standards"):
            dialog.selected_standards = party["standards"]
            # Формуємо список ID стандартів (тепер це завжди список int)
            std_ids = [str(s) for s in party["standards"]]
            std_text = ", ".join(std_ids)
            dialog.entry_standards_display.configure(state="normal")
            dialog.entry_standards_display.delete(0, "end")
            dialog.entry_standards_display.insert(0, std_text)
            dialog.entry_standards_display.configure(state="disabled")
            dialog.lbl_standards_count.configure(
                text=f"✅ Обрано стандартів: {len(party['standards'])} ({std_text})",
                text_color=config.COLORS["success"],
            )

        self.wait_window(dialog)

        if dialog.party_data is not None:
            # Оновлюємо дані, зберігаючи фінальні документи та ID
            self.parties[index] = {
                "id": party.get("id"),  # зберігаємо ID
                "product_name": dialog.product_name.strip(),
                "party_code": dialog.party_data["party_code"],
                "party_date": dialog.party_data["party_date"],
                "mfg_date": dialog.party_data["mfg_date"],
                "quantity": dialog.party_data["quantity"],
                "unit": dialog.party_data.get("unit", "шт"),
                "version": dialog.party_data.get("version", ""),
                "shelf_life_months": party["shelf_life_months"],
                "standards": dialog.party_data.get("standards", []),
                # Зберігаємо фінальні документи (не змінюються при редагуванні партії)
                "protocol_number": party.get("protocol_number", ""),
                "protocol_date": party.get("protocol_date", ""),
                "cert_number": party.get("cert_number", ""),
                "cert_date": party.get("cert_date", ""),
            }
            self.refresh_parties_table()

    def remove_party(self):
        """Видалити партію"""
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected[0])
            if 0 <= index < len(self.parties):
                self.parties.pop(index)
                self.refresh_parties_table()

    def refresh_parties_table(self):
        """Оновити таблицю партій"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, party in enumerate(self.parties, 1):
            # Форматуємо кількість: якщо ціле число – без .0
            quantity = party["quantity"]
            if isinstance(quantity, int):
                quantity_str = str(quantity)
            elif isinstance(quantity, float):
                quantity_str = (
                    str(int(quantity)) if quantity.is_integer() else str(quantity)
                )
            else:
                quantity_str = str(quantity)

            self.tree.insert(
                "",
                "end",
                values=(
                    i,
                    party["product_name"],
                    party["party_code"],
                    party.get("version", ""),
                    party["party_date"],
                    quantity_str,
                    party.get("unit", "шт"),
                    ", ".join([str(s) for s in party.get("standards", [])]),
                ),
            )
