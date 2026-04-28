"""Resolución de rutas compatible con PyInstaller.

Proporciona funciones para obtener la ruta base de la aplicación
de forma transparente tanto en desarrollo como en un ejecutable
empaquetado con PyInstaller (modo --onedir).
"""

import sys
from pathlib import Path


def get_base_path() -> Path:
    """Retorna la ruta base donde viven los archivos editables.

    - En desarrollo: directorio raíz del proyecto.
    - En ejecutable PyInstaller (--onedir): directorio donde está el .exe.

    Uso: datos de salida (dataset/, session_log.csv, grabador_lsec.log)
         y recursos editables (lista_senas.txt, referencias/).
    """
    if getattr(sys, "frozen", False):
        # PyInstaller --onedir: sys.executable apunta al .exe
        return Path(sys.executable).parent
    # Desarrollo: este archivo está en utils/, subimos un nivel
    return Path(__file__).resolve().parent.parent


def get_internal_path() -> Path:
    """Retorna la ruta a recursos internos empaquetados por PyInstaller.

    - En desarrollo: directorio raíz del proyecto.
    - En ejecutable PyInstaller: directorio temporal _MEIPASS.

    Uso: recursos que se empaquetan DENTRO del bundle y no deben
         ser editados por el usuario (ej. módulos MediaPipe).
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent
