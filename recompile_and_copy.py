import os
import sys
import shutil
import subprocess
import stat
from pathlib import Path

def remove_readonly(func, path, excinfo):
    """Handler for rmtree: removes read-only attribute and retries."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_rmtree(path):
    """Remove directory tree with read-only file handling (Python 3.10+ compat)."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=remove_readonly)
    else:
        shutil.rmtree(path, onerror=remove_readonly)

def run_command(cmd_list):
    print(f"Executing: {' '.join(cmd_list)}")
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    if "PyInstaller" in cmd_list:
        cmd_list.append("--log-level=ERROR")
    try:
        result = subprocess.run(cmd_list, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed with return code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"\n[ERROR] Command '{cmd_list[0]}' not found. Is it installed and in PATH?")
        sys.exit(1)

if __name__ == "__main__":
    print("=== 0. PRE-FLIGHT CHECKS ===")
    print(f"Using Python: {sys.executable}")

    print("\n=== AUTO-UPGRADING PYINSTALLER (pinned to 6.11.0 — 6.20+ has encodings hook bug on Python 3.10) ===")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller==6.11.0", "pyinstaller-hooks-contrib>=2024.6,<2025"],
            check=True
        )
        print("[OK] PyInstaller pinned to 6.11.0!")
    except Exception as e:
        print(f"[WARNING] Could not install PyInstaller: {e}")

    print("\n=== 1. CLEANING OLD BUILD FOLDERS ===")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                safe_rmtree(folder)
            except Exception as e:
                print(f"[WARNING] Could not remove {folder}: {e}")

    print("\n=== 2. COMPILING MAIN APP (CertifyPro.exe) ===")
    run_command([sys.executable, "-m", "PyInstaller", "--noconfirm", "build_certifypro.spec"])

    print("\n=== 3. COMPILING LAUNCHER (launcher.exe) ===")
    run_command([sys.executable, "-m", "PyInstaller", "--noconfirm", "build_launcher.spec"])

    print("\n=== 4. COPYING TO CertifyPro_v3.1 ===")
    
    # Determine the project root dynamically (where this script is located)
    root_dir = Path(__file__).resolve().parent
    target_dir = root_dir / "CertifyPro_v3.1"
    
    if not target_dir.exists():
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Cannot create target directory {target_dir}: {e}")
            sys.exit(1)
    
    dist_certifypro = root_dir / "dist" / "CertifyPro"
    dist_launcher = root_dir / "dist" / "launcher"
    
    certifypro_src = dist_certifypro / "CertifyPro.exe"
    launcher_src = dist_launcher / "launcher.exe"
    
    try:
        if certifypro_src.exists():
            print(" -> Copying CertifyPro.exe...")
            shutil.copy2(certifypro_src, target_dir / "CertifyPro.exe")
            
        if launcher_src.exists():
            print(" -> Copying launcher.exe...")
            shutil.copy2(launcher_src, target_dir / "launcher.exe")
            
        # Merge _internal from both builds
        target_internal = target_dir / "_internal"
        if target_internal.exists():
            shutil.rmtree(target_internal)
            
        if (dist_certifypro / "_internal").exists():
            print(" -> Copying _internal from CertifyPro...")
            shutil.copytree(dist_certifypro / "_internal", target_internal, dirs_exist_ok=True)
            
        if (dist_launcher / "_internal").exists():
            print(" -> Merging _internal from launcher...")
            shutil.copytree(dist_launcher / "_internal", target_internal, dirs_exist_ok=True)
            
        # Copy resources (datas)
        print(" -> Copying resources & data...")
        for res in ["resources", "data"]:
            for source_dist in [dist_certifypro, dist_launcher]:
                src_folder = source_dist / res
                if src_folder.exists():
                    shutil.copytree(src_folder, target_dir / res, dirs_exist_ok=True)
            
        print("\n=== SUCCESSFULLY DEPLOYED ===")
        print(f"The executables have been updated in: {target_dir}")
        print("You can now test the application.")
        
    except Exception as e:
        print(f"\n[ERROR] File copy operation failed: {e}")
        sys.exit(1)

    # 5. Очистка временных папок
    print("\n=== 5. CLEANING TEMP FOLDERS ===")
    for folder in ["build", "dist"]:
        folder_path = root_dir / folder
        if folder_path.exists():
            try:
                safe_rmtree(folder_path)
                print(f" -> Removed {folder}/")
            except Exception as e:
                print(f" [WARNING] Could not remove {folder}/: {e}")
    
    # 6. Видалення непотрібних пакетів з _internal (транзитивні залежності pandas)
    print("\n=== 6. REMOVING UNUSED PACKAGES FROM _internal ===")
    internal_dir = target_dir / "_internal"
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
    # Видалення pandas/tests та pandas/_testing (тестові файли не потрібні в продакшені)
    for pandas_subdir in ["tests", "_testing"]:
        pandas_sub = internal_dir / "pandas" / pandas_subdir
        if pandas_sub.exists():
            try:
                safe_rmtree(pandas_sub)
                print(f" -> Removed pandas/{pandas_subdir}/")
            except Exception as e:
                print(f" [WARNING] Could not remove pandas/{pandas_subdir}/: {e}")
    
    for item_name in unused_items:
        item_path = internal_dir / item_name
        if item_path.exists():
            try:
                if item_path.is_dir():
                    safe_rmtree(item_path)
                else:
                    os.remove(item_path)
                print(f" -> Removed {item_name}/")
            except Exception as e:
                print(f" [WARNING] Could not remove {item_name}/: {e}")
    
    # Видалення runtime hook для matplotlib
    mpl_hook = internal_dir / "pyi_rth_mplconfig"
    if mpl_hook.exists():
        try:
            os.remove(mpl_hook)
            print(f" -> Removed pyi_rth_mplconfig")
        except Exception as e:
            print(f" [WARNING] Could not remove pyi_rth_mplconfig: {e}")
    
    print("\n=== CLEANUP COMPLETE ===")
