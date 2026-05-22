"""
Централізоване управління шляхами проекту.
Підтримує як режим розробки, так і режим зібраного .exe (PyInstaller).
"""

import sys
from pathlib import Path


def get_project_root() -> Path:
    """Визначення кореневої директорії проекту (CERTIFYPRO/core)"""
    if getattr(sys, "frozen", False):
        # Якщо запущено як .exe
        return Path(sys._MEIPASS)
    else:
        # Якщо запущено з вихідного коду (core/utils/path_provider.py -> core)
        return Path(__file__).parent.parent


def get_launcher_root() -> Path:
    """Визначення кореневої директорії лаунчера (батьківська папка відносно .exe)"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        # E:\2\FINAL\CERTIFYPRO\core\utils\path_provider.py -> E:\2\FINAL
        return Path(__file__).parent.parent.parent.parent


def get_data_dir(client_data_dir: str) -> Path:
    """Отримання шляху до папки даних конкретного клієнта"""
    return get_launcher_root() / client_data_dir


def get_templates_dir() -> Path:
    """Отримання шляху до шаблонів"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "resources" / "templates"
    else:
        return get_launcher_root() / "CERTIFYPRO" / "resources" / "templates"


def get_profiles_path() -> Path:
    """Шлях до profiles.yaml"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "resources" / "profiles.yaml"
    else:
        return get_launcher_root() / "CERTIFYPRO" / "resources" / "profiles.yaml"
