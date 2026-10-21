# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None
project_root = Path.cwd()

# Collect submodules and data files
hidden_imports = [
    'retro',
    'retro.data',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'cv2',
    'PIL',
    'torch',
    'stable_baselines3',
    'psutil',
    'GPUtil',
    'imageio',
    'pokefirered',
    'pokefirered.gui',
    'pokefirered.gui.main_window',
    'pokefirered.gui.views',
    'pokefirered.gui.widgets',
    'pokefirered.gui.workers',
    'pokefirered.visualization',
    'pokefirered.models',
    'pokefirered.paths',
]
hidden_imports += collect_submodules('pokefirered')
hidden_imports += collect_submodules('retro')

datas = [
    ('assets', 'assets'),
    ('data/custom_integrations', 'data/custom_integrations'),
    ('scripts', 'scripts'),
]
datas += collect_data_files('retro')
datas += collect_data_files('stable_baselines3')
datas += copy_metadata('imageio')
datas += copy_metadata('stable_baselines3')

a = Analysis(
    ['main_gui.py'],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PokeRL_Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keeps console attached for live logs if run via terminal, GUI window shows normally
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'pwhiddy' / 'firered_player_sprites.png') if (project_root / 'assets' / 'pwhiddy' / 'firered_player_sprites.png').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PokeRL_Studio',
)
