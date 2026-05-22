# -*- mode: python ; coding: utf-8 -*-
"""
Spec для сборки CertifyPro.exe (основное приложение).

Собирает из CERTIFYPRO/core/main.py - мультиклиентская версия.
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

FINAL_ROOT = Path(os.getcwd()).resolve()
CERTIFYPRO_CORE = FINAL_ROOT / "CERTIFYPRO" / "core"
DATA_DIR = CERTIFYPRO_CORE / "data"
TEMPLATES_DIR = CERTIFYPRO_CORE / "resources" / "templates"

pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all('pandas')
yaml_datas, yaml_binaries, yaml_hiddenimports = [], [], []

vcruntime_path = r'C:\Windows\System32\vcruntime140_1.dll'
vcruntime_binaries = [(vcruntime_path, '.')] if os.path.exists(vcruntime_path) else []

a = Analysis(
    [str(CERTIFYPRO_CORE / 'main.py')],
    pathex=[str(CERTIFYPRO_CORE), str(FINAL_ROOT)],
    binaries=pandas_binaries + yaml_binaries + vcruntime_binaries,
    datas=pandas_datas + yaml_datas + [
        (str(CERTIFYPRO_CORE / 'config.py'), '.'),
        (str(CERTIFYPRO_CORE / 'exceptions.py'), '.'),
        (str(CERTIFYPRO_CORE / 'utils' / 'path_provider.py'), 'CERTIFYPRO/core/utils'),
        (str(FINAL_ROOT / 'CERTIFYPRO' / 'resources' / 'profiles.yaml'), 'resources'),
        (str(FINAL_ROOT / 'CERTIFYPRO' / 'resources' / 'templates'), 'resources/templates'),
        (str(CERTIFYPRO_CORE / 'database' / 'db_schema.sql'), 'CERTIFYPRO/core/database'),
    ],
    hiddenimports=pandas_hiddenimports + yaml_hiddenimports + [
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'customtkinter',
        'docxtpl',
        'docx',
        'dateutil',
        'sqlite3',
        'tkinter',
        'PIL',
        'PIL._imaging',
        'lxml',
        'babel',
        'dotenv',
    ],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['win32com', 'torch', 'torchvision', 'torchaudio', 'basicsr', 'facexlib', 'gfpgan', 'realesrgan', 'tensorflow'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CertifyPro',
    console=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    a.scripts,
    name='CertifyPro',
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
