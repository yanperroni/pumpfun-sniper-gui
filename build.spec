# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para PumpFun Visual Sniper
Gera um executavel unico com todas as dependencias
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Coletar dados do customtkinter
ctk_datas = collect_data_files('customtkinter')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=ctk_datas + [
        ('config', 'config'),
        ('core', 'core'),
        ('gui', 'gui'),
        ('installer', 'installer'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'cv2',
        'numpy',
        'pytesseract',
        'aiohttp',
        'requests',
        'ctypes',
        'ctypes.wintypes',
        'asyncio',
        'threading',
        'json',
        'dataclasses',
        'typing',
        're',
        'subprocess',
        'tempfile',
        'io',
    ] + collect_submodules('customtkinter'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PumpFunSniper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app, sem console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # Descomentar se tiver icone
)
