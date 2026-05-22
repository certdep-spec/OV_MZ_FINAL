"""
Менеджер геометрії вікон.

Єдине місце для збереження та відновлення позицій/розмірів вікон.
Замінює дублювання функцій save/restore_window_geometry у кожному діалозі.

Використання:
    from client_launcher.geometry_manager import save_window_geometry, restore_window_geometry

    # При відкритті:
    restore_window_geometry(self, "MyDialog", 500, 400)

    # При закритті:
    save_window_geometry(self, "MyDialog")
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Файл геометрії зберігається поруч з launcher.exe (у frozen режимі) або в client_launcher/ (у режимі розробки)
if getattr(sys, "frozen", False):
    _GEOM_FILE = Path(sys.executable).parent / "window_geometry.json"
else:
    _GEOM_FILE = Path(__file__).parent / "window_geometry.json"


def _load_geom() -> dict:
    """Завантажити словник геометрії з файлу."""
    if _GEOM_FILE.exists():
        try:
            with open(_GEOM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Не вдалося прочитати window_geometry.json: {e}")
    return {}


def _save_geom(data: dict) -> None:
    """Зберегти словник геометрії у файл."""
    try:
        with open(_GEOM_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.warning(f"Не вдалося записати window_geometry.json: {e}")


def restore_window_geometry(window, name: str, default_w: int, default_h: int) -> None:
    """
    Відновити збережену геометрію вікна.

    Args:
        window: Вікно (CTk/CTkToplevel)
        name: Унікальне ім'я вікна
        default_w: Ширина за замовчуванням
        default_h: Висота за замовчуванням
    """
    try:
        data = _load_geom()
        g = data.get(name, {})
        if g and all(k in g for k in ("w", "h", "x", "y")):
            window.geometry(f"{g['w']}x{g['h']}+{g['x']}+{g['y']}")
            logger.debug(
                f"📐 Відновлено геометрію {name}: {g['w']}x{g['h']}+{g['x']}+{g['y']}"
            )
            return
    except Exception as e:
        logger.debug(f"Не вдалося відновити геометрію для {name}: {e}")

    window.geometry(f"{default_w}x{default_h}")


def save_window_geometry(window, name: str) -> None:
    """
    Зберегти поточну геометрію вікна.

    Парсимо .geometry() рядок замість winfo_width/height бо для CTkToplevel
    вони можуть повертати неправильні значення.

    Args:
        window: Вікно (CTk/CTkToplevel)
        name: Унікальне ім'я вікна
    """
    try:
        data = _load_geom()

        # Отримуємо геометрію у форматі "widthxheight+x+y"
        geom_str = window.geometry()
        # Парсимо: "450x400+100+200" → w=450, h=400, x=100, y=200
        import re

        match = re.match(r"(\d+)x(\d+)\+([-\d]+)\+([-\d]+)", geom_str)
        if match:
            w, h, x, y = (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4)),
            )
            data[name] = {"w": w, "h": h, "x": x, "y": y}
            logger.debug(f"💾 Збережено геометрію {name}: {w}x{h}+{x}+{y}")
        else:
            # Fallback на winfo
            data[name] = {
                "x": window.winfo_x(),
                "y": window.winfo_y(),
                "w": window.winfo_width(),
                "h": window.winfo_height(),
            }
            logger.debug(f"💾 Збережено геометрію {name} (fallback)")

        _save_geom(data)
    except Exception as e:
        logger.debug(f"Не вдалося зберегти геометрію для {name}: {e}")
