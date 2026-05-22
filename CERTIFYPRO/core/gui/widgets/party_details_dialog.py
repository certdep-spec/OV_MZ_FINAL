"""
Діалогові вікна для введення деталей партії та фінальних документів
"""

import logging
from datetime import datetime
from tkinter import messagebox
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


class PartyDetailsDialog(ctk.CTkToplevel):
    """Діалогове вікно для введення деталей партії з ВИБОРОМ СТАНДАРТІВ"""

    def __init__(self, parent, dict_service, product_name):
        super().__init__(parent)

        self.title("📦 Деталі Партії")
        self.geometry("550x550")
        self.transient(parent)
        self.grab_set()

        self.dict_service = dict_service
        self.db = dict_service  # Для зворотної сумісності
        self.product_name = product_name
        self.party_data = None

        self.create_widgets()

        # Восстанавливаем сохраненную геометрию
        self.after(
            100,
            lambda: restore_window_geometry(self, "PartyDetailsDialog", 550, 550),
        )

        # Привязываем функцию сохранения геометрии при закрытии
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📦 Деталі Партії",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=15)

        # Прокрутка
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Продукт (тільки для перегляду)
        info_frame = ctk.CTkFrame(self.scroll_frame)
        info_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            info_frame,
            text="Продукт:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=5, padx=5)

        ctk.CTkLabel(
            info_frame,
            text=self.product_name[:50]
            + ("..." if len(self.product_name) > 50 else ""),
            font=ctk.CTkFont(size=12),
            width=450,
            anchor="w",
        ).grid(row=0, column=1, pady=5, padx=5, sticky="w")

        # Поля введення
        entry_frame = ctk.CTkFrame(self.scroll_frame)
        entry_frame.pack(fill="x", pady=10)

        # Код партії
        ctk.CTkLabel(entry_frame, text="Код партії:").grid(
            row=0, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_party_code = ctk.CTkEntry(entry_frame, width=250)
        self.entry_party_code.grid(row=0, column=1, pady=5, padx=5)
        self.entry_party_code.insert(0, "01E")

        # Версія (склад)
        ctk.CTkLabel(entry_frame, text="Версія (склад):").grid(
            row=1, column=0, sticky="w", pady=5, padx=5
        )
        # Завантажуємо доступні версії
        available_versions = (
            self.dict_service.get_unique_versions_for_product(self.product_name)
            if self.dict_service
            else []
        )
        self.combo_version = ctk.CTkComboBox(
            entry_frame, values=available_versions, width=250
        )
        self.combo_version.grid(row=1, column=1, pady=5, padx=5)
        if available_versions:
            self.combo_version.set(available_versions[0])

        # Дата партії
        ctk.CTkLabel(entry_frame, text="Дата партії:").grid(
            row=2, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_party_date = ctk.CTkEntry(entry_frame, width=250)
        self.entry_party_date.grid(row=2, column=1, pady=5, padx=5)
        self.entry_party_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        # Дата виробництва
        ctk.CTkLabel(entry_frame, text="Дата виробництва:").grid(
            row=3, column=0, sticky="w", pady=5, padx=5
        )
        self.entry_mfg_date = ctk.CTkEntry(entry_frame, width=250)
        self.entry_mfg_date.grid(row=3, column=1, pady=5, padx=5)
        self.entry_mfg_date.insert(0, datetime.now().strftime("%d.%m.%Y"))

        # Кількість та Одиниця виміру
        qty_unit_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        qty_unit_frame.grid(row=4, column=0, columnspan=2, pady=5, padx=5, sticky="ew")

        ctk.CTkLabel(qty_unit_frame, text="Кількість:").pack(side="left", padx=5)
        self.entry_quantity = ctk.CTkEntry(qty_unit_frame, width=150)
        self.entry_quantity.pack(side="left", padx=5)
        # Значення за замовчуванням – ціле число
        self.entry_quantity.insert(0, "1000")

        ctk.CTkLabel(qty_unit_frame, text="Одиниця:").pack(side="left", padx=5)
        self.combo_unit = ctk.CTkComboBox(
            qty_unit_frame,
            values=["шт", "кг", "мл", "л", "банка", "уп", "г", "м", "м.п."],
            width=100,
        )
        self.combo_unit.pack(side="left", padx=5)
        self.combo_unit.set("шт")

        add_context_menu(self.entry_party_code, self)
        add_context_menu(self.entry_party_date, self)
        add_context_menu(self.entry_mfg_date, self)
        add_context_menu(self.entry_quantity, self)
        add_context_menu(self.combo_unit, self)

        # ===== ВИБІР СТАНДАРТІВ =====
        standards_frame = ctk.CTkFrame(self.scroll_frame)
        standards_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            standards_frame,
            text="📋 Стандарти для випробувань:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=5)

        # Поле для відображення вибраних стандартів
        self.entry_standards_display = ctk.CTkEntry(
            standards_frame, width=450, state="disabled"
        )
        self.entry_standards_display.pack(pady=5)

        # Кнопка вибору стандартів
        self.btn_select_standards = ctk.CTkButton(
            standards_frame,
            text="📋 Обрати стандарти",
            height=30,
            command=self.select_standards,
        )
        self.btn_select_standards.pack(pady=5)

        # Мітка для кількості вибраних стандартів
        self.lbl_standards_count = ctk.CTkLabel(
            standards_frame,
            text="❌ Стандарти не обрано",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.lbl_standards_count.pack(pady=5)

        self.selected_standards = []

        # ===== КНОПКА ЗБЕРЕЖЕННЯ =====
        save_frame = ctk.CTkFrame(self)
        save_frame.pack(pady=15)

        ctk.CTkButton(
            save_frame,
            text="✅ Зберегти партію",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.on_save,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            save_frame,
            text="❌ Скасувати",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            command=self.destroy,
        ).pack(side="left", padx=10)

    def select_standards(self):
        """Відкриття діалогу вибору стандартів"""
        from gui.widgets.standards_selection_dialog import (
            StandardsSelectionDialog,
        )

        dialog = StandardsSelectionDialog(self, self.dict_service)
        self.wait_window(dialog)

        if dialog.selected_standards:
            self.selected_standards = dialog.selected_standards

            # Формуємо список ID стандартів (тепер це завжди список int)
            std_ids = [str(s) for s in self.selected_standards]
            std_text = ", ".join(std_ids)

            # Оновлюємо відображення
            self.entry_standards_display.configure(state="normal")
            self.entry_standards_display.delete(0, "end")
            self.entry_standards_display.insert(0, std_text)
            self.entry_standards_display.configure(state="disabled")

            self.lbl_standards_count.configure(
                text=f"✅ Обрано стандартів: {len(self.selected_standards)} ({std_text})",
                text_color=config.COLORS["success"],
            )

    def on_closing(self):
        """Сохранение геометрии перед закрытием"""
        save_window_geometry(self, "PartyDetailsDialog")
        self.destroy()

    def on_save(self):
        """Збереження даних партії"""
        party_code = self.entry_party_code.get().strip()
        party_date = self.entry_party_date.get().strip()
        mfg_date = self.entry_mfg_date.get().strip()
        quantity_str = self.entry_quantity.get().replace(",", ".").strip()
        unit = self.combo_unit.get().strip()

        # Перевірка
        if not party_code:
            messagebox.showerror("Помилка", "Введіть код партії!")
            return

        if not party_date:
            messagebox.showerror("Помилка", "Введіть дату партії!")
            return

        if not mfg_date:
            messagebox.showerror("Помилка", "Введіть дату виробництва!")
            return

        try:
            quantity = float(quantity_str)
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректну кількість (число)!")
            return

        # Зберігаємо дані
        self.party_data = {
            "product_name": self.product_name,
            "party_code": party_code,
            "party_date": party_date,
            "mfg_date": mfg_date,
            "quantity": quantity,
            "unit": unit,
            "version": self.combo_version.get().strip(),
            "standards": self.selected_standards,
        }

        logger.info(
            f"✅ Збережено партію: {party_code}, Версія: {self.combo_version.get()}, Стандарти: {len(self.selected_standards)}"
        )
        self.on_closing()


class FinalDocumentsPerPartyDialog(ctk.CTkToplevel):
    """Диалог одновременно показывает данные партии и запрашивает финальные данные"""

    def __init__(self, parent, party_data: Dict, party_index: int = 1):
        super().__init__(parent)

        self.title(f"📜 Фінальні дані Партії {party_index}")
        self.geometry("600x600")
        self.transient(parent)
        self.grab_set()

        self.party_data = party_data
        self.party_index = party_index
        self.final_data = None

        self.create_widgets()

        # Восстанавливаем сохраненную геометрию
        self.after(
            100,
            lambda: restore_window_geometry(
                self, "FinalDocumentsPerPartyDialog", 600, 600
            ),
        )

        # Привязываем функцию сохранения геометрии при закрытии
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Бейдж клієнта
        self.after(200, lambda: add_client_badge(self))

    def create_widgets(self):
        # Заголовок
        ctk.CTkLabel(
            self,
            text=f"📜 Фінальні Дані для Партії #{self.party_index}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=15)

        # Прокрутка
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ===== ІНФОРМАЦІЯ ПРО ПАРТІЮ (тільки для перегляду) =====
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="📦 ІНФОРМАЦІЯ ПРО ПАРТІЮ:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2B7CB9",
        )
        info_label.pack(anchor="w", pady=(10, 5))

        info_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2B2B2B")
        info_frame.pack(fill="x", pady=5)

        # Розташовуємо інформацію в два стовпці
        info_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_grid.pack(fill="x", padx=10, pady=10)

        # Лів ий стовпець
        ctk.CTkLabel(
            info_grid,
            text="Продукт:",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=3)

        ctk.CTkLabel(
            info_grid,
            text=self.party_data.get("product_name", "N/A"),
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=1, sticky="w", padx=10, pady=3)

        ctk.CTkLabel(
            info_grid,
            text="Код партії:",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=1, column=0, sticky="w", pady=3)

        ctk.CTkLabel(
            info_grid,
            text=self.party_data.get("party_code", "N/A"),
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=1, sticky="w", padx=10, pady=3)

        ctk.CTkLabel(
            info_grid,
            text="Дата партії:",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=2, column=0, sticky="w", pady=3)

        ctk.CTkLabel(
            info_grid,
            text=self.party_data.get("party_date", "N/A"),
            font=ctk.CTkFont(size=10),
        ).grid(row=2, column=1, sticky="w", padx=10, pady=3)

        # Правий стовпець
        ctk.CTkLabel(
            info_grid,
            text="Кількість:",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=2, sticky="w", pady=3, padx=(20, 0))

        # Форматуємо кількість для відображення
        quantity_value = self.party_data.get("quantity", "N/A")
        if isinstance(quantity_value, (int, float)):
            quantity_display = (
                str(int(quantity_value))
                if float(quantity_value).is_integer()
                else str(quantity_value)
            )
        else:
            quantity_display = str(quantity_value)

        ctk.CTkLabel(
            info_grid,
            text=f"{quantity_display} {self.party_data.get('unit', 'шт')}",
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=3, sticky="w", padx=10, pady=3)

        ctk.CTkLabel(
            info_grid,
            text=self.party_data.get("mfg_date", "N/A"),
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=3, sticky="w", padx=10, pady=3)

        # Версія складу
        ctk.CTkLabel(
            info_grid,
            text="Версія:",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=2, column=2, sticky="w", pady=3, padx=(20, 0))

        ctk.CTkLabel(
            info_grid,
            text=self.party_data.get("version", "N/A") or "N/A",
            font=ctk.CTkFont(size=10),
            text_color="#FFD700" if self.party_data.get("version") else "gray",
        ).grid(row=2, column=3, sticky="w", padx=10, pady=3)

        # ===== ФОРМА ДЛЯ ВВЕДЕННЯ ФІНАЛЬНИХ ДАНИХ =====
        form_label = ctk.CTkLabel(
            self.scroll_frame,
            text="🔐 ДАНІ СЕРТИФІКАЦІЇ:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2E8B57",
        )
        form_label.pack(anchor="w", pady=(20, 5))

        form_frame = ctk.CTkFrame(self.scroll_frame)
        form_frame.pack(fill="x", pady=5)

        # Номер сертифіката
        ctk.CTkLabel(form_frame, text="Номер сертифіката:").grid(
            row=0, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_cert_number = ctk.CTkEntry(form_frame, width=350)
        self.entry_cert_number.grid(row=0, column=1, pady=8, padx=10)
        self.entry_cert_number.insert(0, str(self.party_data.get("cert_number", "UA.")))

        # Дата сертифіката
        ctk.CTkLabel(form_frame, text="Дата сертифіката:").grid(
            row=1, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_cert_date = ctk.CTkEntry(form_frame, width=350)
        self.entry_cert_date.grid(row=1, column=1, pady=8, padx=10)
        self.entry_cert_date.insert(
            0,
            str(self.party_data.get("cert_date", datetime.now().strftime("%d.%m.%Y"))),
        )

        # Номер протоколу випробувань
        ctk.CTkLabel(form_frame, text="Номер протоколу:").grid(
            row=2, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_protocol_number = ctk.CTkEntry(form_frame, width=350)
        self.entry_protocol_number.grid(row=2, column=1, pady=8, padx=10)
        self.entry_protocol_number.insert(
            0, str(self.party_data.get("protocol_number", ""))
        )

        # Дата протоколу
        ctk.CTkLabel(form_frame, text="Дата протоколу:").grid(
            row=3, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_protocol_date = ctk.CTkEntry(form_frame, width=350)
        self.entry_protocol_date.grid(row=3, column=1, pady=8, padx=10)
        self.entry_protocol_date.insert(
            0,
            str(
                self.party_data.get(
                    "protocol_date", datetime.now().strftime("%d.%m.%Y")
                )
            ),
        )

        # Додаємо контекстне меню
        for widget in [
            self.entry_cert_number,
            self.entry_cert_date,
            self.entry_protocol_number,
            self.entry_protocol_date,
        ]:
            add_context_menu(widget, self)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ Зберегти",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLORS["success"],
            command=self.on_save,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            command=self.on_closing,
        ).pack(side="left", padx=10)

    def on_closing(self):
        """Сохранение геометрии перед закрытием"""
        save_window_geometry(self, "FinalDocumentsPerPartyDialog")
        self.destroy()

    def on_save(self):
        """Перевірка даних та збереження"""
        cert_number = self.entry_cert_number.get().strip()
        cert_date = self.entry_cert_date.get().strip()
        protocol_number = self.entry_protocol_number.get().strip()
        protocol_date = self.entry_protocol_date.get().strip()

        # Валідація обов'язкових полів
        if not cert_number:
            messagebox.showerror("Помилка", "Введіть номер сертифіката!")
            return

        if not cert_date:
            messagebox.showerror("Помилка", "Введіть дату сертифіката!")
            return

        # Валідація формату дат
        for date_str, field_name in [
            (cert_date, "сертифіката"),
            (protocol_date, "протоколу"),
        ]:
            try:
                datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                messagebox.showerror(
                    "Помилка",
                    f"Некоректний формат дати {field_name}:\n{date_str}\nВикористовуйте: дд.мм.рррр",
                )
                return

        # Зберігаємо дані
        self.final_data = {
            "cert_number": cert_number,
            "cert_date": cert_date,
            "protocol_number": protocol_number,
            "protocol_date": protocol_date,
        }

        logger.info(f"✅ Фінальні дані партії #{self.party_index} збережені")
        self.on_closing()
