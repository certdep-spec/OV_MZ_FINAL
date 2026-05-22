"""
Діалог вибору періоду для реєстру заявок.
"""

import json
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

_GEOM_FILE = Path(__file__).parent / "window_geometry.json"


def _restore_window_geometry(window, name, default_w, default_h):
    try:
        if _GEOM_FILE.exists():
            with open(_GEOM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            g = data.get(name, {})
            if g:
                window.geometry(f"{g['w']}x{g['h']}+{g['x']}+{g['y']}")
                return
    except Exception:
        pass
    window.geometry(f"{default_w}x{default_h}")


def _save_window_geometry(window, name):
    try:
        data = {}
        if _GEOM_FILE.exists():
            with open(_GEOM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[name] = {
            "x": window.winfo_x(),
            "y": window.winfo_y(),
            "w": window.winfo_width(),
            "h": window.winfo_height(),
        }
        with open(_GEOM_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class DateRangeDialog(ctk.CTkToplevel):
    """Діалог вибору періоду дат"""

    def __init__(self, parent=None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)

        self.title("📅 Період реєстру")
        self.geometry("380x280")
        self.resizable(False, False)

        if parent:
            self.transient(parent)
            self.grab_set()

        self.date_from: Optional[str] = None
        self.date_to: Optional[str] = None

        self._create_widgets()

        # Відновлення геометрії
        self.after(
            100, lambda: _restore_window_geometry(self, "DateRangeDialog", 380, 280)
        )
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Створення віджетів"""
        # Заголовок
        ctk.CTkLabel(
            self,
            text="📅 Період реєстру заявок",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=15)

        # Поля дат
        date_frame = ctk.CTkFrame(self)
        date_frame.pack(fill="x", padx=20, pady=10)

        # Дата від
        ctk.CTkLabel(date_frame, text="Дата від:").grid(
            row=0, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_date_from = ctk.CTkEntry(date_frame, width=200)
        self.entry_date_from.grid(row=0, column=1, pady=8, padx=10)

        # Підказка
        ctk.CTkLabel(
            date_frame,
            text="(дд.мм.рррр)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        ).grid(row=0, column=2, pady=8, padx=5)

        # Дата до
        ctk.CTkLabel(date_frame, text="Дата до:").grid(
            row=1, column=0, sticky="w", pady=8, padx=10
        )
        self.entry_date_to = ctk.CTkEntry(date_frame, width=200)
        self.entry_date_to.grid(row=1, column=1, pady=8, padx=10)

        ctk.CTkLabel(
            date_frame,
            text="(не вказано → сьогодні)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        ).grid(row=1, column=2, pady=8, padx=5)

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ Показати реєстр",
            height=35,
            width=140,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self._on_ok,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="❌ Скасувати",
            height=35,
            width=120,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="#555",
            command=self._on_cancel,
        ).pack(side="left", padx=10)

    def _on_ok(self):
        """Обробка підтвердження"""
        date_from_str = self.entry_date_from.get().strip()
        date_to_str = self.entry_date_to.get().strip()

        if not date_from_str:
            messagebox.showerror("Помилка", "Вкажіть дату початку періоду!")
            return

        # Валідація дати від
        try:
            datetime.strptime(date_from_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror(
                "Помилка",
                f"Некоректний формат дати від:\n{date_from_str}\nВикористовуйте: дд.мм.рррр",
            )
            return

        # Валідація дати до
        if date_to_str:
            try:
                datetime.strptime(date_to_str, "%d.%m.%Y")
            except ValueError:
                messagebox.showerror(
                    "Помилка",
                    f"Некоректний формат дати до:\n{date_to_str}\nВикористовуйте: дд.мм.рррр",
                )
                return

            # Перевірка послідовності
            dt_from = datetime.strptime(date_from_str, "%d.%m.%Y")
            dt_to = datetime.strptime(date_to_str, "%d.%m.%Y")
            if dt_to < dt_from:
                messagebox.showerror(
                    "Помилка",
                    "Дата завершення не може бути раніше дати початку!",
                )
                return
        else:
            # Якщо не вказано — поточна дата
            date_to_str = datetime.now().strftime("%d.%m.%Y")

        self.date_from = date_from_str
        self.date_to = date_to_str
        self._on_close()

    def _on_cancel(self):
        """Скасування"""
        self.date_from = None
        self.date_to = None
        self._on_close()

    def _on_close(self):
        """Збереження геометрії перед закриттям"""
        _save_window_geometry(self, "DateRangeDialog")
        self.destroy()
