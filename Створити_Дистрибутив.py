import os
import shutil
import subprocess
import sys
import stat
from pathlib import Path

def remove_readonly(func, path, excinfo):
    """Обробник помилок для rmtree: знімає атрибут 'read-only' та пробує знову."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_rmtree(path):
    """Видалення дерева каталогів з обробкою read-only файлів (сумісність Python 3.10+)."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=remove_readonly)
    else:
        shutil.rmtree(path, onerror=remove_readonly)

def run_command(cmd_list):
    print(f"Виконується: {' '.join(cmd_list)}")
    try:
        subprocess.run(cmd_list, check=True)
    except Exception as e:
        print(f"Помилка при виконанні команди: {e}")
        return False
    return True

def find_stable_python():
    """Використовуємо Python 3.10 — стабільна версія для PyInstaller."""
    programs_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python"
    candidate = programs_dir / "Python310" / "python.exe"
    
    if candidate.exists():
        print(f"[OK] Використовуємо Python 3.10: {candidate}")
        return candidate

    # Резервний пошук через Launcher
    for py_cmd in ["py -3.10", "python3.10"]:
        try:
            parts = py_cmd.split()
            res = subprocess.run(parts + ["-c", "import sys; print(sys.executable)"], capture_output=True, text=True)
            if res.returncode == 0:
                candidate_path = Path(res.stdout.strip())
                if candidate_path.exists():
                    print(f"[OK] Знайдено Python 3.10 через PATH: {candidate_path}")
                    return candidate_path
        except Exception:
            continue
            
    # Останній резерв — поточний інтерпретатор
    current_exe = Path(sys.executable)
    major, minor = sys.version_info[:2]
    print(f"[WARN] Python 3.10 не знайдено. Використовуємо поточний Python {major}.{minor}: {current_exe}")
    return current_exe

def create_distributive():
    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "Дистрибутив"
    dist_data_dir = dist_dir / "data"
    
    print("=== ПІДГОТОВКА ДИСТРИБУТИВА ===")
    
    # 1. Очищуємо стару папку (з обробкою read-only файлів та зайнятих файлів)
    if dist_dir.exists():
        print(" -> Очищення старої папки Дистрибутив...")
        while True:
            try:
                safe_rmtree(dist_dir)
                break
            except Exception as e:
                print(f"\n[ERROR] ПОМИЛКА ОЧИЩЕННЯ: {e}")
                print("Можливо, деякі файли дистрибутива відкриті в іншій програмі (наприклад, у Microsoft Word).")
                print("-> БУДЬ ЛАСКА, ЗАКРИЙТЕ Microsoft Word та всі відкриті файли документів!")
                ans = input("Натисніть Enter, щоб спробувати знову, або введіть 'q' для скасування: ").strip().lower()
                if ans == 'q':
                    print("Збірка скасована користувачем.")
                    return
    dist_dir.mkdir(exist_ok=True)
    dist_data_dir.mkdir(exist_ok=True)
    
    # 2. Компіляція
    print("\n1. Компіляція проекту (це може зайняти час)...")
    
    python_exe = find_stable_python()
    
    # Якщо переключилися на альтернативний Python, встановлюємо туди всі залежності проекту
    if python_exe != Path(sys.executable):
        print(f"\n[INFO] Встановлюємо необхідні бібліотеки для обраного інтерпретатора {python_exe}...")
        deps = [
            "customtkinter>=5.2.0",
            "python-docx>=1.1.0",
            "docxtpl>=0.16.0",
            "openpyxl>=3.1.5",
            "pandas>=2.0.0",
            "Pillow>=11.0.0",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0",
            "pyinstaller==6.11.0",
            "pyinstaller-hooks-contrib>=2024.6,<2025"
        ]
        run_command([str(python_exe), "-m", "pip", "install"] + deps)
        
    if os.path.exists("recompile_and_copy.py"):
        success = run_command([str(python_exe), "recompile_and_copy.py"])
        if not success:
            print("\n[ERROR] КРИТИЧНА ПОМИЛКА: Не вдалося скомпілювати проект!")
            print("Збірка зупинена. Дистрибутив НЕ створено.")
            return
    
    # 3. Копіюємо результати з CertifyPro_v3.1
    source_dir = root_dir / "CertifyPro_v3.1"
    if source_dir.exists():
        print(f"\n2. Копіювання програм з {source_dir.name}...")
        ignore_func = shutil.ignore_patterns('.git', '.vscode', '__pycache__', '.pytest_cache', '*.pyc', '.aider*')
        
        for item in source_dir.iterdir():
            dest_item = dist_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True, ignore=ignore_func)
            else:
                shutil.copy2(item, dest_item)
    else:
        print("! Папка CertifyPro_v3.1 не знайдена. Перевірте, чи пройшла збірка.")

    # 4. Копіюємо базу лаунчера
    launcher_db_src = root_dir / "src" / "client_launcher" / "data" / "applicants.db"
    if not launcher_db_src.exists():
        launcher_db_src = root_dir / "client_launcher" / "data" / "applicants.db"
        
    if launcher_db_src.exists():
        print(f"\n3. Копіювання бази лаунчера...")
        shutil.copy2(launcher_db_src, dist_data_dir / "applicants.db")

    # 5. Копіюємо дані клієнтів (Розумний пошук баз та шаблонів)
    print("\n4. Збір даних клієнтів у папку data/...")
    clients = ["АФІНА", "ДЖОНСОН", "PROCTER"]
    
    for client in clients:
        # Шукаємо де лежить клієнт (в корені або в data/)
        client_src = root_dir / client
        if not client_src.exists():
            client_src = root_dir / "data" / client
            
        if client_src.exists():
            print(f" -> Опрацювання клієнта: {client}...")
            dest_client_dir = dist_data_dir / client
            dest_client_dir.mkdir(exist_ok=True)
            
            # А) Шукаємо БАЗУ (certify.db) серед усіх можливих місць та обираємо НАЙНОВІШУ за часом модифікації
            db_candidates = [
                root_dir / "CertifyPro_v3.1" / "data" / client / "certify.db", # Робоча база з релізу
                client_src / "data" / "certify.db",
                client_src / "certify.db"
            ]
            
            existing_dbs = []
            for db_path in db_candidates:
                if db_path.exists():
                    existing_dbs.append(db_path)
            
            db_found = False
            if existing_dbs:
                # Вибираємо базу з найновішим часом модифікації
                newest_db = max(existing_dbs, key=lambda p: p.stat().st_mtime)
                import datetime
                mod_time = datetime.datetime.fromtimestamp(newest_db.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"    [OK] Знайдено та вибрано НАЙНОВІШУ базу: {newest_db.relative_to(root_dir)} ({newest_db.stat().st_size} байт, змінено: {mod_time})")
                shutil.copy2(newest_db, dest_client_dir / "certify.db")
                db_found = True
            
            if not db_found:
                print(f"    [ERROR] Базу даних для {client} не знайдено!")

            # Б) Копіюємо ШАБЛОНИ (якщо є)
            templates_src = client_src / "templates"
            if templates_src.exists():
                print(f"    [OK] Копіювання шаблонів з {templates_src.relative_to(root_dir)}")
                shutil.copytree(templates_src, dest_client_dir / "templates", dirs_exist_ok=True)
            else:
                print(f"    [WARN] Папку templates для {client} не знайдено.")

            # В) Копіюємо ДОКУМЕНТИ (Documents) якщо є
            docs_src = client_src / "data" / "Documents" if (client_src / "data" / "Documents").exists() else client_src / "Documents"
            if docs_src.exists():
                shutil.copytree(docs_src, dest_client_dir / "Documents", dirs_exist_ok=True)
        else:
            print(f" -> ! Клієнта {client} взагалі не знайдено на диску.")

    print("\n" + "="*40)
    print("[OK] ДИСТРИБУТИВ ГОТОВИЙ!")
    print(f"Шлях: {dist_dir}")
    print("="*40)
    print("\nТепер усі бази та шаблони зібрані в правильну структуру 'data/КЛІЄНТ/'.")

    # 6. Очистка тимчасових папок
    print("\n5. Очищення тимчасових папок...")
    for folder in ["build", "dist"]:
        folder_path = root_dir / folder
        if folder_path.exists():
            try:
                safe_rmtree(folder_path)
                print(f" -> Видалено {folder}/")
            except Exception as e:
                print(f" ! Не вдалося видалити {folder}/: {e}")

    # 7. Видалення непотрібних пакетів з _internal дистрибутива
    print("\n6. Очищення _internal від непотрібних пакетів...")
    internal_dir = dist_dir / "_internal"
    unused_items = [
        "scipy", "scipy.libs",
        "numba",
        "llvmlite", "llvmlite.libs",
        "matplotlib",
        "kiwisolver",
        "contourpy",
        "setuptools-65.5.0.dist-info",
        "markupsafe-3.0.3.dist-info",
        "tqdm-4.67.3.dist-info",
    ]
    # Видалення pandas/tests та pandas/_testing
    for pandas_subdir in ["tests", "_testing"]:
        pandas_sub = internal_dir / "pandas" / pandas_subdir
        if pandas_sub.exists():
            try:
                safe_rmtree(pandas_sub)
                print(f" -> Видалено pandas/{pandas_subdir}/")
            except Exception as e:
                print(f" ! Не вдалося видалити pandas/{pandas_subdir}/: {e}")
    
    for item_name in unused_items:
        item_path = internal_dir / item_name
        if item_path.exists():
            try:
                if item_path.is_dir():
                    safe_rmtree(item_path)
                else:
                    os.remove(item_path)
                print(f" -> Видалено {item_name}/")
            except Exception as e:
                print(f" ! Не вдалося видалити {item_name}/: {e}")

    # Видалення runtime hook для matplotlib
    mpl_hook = internal_dir / "pyi_rth_mplconfig"
    if mpl_hook.exists():
        try:
            os.remove(mpl_hook)
            print(f" -> Видалено pyi_rth_mplconfig")
        except Exception as e:
            print(f" ! Не вдалося видалити pyi_rth_mplconfig: {e}")

    # 8. Видалення __pycache__ з дистрибутива
    print("\n7. Видалення __pycache__...")
    for pycache in dist_dir.rglob("__pycache__"):
        try:
            safe_rmtree(pycache)
        except Exception:
            pass

if __name__ == "__main__":
    try:
        create_distributive()
    except Exception as e:
        print(f"\n[ERROR] КРИТИЧНА ПОМИЛКА: {e}")
    
    input("\nНатисніть Enter, щоб закрити вікно...")
