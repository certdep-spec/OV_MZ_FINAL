"""
Головний лаунчер CertifyPro (Мультиклієнтська версія).

Запускає вікно вибору клієнта → запускає CertifyPro з відповідним client_id.
Маппінг papka_proektu → client_id завантажується з profiles.yaml —
**жодного захардкодженого клієнта**.

Підтримує два режими запуску:
  1. З вихідного коду: шукає CERTIFYPRO/core/main.py і запускає через Python
  2. З .exe (PyInstaller): шукає CertifyPro.exe поруч із launcher.exe
"""

import io
import logging
import os
import subprocess
import sys
from pathlib import Path

# Примусово UTF-8 для консолі Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"

# --- Шляхи для імпорту ---
LAUNCHER_FILE = Path(__file__).resolve()
PROJECT_ROOT = LAUNCHER_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# === DEBUG LOGGER (для отладки передачи данных клиента) ===
try:
    from client_launcher.debug_logger import log_info as _log_info
    from client_launcher.debug_logger import log_stage as _log_stage

    _DEBUG_AVAILABLE = True
except ImportError:
    _DEBUG_AVAILABLE = False
    _log_stage = None
    _log_info = None

# --- Визначення кореневого шляху ---
from CERTIFYPRO.core.utils.path_provider import (
    get_launcher_root,
    get_profiles_path,
    get_project_root,
)

LAUNCHER_DIR = get_launcher_root()
ROOT_DIR = LAUNCHER_DIR  # Для лаунчера вони часто співпадають в .exe
IS_FROZEN = getattr(sys, "frozen", False)

# --- Налаштування логування ---
LOGS_DIR = LAUNCHER_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "launcher.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("Launcher")

# Шляхи до компонентів
CERTIFYPRO_EXE = LAUNCHER_DIR / "CertifyPro.exe"
# Коренева папка CertifyPro для запуску через Python
CERTIFYPRO_CORE = get_project_root()

PROFILES_PATH = get_profiles_path()


def _load_client_mapping() -> dict[str, str]:
    """
    Завантажити маппінг papka_proektu → client_id з profiles.yaml.

    Returns:
        {"АФІНА": "afina", "ДЖОНСОН": "johnson"}

    Якщо profiles.yaml недоступний — повертає порожній dict.
    """
    try:
        import yaml

        if not PROFILES_PATH.exists():
            logger.warning(f"profiles.yaml не знайдено: {PROFILES_PATH}")
            return {}

        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        mapping = {}
        for client_id, client_data in data.get("clients", {}).items():
            launcher_name = client_data.get("launcher_mapping", client_data.get("name"))
            mapping[launcher_name] = client_id

        logger.info(f"Завантажено маппінг: {mapping}")
        return mapping

    except Exception as e:
        logger.error(f"Помилка завантаження profiles.yaml: {e}")
        return {}


def launch_client(client_id: str) -> bool:
    """
    Запуск CertifyPro для конкретного клієнта.

    У режимі .exe: запускає CertifyPro.exe з аргументом client_id.
    У режимі Python: запускає main.py через sys.executable.

    Args:
        client_id: Ідентифікатор клієнта ("afina", "johnson")

    Returns:
        True якщо запуск успішний
    """
    if IS_FROZEN:
        # --- Режим .exe ---
        if not CERTIFYPRO_EXE.exists():
            logger.error(f"CertifyPro.exe не знайдено: {CERTIFYPRO_EXE}")
            from tkinter import messagebox

            messagebox.showerror(
                "Помилка",
                f"Не знайдено CertifyPro.exe поруч із launcher.exe.\nОчікується: {CERTIFYPRO_EXE}",
            )
            return False

        logger.info(f"🚀 Запуск CertifyPro.exe для клієнта: {client_id}")
        try:
            process = subprocess.Popen(
                [str(CERTIFYPRO_EXE), client_id],
                cwd=str(LAUNCHER_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                # creationflags убран для совместимости с Windows GUI
            )
            logger.info(f"✅ Процес запущено! PID: {process.pid}")
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                err_msg = (
                    stderr.decode("utf-8", errors="ignore") if stderr else "Невідомо"
                )
                logger.error(
                    f"CertifyPro упав (код {process.returncode}): {err_msg[:500]}"
                )
                return False
            logger.info("📋 CertifyPro завершено. Повертаємось до вибору...")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Помилка запуску: {e}")
            import traceback

            traceback.print_exc()
            return False
        except Exception as e:
            logger.error(f"Невідома помилка: {e}")
            import traceback

            traceback.print_exc()
            return False

    else:
        # --- Режим Python (вихідний код) ---
        main_py = CERTIFYPRO_CORE / "main.py"
        if not main_py.exists():
            logger.error(f"main.py не знайдено: {main_py}")
            return False

        logger.info(f"🚀 Запуск CertifyPro для клієнта: {client_id}")
        logger.info(f"📂 Робоча директорія: {CERTIFYPRO_CORE}")
        try:
            # Перенаправляємо вивід дочірнього процесу в лог-файл лаунчера
            # щоб консоль залишалась чистою (без мішанини двох процесів)
            child_log = LOG_FILE.parent / "certifypro_child.log"
            with open(child_log, "a", encoding="utf-8") as child_out:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",  # Примусово UTF-8
                        str(main_py),
                        client_id,
                    ],
                    cwd=str(CERTIFYPRO_CORE),
                    stdout=child_out,
                    stderr=child_out,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
            if result.returncode != 0:
                logger.error(
                    f"CertifyPro завершилось з помилкою (код {result.returncode}). "
                    f"Детальний лог: {child_log}"
                )
                return False
            logger.info("📋 CertifyPro завершено. Повертаємось до вибору...")
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Помилка запуску: {e}")
            return False


def main_loop():
    """Головний цикл: вибір клієнта → запуск → повернення"""
    from tkinter import messagebox

    import customtkinter as ctk
    from client_launcher.launcher_dialog import ClientSelectorDialog

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    try:
        while True:
            # Завантажуємо маппінг з profiles.yaml (перезавантаження на кожній ітерації)
            papka_to_client_id = _load_client_mapping()
            if not papka_to_client_id:
                logger.warning(
                    "⚠️ Не вдалося завантажити profiles.yaml, використовується fallback маппінг"
                )
                papka_to_client_id = {
                    "АФІНА": "afina",
                    "ДЖОНСОН": "johnson",
                }

            # Приховане головне вікно
            root = ctk.CTk()
            root.withdraw()

            # Діалог вибору
            dialog = ClientSelectorDialog(root)
            root.wait_window(dialog)

            selected = dialog.selected_applicant
            root.destroy()

            if selected is None:
                logger.info("❌ Користувач скасував вибір. Вихід.")
                break

            logger.info(f"✅ Обрано: {selected.nazva_pidpryyemstva}")
            logger.info(f"📁 Папка проекту: {selected.papka_proektu}")

            client_id = papka_to_client_id.get(selected.papka_proektu)
            if client_id is None:
                # Якщо клієнта немає в profiles.yaml, спробуємо використати papka_proektu як client_id
                # Це дозволить запускати динамічно доданих клієнтів
                logger.warning(
                    f"Клієнт '{selected.papka_proektu}' не знайдений у profiles.yaml. Спроба запуску як '{selected.papka_proektu}'..."
                )
                client_id = selected.papka_proektu
            else:
                logger.info(
                    f"📋 Знайдено client_id='{client_id}' для papka_proektu='{selected.papka_proektu}'"
                )

            mode_str = "[FROZEN]" if IS_FROZEN else "[SOURCE]"
            logger.info(f"🚀 {mode_str} Запуск CertifyPro з client_id='{client_id}'")

            if not launch_client(client_id):
                logger.error(f"⚠️ Помилка запуску клієнта {client_id}")

    except Exception as e:
        import traceback

        error_msg = f"Критична помилка лаунчера:\n\n{e}\n\n{traceback.format_exc()}"
        logger.critical(error_msg)

        try:
            # Показуємо вікно помилки
            err_root = ctk.CTk()
            err_root.withdraw()
            messagebox.showerror("CertifyPro Launcher: Помилка", error_msg)
            err_root.destroy()
        except Exception:
            logger.error(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main_loop()
