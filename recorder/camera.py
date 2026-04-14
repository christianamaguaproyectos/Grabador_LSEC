"""
Abstracción de la cámara con OpenCV.

Proporciona una interfaz limpia para capturar frames
con configuración centralizada de resolución y FPS.
"""

import logging
from typing import Optional

import cv2
import numpy as np

from config import (
    INDICE_CAMARA,
    VIDEO_ANCHO,
    VIDEO_ALTO,
    VIDEO_FPS,
)

logger = logging.getLogger(__name__)


class Camara:
    """Gestiona la captura de video desde una cámara USB/integrada.

    Encapsula la configuración de OpenCV y proporciona
    métodos para leer frames de forma segura.

    Attributes:
        indice: Índice de la cámara.
        _captura: Objeto VideoCapture de OpenCV.
    """

    def __init__(self, indice: int = INDICE_CAMARA) -> None:
        """Inicializa la cámara.

        Args:
            indice: Índice de la cámara (0 = cámara principal).
        """
        self.indice: int = indice
        self._captura: Optional[cv2.VideoCapture] = None

    def abrir(self) -> bool:
        """Abre la cámara y configura resolución y FPS.

        Returns:
            True si la cámara se abrió correctamente.
        """
        logger.info("Abriendo cámara (índice: %d)...", self.indice)
        self._captura = cv2.VideoCapture(self.indice)

        if not self._captura.isOpened():
            logger.error("No se pudo abrir la cámara.")
            return False

        self._captura.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_ANCHO)
        self._captura.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_ALTO)
        self._captura.set(cv2.CAP_PROP_FPS, VIDEO_FPS)

        # Verificar resolución real obtenida
        ancho_real = int(self._captura.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto_real = int(self._captura.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(
            "Cámara abierta. Resolución: %dx%d.", ancho_real, alto_real
        )

        return True

    def leer_frame(self) -> tuple[bool, Optional[np.ndarray]]:
        """Lee un frame de la cámara.

        Returns:
            Tupla (éxito, frame). El frame es None si la lectura falla.
        """
        if self._captura is None or not self._captura.isOpened():
            return False, None

        exito, frame = self._captura.read()

        if not exito:
            logger.warning("No se pudo leer frame de la cámara.")
            return False, None

        # Voltear horizontalmente para efecto espejo (más natural)
        frame = cv2.flip(frame, 1)
        return True, frame

    def esta_abierta(self) -> bool:
        """Verifica si la cámara está abierta.

        Returns:
            True si la cámara está abierta y funcionando.
        """
        return self._captura is not None and self._captura.isOpened()

    def cerrar(self) -> None:
        """Libera los recursos de la cámara."""
        if self._captura is not None:
            self._captura.release()
            self._captura = None
            logger.info("Cámara cerrada correctamente.")

    def __enter__(self) -> "Camara":
        """Context manager: entrada."""
        self.abrir()
        return self

    def __exit__(self, tipo_exc: object, valor_exc: object, tb: object) -> None:
        """Context manager: salida."""
        self.cerrar()
