# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook для PyYAML (yaml)
Використовуємо collect_all для повного включення пакету
"""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("yaml")
