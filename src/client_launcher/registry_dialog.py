"""
Діалог реєстру заявок.

Загальний реєстр для всіх заявників з можливістю сортування та експорту в Excel.
"""

import logging
import queue
import sys
import threading
from pathlib import Path
from tkinter import messagebox, ttk
from typing import List

import customtkinter as ctk
from client_launcher.geometry_manager import (
    restore_window_geometry,
    save_window_geometry,
)
from client_launcher.registry_service import RegistryEntry, RegistryService

logger = logging.getLogger("registry_dialog")


# Визначення кореневої директорії (аналогічно launcher.py)
if getattr(sys, "frozen", False):
    # Режим .exe: папка де лежить launcher.exe
    _ROOT_DIR = Path(sys.executable).parent
else:
    # Режим вихідного коду: parent від client_launcher/
    _ROOT_DIR = Path(__file__).parent.parent


def _find_certifypro_data_dirs(root_dir: Path) -> list:
    """
    Знайти всі директорії з даними CertifyPro (data/).

    Шукає:
    1. {root_dir}/data/ (якщо БД лежать поруч з launcher.exe)
    2. {root_dir}/CertifyPro*/data/ (якщо є кілька версій)
    3. {root_dir}/*/data/ (загальний пошук)

    Returns:
        Список шляхів до директорій, що містять data/
    """
    candidates = []

    # 1. Сама root_dir/data/
    if (root_dir / "data").exists():
        candidates.append(root_dir)

    # 2. Піддиректорії виду CertifyPro*/data/
    for pattern in ["CertifyPro*", "certifypro*"]:
        for d in root_dir.glob(pattern):
            if d.is_dir() and (d / "data").exists():
                candidates.append(d)

    # 3. Будь-яка піддиректорія з data/
    try:
        for d in root_dir.iterdir():
            if d.is_dir() and d.name.lower() not in ("dist", "build", ".git", ".venv", "env", "__pycache__"):
                if (d / "data").exists() and d not in candidates:
                    candidates.append(d)
    except PermissionError:
        pass

    return candidates


class RegistryDialog(ctk.CTkToplevel):
    """Діалог реєстру заявок"""

    def __init__(self, parent=None, date_from: str = None, date_to: str = None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)

        self.title("📋 Реєстр заявок")
        self.geometry("1400x650")

        if parent:
            self.transient(parent)
            self.grab_set()

        self.date_from = date_from
        self.date_to = date_to

        # Відновлення геометрії
        self.after(
            100, lambda: restore_window_geometry(self, "RegistryDialog", 1400, 650)
        )
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Root директорія (визначається з урахуванням режиму .exe)
        self.root_dir = _ROOT_DIR

        # Знаходимо всі директорії з CertifyPro даними
        self.data_dirs = _find_certifypro_data_dirs(self.root_dir)

        # Передаємо всі директорії в сервіс
        self.registry_service = RegistryService(self.root_dir, data_dirs=self.data_dirs)
        self.entries: List[RegistryEntry] = []
        self.is_loading = False

        self._create_widgets()

        # Черга для міжпотокової взаємодії
        self.queue = queue.Queue()
        self._check_queue()

        self._load_data()

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

    def _create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            title_frame,
            text="📋 Загальний реєстр заявок",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=10, pady=5)

        # Кількість записів
        self.lbl_count = ctk.CTkLabel(
            title_frame,
            text="Записів: 0",
            font=ctk.CTkFont(size=14),
        )
        self.lbl_count.pack(side="right", padx=10, pady=5)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.btn_refresh = ctk.CTkButton(
            btn_frame,
            text="🔄 Оновити",
            height=30,
            width=120,
            fg_color="#2B7CB9",
            hover_color="#1A5F8A",
            command=self._load_data,
        )
        self.btn_refresh.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="📥 Експорт в Excel",
            height=30,
            width=140,
            fg_color="#2E8B57",
            hover_color="#236B43",
            command=self._export_to_excel,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="❌ Закрити",
            height=30,
            width=100,
            fg_color="gray",
            hover_color="#555",
            command=self.destroy,
        ).pack(side="right", padx=5)

        # Таблиця
        columns = (
            "row_num",
            "app_number",
            "app_date",
            "applicant_name",
            "applicant_edrpou",
            "product_name",
            "manufacturer_name",
            "protocol_number",
            "protocol_date",
            "cert_info",
            "ugoda_number",
        )

        headers = {
            "row_num": "№",
            "app_number": "Номер заявки",
            "app_date": "Дата заявки",
            "applicant_name": "Заявник",
            "applicant_edrpou": "ЄДРПОУ",
            "product_name": "Продукція",
            "manufacturer_name": "Виробник",
            "protocol_number": "Протокол №",
            "protocol_date": "Дата протоколу",
            "cert_info": "Сертифікат",
            "ugoda_number": "Номер угоди",
        }

        widths = {
            "row_num": 40,
            "app_number": 130,
            "app_date": 90,
            "applicant_name": 160,
            "applicant_edrpou": 90,
            "product_name": 250,
            "manufacturer_name": 200,
            "protocol_number": 90,
            "protocol_date": 100,
            "cert_info": 220,
            "ugoda_number": 200,
        }

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=20,
        )

        for col in columns:
            self.tree.heading(
                col, text=headers[col], command=lambda c=col: self._sort_by_column(c)
            )
            self.tree.column(
                col,
                width=widths[col],
                anchor=(
                    "center"
                    if col in ("row_num", "protocol_number", "protocol_date")
                    else "w"
                ),
            )

        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y")

    def _load_data(self):
        """Завантаження даних реєстру у фоновому режимі"""
        if self.is_loading:
            return

        self.is_loading = True
        self.btn_refresh.configure(state="disabled", text="⏳ Завантаження...")
        self.lbl_count.configure(text="⏳ Збір даних з усіх баз клієнтів... Зачекайте.")

        # Очищення таблиці
        for item in self.tree.get_children():
            self.tree.delete(item)

        def _bg_task():
            try:
                # Збір всіх записів (тривала операція)
                all_entries = self.registry_service.collect_all_entries()

                # Фільтрація за періодом
                filtered_entries = self._filter_entries_by_date(all_entries)

                # Повертаємось в основний потік для оновлення UI через чергу
                self.queue.put(lambda: self._on_data_loaded(filtered_entries))
            except Exception as e:
                logger.error(f"Помилка фонового завантаження реєстру: {e}")
                self.queue.put(lambda: self._on_load_error(str(e)))

        thread = threading.Thread(target=_bg_task, daemon=True)
        thread.start()

    def _on_data_loaded(self, entries: List[RegistryEntry]):
        """Оновлення UI після завершення фонового завантаження"""
        self.entries = entries
        self.is_loading = False

        # Пронумеруємо відфільтровані записи
        for i, entry in enumerate(self.entries, 1):
            entry.row_number = i

        for entry in self.entries:
            self.tree.insert(
                "",
                "end",
                values=(
                    entry.row_number,
                    entry.app_number_formatted,
                    entry.app_date,
                    entry.applicant_name,
                    entry.applicant_edrpou,
                    entry.product_name,
                    entry.manufacturer_address, # Використовуємо повну адресу замість тільки назви
                    entry.protocol_number,
                    entry.protocol_date,
                    entry.cert_info,
                    entry.ugoda_number,
                ),
            )

        # Оновлення кнопок та міток
        self.btn_refresh.configure(state="normal", text="🔄 Оновити")

        period_text = f"Період: {self.date_from}"
        if self.date_to:
            period_text += f" — {self.date_to}"

        self.lbl_count.configure(text=f"Записів: {len(self.entries)} | {period_text}")

    def _on_load_error(self, error_msg: str):
        """Обробка помилки завантаження"""
        self.is_loading = False
        self.btn_refresh.configure(state="normal", text="🔄 Оновити")
        self.lbl_count.configure(text="❌ Помилка завантаження")
        messagebox.showerror(
            "Помилка реєстру", f"Не вдалося зібрати дані реєстру:\n{error_msg}"
        )

    def _filter_entries_by_date(
        self, entries: List[RegistryEntry]
    ) -> List[RegistryEntry]:
        """Фільтрація записів за періодом дати протоколу"""
        if not self.date_from:
            return entries

        from datetime import datetime

        try:
            dt_from = datetime.strptime(self.date_from, "%d.%m.%Y")
        except ValueError:
            return entries

        # Якщо дата до не вказана — використовуємо поточну дату
        if self.date_to:
            try:
                dt_to = datetime.strptime(self.date_to, "%d.%m.%Y")
            except ValueError:
                dt_to = datetime.now()
        else:
            dt_to = datetime.now()

        filtered = []
        for entry in entries:
            if not entry.protocol_date:
                continue

            try:
                dt_protocol = datetime.strptime(entry.protocol_date, "%d.%m.%Y")
                if dt_from <= dt_protocol <= dt_to:
                    filtered.append(entry)
            except ValueError:
                # Невірний формат дати — пропускаємо
                continue

        return filtered

    def _sort_by_column(self, column: str):
        """Сортування по колонці"""
        # Отримуємо всі елементи
        items = [
            (self.tree.set(item, column), item) for item in self.tree.get_children("")
        ]

        # Визначаємо чи сортувати як числа
        try:
            items.sort(key=lambda x: int(x[0]))
        except ValueError:
            items.sort(key=lambda x: x[0].lower())

        # Перебудовуємо таблицю
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)
            # Оновлюємо номер рядка
            if column != "row_num":
                self.tree.set(item, "row_num", str(index + 1))

        # Оновлюємо row_number у entries
        for i, (_, _) in enumerate(items):
            if i < len(self.entries):
                self.entries[i].row_number = i + 1

    def _export_to_excel(self):
        """Експорт реєстру в Excel"""
        try:
            import openpyxl
            from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        except ImportError:
            messagebox.showerror(
                "Помилка",
                "Бібліотека openpyxl не встановлена.\nВиконайте: pip install openpyxl",
            )
            return

        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            title="Зберегти реєстр",
            defaultextension=".xlsx",
            filetypes=[("Excel файли", "*.xlsx")],
            initialfile=f"Реєстр_заявок_{Path(__file__).parent.parent.name}.xlsx",
        )

        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Реєстр заявок"

            # Заголовки
            headers = [
                "№ п/п",
                "Номер заявки",
                "Дата заявки",
                "Заявник",
                "Адреса заявника",
                "ЄДРПОУ",
                "Продукція",
                "Виробник",
                "Протокол №",
                "Дата протоколу",
                "Сертифікат",
                "Номер угоди",
            ]

            # Стилі
            Font(bold=True, size=11)
            header_fill = PatternFill(
                start_color="2B7CB9", end_color="2B7CB9", fill_type="solid"
            )
            header_font_white = Font(bold=True, size=11, color="FFFFFF")
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )

            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.font = header_font_white
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", wrap_text=True)
                cell.border = thin_border

            # Дані
            for entry in self.entries:
                row_data = [
                    entry.row_number,
                    entry.app_number_formatted,
                    entry.app_date,
                    entry.applicant_name,
                    entry.applicant_address,
                    entry.applicant_edrpou,
                    entry.product_name,
                    entry.manufacturer_address,
                    entry.protocol_number,
                    entry.protocol_date,
                    entry.cert_info,
                    entry.ugoda_number,
                ]

                for col_idx, value in enumerate(row_data, 1):
                    cell = ws.cell(
                        row=entry.row_number + 1, column=col_idx, value=value
                    )
                    cell.border = thin_border
                    cell.alignment = Alignment(wrap_text=True, vertical="top")

                    # Автоширина для номерів
                    if col_idx == 1:
                        cell.alignment = Alignment(horizontal="center")

            # Ширина колонок
            column_widths = [6, 18, 25, 40, 12, 40, 30, 40, 12, 14, 28]
            for col_idx, width in enumerate(column_widths, 1):
                ws.column_dimensions[
                    openpyxl.utils.get_column_letter(col_idx)
                ].width = width

            # Збереження
            wb.save(file_path)
            messagebox.showinfo("Успіх", f"✅ Реєстр експортовано в:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Помилка", f"❌ Помилка експорту:\n{e}")

    def _on_close(self):
        """Збереження геометрії перед закриттям"""
        save_window_geometry(self, "RegistryDialog")
        self.destroy()
