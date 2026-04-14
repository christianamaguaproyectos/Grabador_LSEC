"""Utilidades de validacion para el sistema de grabacion LSEC.

Valida la disponibilidad de la camara, archivos de lista de senas y nombres de participantes
antes de que comience la sesion de grabacion.
"""

import logging
import os
from pathlib import Path

import cv2

from config import INDICE_CAMARA, ARCHIVO_LISTA_SENAS

logger = logging.getLogger(__name__)


def validar_camara(indice_camara: int = INDICE_CAMARA) -> bool:
    """Verifica si una cámara está disponible en el índice dado.

    Args:
        indice_camara: Índice del dispositivo de cámara a verificar.

    Returns:
        True si la cámara está disponible y puede capturar cuadros.
    """
    cap = cv2.VideoCapture(indice_camara)
    if not cap.isOpened():
        logger.error("No se pudo abrir la cámara en el índice %d", indice_camara)
        return False

    ret, cuadro = cap.read()
    cap.release()

    if not ret or cuadro is None:
        logger.error("La cámara se abrió pero no puede capturar cuadros")
        return False

    logger.info("Cámara validada correctamente en el índice %d", indice_camara)
    return True


def cargar_lista_senas(ruta_archivo: str = ARCHIVO_LISTA_SENAS) -> list[str]:
    """Carga y valida el archivo de lista de señas.

    Args:
        ruta_archivo: Ruta al archivo de texto que contiene nombres de señas (una por línea).

    Returns:
        Lista de nombres de señas (limpios, en minúsculas, no vacíos).

    Raises:
        FileNotFoundError: Si el archivo de lista de señas no existe.
        ValueError: Si el archivo de lista de señas está vacío o no tiene entradas válidas.
    """
    ruta = Path(ruta_archivo)

    if not ruta.exists():
        raise FileNotFoundError(
            f"El archivo de señas '{ruta_archivo}' no existe. "
            f"Crea el archivo con una seña por línea."
        )

    lineas_crudas = ruta.read_text(encoding="utf-8").splitlines()

    # Limpiar: quitar espacios, convertir a minúsculas, eliminar vacías
    senas = []
    for linea in lineas_crudas:
        limpia = linea.strip().lower()
        if limpia:
            # Reemplazar espacios internos con guion bajo para uso en carpetas
            sanitizada = sanitizar_nombre_carpeta(limpia)
            senas.append(sanitizada)

    if not senas:
        raise ValueError(
            f"El archivo '{ruta_archivo}' está vacío o no contiene señas válidas."
        )

    # Eliminar duplicados preservando el orden
    vistas: set[str] = set()
    senas_unicas: list[str] = []
    for sena in senas:
        if sena not in vistas:
            vistas.add(sena)
            senas_unicas.append(sena)

    duplicados_eliminados = len(senas) - len(senas_unicas)
    if duplicados_eliminados > 0:
        logger.warning(
            "Se eliminaron %d señas duplicadas del archivo", duplicados_eliminados
        )

    logger.info("Se cargaron %d señas desde '%s'", len(senas_unicas), ruta_archivo)
    return senas_unicas


def cargar_lista_senas(ruta_archivo: str = ARCHIVO_LISTA_SENAS) -> list[str]:
    """Carga y valida el archivo de lista de señas.

    Args:
        ruta_archivo: Ruta al archivo de texto que contiene nombres de señas (una por línea).

    Returns:
        Lista de nombres de señas (limpios, en minúsculas, no vacíos).

    Raises:
        FileNotFoundError: Si el archivo de lista de señas no existe.
        ValueError: Si el archivo de lista de señas está vacío o no tiene entradas válidas.
    """
    ruta = Path(ruta_archivo)

    if not ruta.exists():
        raise FileNotFoundError(
            f"El archivo de señas '{ruta_archivo}' no existe. "
            f"Crea el archivo con una seña por línea."
        )

    lineas_crudas = ruta.read_text(encoding="utf-8").splitlines()

    # Limpiar: quitar espacios, convertir a minúsculas, eliminar vacías
    senas = []
    for linea in lineas_crudas:
        limpia = linea.strip().lower()
        if limpia:
            # Reemplazar espacios internos con guion bajo para uso en carpetas
            sanitizada = sanitizar_nombre_carpeta(limpia)
            senas.append(sanitizada)

    if not senas:
        raise ValueError(
            f"El archivo '{ruta_archivo}' está vacío o no contiene señas válidas."
        )

    # Eliminar duplicados preservando el orden
    vistas: set[str] = set()
    senas_unicas: list[str] = []
    for sena in senas:
        if sena not in vistas:
            vistas.add(sena)
            senas_unicas.append(sena)

    duplicados_eliminados = len(senas) - len(senas_unicas)
    if duplicados_eliminados > 0:
        logger.warning(
            "Se eliminaron %d señas duplicadas del archivo", duplicados_eliminados
        )

    logger.info("Se cargaron %d señas desde '%s'", len(senas_unicas), ruta_archivo)
    return senas_unicas


def validar_nombre_participante(nombre: str) -> tuple[bool, str]:
    """Valida y sanitiza el nombre del participante.

    Args:
        nombre: Entrada cruda del nombre del participante.

    Returns:
        Tupla (es_valido, mensaje_de_error_o_nombre_sanitizado).
    """
    nombre_sanitizado = nombre.strip().lower()

    if not nombre_sanitizado:
        return False, "El nombre no puede estar vacío."

    if " " in nombre_sanitizado:
        return False, "El nombre no debe contener espacios."

    # Solo permitir letras, números y guiones bajos
    nombre_final = "".join(
        c for c in nombre_sanitizado if c.isalnum() or c in ("_", "-")
    )

    if not nombre_final:
        return (
            False,
            "El nombre solo contiene caracteres inválidos. Usa letras y números.",
        )

    if nombre_final != nombre_sanitizado:
        return (
            False,
            "El nombre contiene caracteres inválidos. Usa solo letras, números, guiones o guiones bajos.",
        )

    return True, nombre_final


def sanitizar_nombre_carpeta(nombre: str) -> str:
    """Sanitiza una cadena para que sea segura de usar como nombre de carpeta/archivo.

    Reemplaza espacios con guiones bajos y elimina caracteres que no son
    alfanuméricos, guiones bajos o guiones.

    Args:
        nombre: Cadena cruda a sanitizar.

    Returns:
        Cadena sanitizada segura para el sistema de archivos.
    """
    # Reemplazar espacios con guiones bajos
    nombre = nombre.replace(" ", "_")
    # Mantener solo alfanuméricos, guiones bajos y guiones
    return "".join(c for c in nombre if c.isalnum() or c in ("_", "-"))


def validar_directorio_dataset(directorio_dataset: str) -> Path:
    """Asegura que el directorio de salida exista, creándolo si es necesario.

    Args:
        directorio_dataset: Ruta al directorio raíz del dataset.

    Returns:
        Objeto Path para el directorio del dataset.
    """
    ruta = Path(directorio_dataset)
    ruta.mkdir(parents=True, exist_ok=True)
    logger.info("Directorio de dataset verificado: %s", ruta.resolve())
    return ruta


def obtener_repeticiones_existentes(
    directorio_dataset: str, nombre_sena: str, nombre_participante: str
) -> int:
    """Cuenta las repeticiones existentes para una sena y un participante dados.

    Util para reanudar sesiones interrumpidas.

    Args:
        directorio_dataset: Ruta al directorio raiz del dataset.
        nombre_sena: Nombre de la sena.
        nombre_participante: Nombre del participante.

    Returns:
        Numero de archivos de repeticion existentes encontrados.
    """
    dir_sena = Path(directorio_dataset) / nombre_sena
    if not dir_sena.exists():
        return 0

    patron = f"{nombre_participante}_rep*"
    existentes = list(dir_sena.glob(patron))
    conteo = len(existentes)

    if conteo > 0:
        logger.info(
            "Encontradas %d repeticiones existentes para '%s' / '%s'",
            conteo,
            nombre_sena,
            nombre_participante,
        )

    return conteo
