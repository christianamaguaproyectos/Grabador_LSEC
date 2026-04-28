# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para Grabador LSEC.

Genera un ejecutable en modo --onedir con todos los recursos
necesarios: MediaPipe models, OpenCV DLLs, imágenes de referencia
y lista de señas.

Uso:
    pyinstaller grabador_lsec.spec
"""

import os
import sys
from pathlib import Path

# ─── Rutas del entorno virtual ─────────────────────────────────
VENV_SITE = Path('venv/Lib/site-packages')
MEDIAPIPE_PATH = VENV_SITE / 'mediapipe'
CV2_PATH = VENV_SITE / 'cv2'

# ─── Datos a incluir DENTRO del bundle (_MEIPASS) ──────────────
# MediaPipe necesita sus módulos y modelos para funcionar
datas = [
    # MediaPipe modules (contiene los modelos .tflite)
    (str(MEDIAPIPE_PATH / 'modules'), 'mediapipe/modules'),
    # MediaPipe python solutions
    (str(MEDIAPIPE_PATH / 'python' / 'solutions'), 'mediapipe/python/solutions'),
    # MediaPipe calculators
    (str(MEDIAPIPE_PATH / 'calculators'), 'mediapipe/calculators'),
]

# ─── Binarios ──────────────────────────────────────────────────
binaries = [
    # OpenCV FFmpeg DLL
    (str(CV2_PATH / '*.dll'), 'cv2'),
]

# ─── Hidden imports que PyInstaller no detecta automáticamente ─
hiddenimports = [
    'mediapipe',
    'mediapipe.python',
    'mediapipe.python.solutions',
    'mediapipe.python.solutions.hands',
    'mediapipe.python.solutions.drawing_utils',
    'mediapipe.python.solutions.drawing_styles',
    'cv2',
    'numpy',
    'csv',
    'dataclasses',
    'pyparsing',
    'matplotlib',
]

# ─── Módulos a excluir (reducir tamaño) ────────────────────────
excludes = [
    'tkinter',
    'test',
    'pip',
    'wheel',
    'pydoc',
    'doctest',
    'mediapipe.model_maker',
    'mediapipe.examples',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GrabadorLSEC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Mantener consola para input del usuario
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # Descomentar cuando se tenga icono
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GrabadorLSEC',
)
