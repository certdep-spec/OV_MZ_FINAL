# -*- mode: python ; coding: utf-8 -*-
"""
Spec для сборки launcher.exe (выбор клиента).
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

FINAL_ROOT = Path(os.getcwd()).resolve()
SRC_DIR = FINAL_ROOT / "src" / "client_launcher"
CERTIFYPRO_RESOURCES = FINAL_ROOT / "CERTIFYPRO" / "resources"
CERTIFYPRO_CORE = FINAL_ROOT / "CERTIFYPRO" / "core"

# Collect dependencies
import importlib.util
import sys

# Get customtkinter location
ctk_spec = importlib.util.find_spec('customtkinter')
ctk_path = Path(ctk_spec.submodule_search_locations[0]) if ctk_spec and ctk_spec.submodule_search_locations else None

yaml_datas, yaml_binaries, yaml_hiddenimports = [], [], []

vcruntime_path = r'C:\Windows\System32\vcruntime140_1.dll'
vcruntime_binaries = [(vcruntime_path, '.')] if os.path.exists(vcruntime_path) else []

a = Analysis(
    [str(SRC_DIR / 'launcher.py')],
    pathex=[str(SRC_DIR), str(FINAL_ROOT)],
    binaries=yaml_binaries + vcruntime_binaries,
    datas=yaml_datas + [
        (str(CERTIFYPRO_RESOURCES / 'profiles.yaml'), 'resources'),
        (str(FINAL_ROOT / 'config' / 'window_geometry.json'), '.'),
        (str(SRC_DIR), 'client_launcher'),
        (str(CERTIFYPRO_CORE / 'utils' / 'path_provider.py'), 'CERTIFYPRO/core/utils'),
    ] + ([(str(ctk_path), 'customtkinter')] if ctk_path else []),
    hiddenimports=yaml_hiddenimports + [
        'customtkinter',
        'darkdetect',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.ttk',
        'yaml',
        'sqlite3',
        'queue',
        'threading',
        'logging',
        'pathlib',
    ],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['win32com', 'torch', 'torchvision', 'torchaudio', 'basicsr', 'facexlib', 'gfpgan', 'realesrgan', 'tensorflow'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='launcher',
)
