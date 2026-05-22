"""
Допоміжні утиліти для GUI
"""

import json
import logging
from pathlib import Path
from tkinter import Menu

logger = logging.getLogger(__name__)


def add_context_menu(widget, master):
    """
    Додає контекстне меню (Вирізати, Копіювати, Вставити, Виділити все) до віджета.
    Працює з CTkEntry та CTkComboBox.
    """
    # Знаходимо реальний tkinter віджет всередині CTkEntry/CTkComboBox
    real_widget = widget._entry if hasattr(widget, "_entry") else widget

    menu = Menu(master, tearoff=0)

    # Визначаємо команди через віртуальні івенти реального віджета
    menu.add_command(
        label="Вирізати", command=lambda: real_widget.event_generate("<<Cut>>")
    )
    menu.add_command(
        label="Копіювати",
        command=lambda: real_widget.event_generate("<<Copy>>"),
    )
    menu.add_command(
        label="Вставити",
        command=lambda: real_widget.event_generate("<<Paste>>"),
    )

    def show_menu(event):
        real_widget.focus_set()  # Обов'язково ставимо фокус
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    # Прив'язуємо до правої кнопки миші реального віджета
    real_widget.bind("<Button-3>", show_menu)


def _select_all(widget):
    """Виділяє весь текст у полі та встановлює фокус"""
    if hasattr(widget, "select_range"):
        widget.select_range(0, "end")
    widget.focus_set()


# ===== СОХРАНЕНИЕ ГЕОМЕТРИИ ОКНА =====


def save_window_geometry(window, window_name: str):
    """
    Зберігає геометрію вікна у файл JSON.
    Використовує window.geometry() для стабільності.
    """
    try:
        window.update_idletasks()

        # Не зберігаємо, якщо вікно згорнуте
        if window.state() == "iconic":
            return

        geometry = window.geometry()  # Формат WxH+X+Y

        # Перевірка мінімальних розмірів (щоб не зберігати "схлопнуті" вікна)
        parts = geometry.replace("x", "+").split("+")
        if len(parts) >= 2:
            width = int(parts[0])
            height = int(parts[1])
            if width < 200 or height < 200:
                return

        config_path = Path("config") / "window_geometry.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {}

        data[window_name] = geometry

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Помилка при збереженні геометрії {window_name}: {e}")


def restore_window_geometry(
    window,
    window_name: str,
    default_width: int = 800,
    default_height: int = 600,
):
    """
    Відновлює геометрію вікна з файлу JSON.
    """
    try:
        config_path = Path("config") / "window_geometry.json"

        if not config_path.exists():
            window.geometry(f"{default_width}x{default_height}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if window_name in data:
            geometry = data[window_name]
            window.geometry(geometry)
        else:
            window.geometry(f"{default_width}x{default_height}")

    except Exception as e:
        logger.error(f"Помилка при відновленні геометрії {window_name}: {e}")
        window.geometry(f"{default_width}x{default_height}")
