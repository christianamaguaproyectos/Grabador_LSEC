"""
Wrapper de MediaPipe para detección de manos.

Encapsula la lógica de detección y dibujo de keypoints,
facilitando el cambio de versión de MediaPipe en el futuro
(Strategy Pattern).
"""

import logging
from typing import Optional, Any

import cv2
import numpy as np
import mediapipe as mp

from config import (
    MEDIAPIPE_CONFIANZA_DETECCION_MINIMA,
    MEDIAPIPE_CONFIANZA_SEGUIMIENTO_MINIMA,
    NUMERO_MAXIMO_MANOS,
)

logger = logging.getLogger(__name__)


class ResultadoDeteccion:
    """Resultado de la detección de manos en un frame.

    Attributes:
        manos_detectadas: Número de manos detectadas.
        landmarks: Lista de landmarks por mano (21 puntos c/u).
        frame_anotado: Frame con los keypoints dibujados.
    """

    def __init__(
        self,
        manos_detectadas: int = 0,
        landmarks: Optional[list] = None,
        frame_anotado: Optional[np.ndarray] = None,
    ) -> None:
        self.manos_detectadas: int = manos_detectadas
        self.landmarks: list = landmarks or []
        self.frame_anotado: Optional[np.ndarray] = frame_anotado

    @property
    def hay_deteccion(self) -> bool:
        """Indica si se detectó al menos una mano."""
        return self.manos_detectadas > 0


class DetectorMediaPipe:
    """Detector de manos usando MediaPipe Hands.

    Implementa el patrón Strategy: se puede reemplazar por
    otra implementación de detector sin cambiar el código cliente.

    Attributes:
        _hands: Instancia de MediaPipe Hands.
        _mp_hands: Módulo de hands de MediaPipe.
        _mp_drawing: Módulo de dibujo de MediaPipe.
        _mp_drawing_styles: Estilos de dibujo de MediaPipe.
    """

    def __init__(
        self,
        confianza_deteccion: float = MEDIAPIPE_CONFIANZA_DETECCION_MINIMA,
        confianza_seguimiento: float = MEDIAPIPE_CONFIANZA_SEGUIMIENTO_MINIMA,
        max_manos: int = NUMERO_MAXIMO_MANOS,
    ) -> None:
        """Inicializa el detector de MediaPipe.

        Args:
            confianza_deteccion: Confianza mínima para detección.
            confianza_seguimiento: Confianza mínima para seguimiento.
            max_manos: Número máximo de manos a detectar.
        """
        self._mp_hands = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_drawing_styles = mp.solutions.drawing_styles

        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_manos,
            min_detection_confidence=confianza_deteccion,
            min_tracking_confidence=confianza_seguimiento,
        )

        logger.info(
            "MediaPipe Hands inicializado (detección: %.1f, seguimiento: %.1f, "
            "max manos: %d).",
            confianza_deteccion,
            confianza_seguimiento,
            max_manos,
        )

    def detectar(self, frame: np.ndarray) -> ResultadoDeteccion:
        """Detecta manos en un frame y dibuja los keypoints.

        Args:
            frame: Frame BGR de OpenCV.

        Returns:
            ResultadoDeteccion con la información de la detección.
        """
        # MediaPipe requiere RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultados = self._hands.process(frame_rgb)

        frame_anotado = frame.copy()
        manos_detectadas = 0
        landmarks_lista: list[Any] = []

        if resultados.multi_hand_landmarks:
            manos_detectadas = len(resultados.multi_hand_landmarks)

            for hand_landmarks in resultados.multi_hand_landmarks:
                landmarks_lista.append(hand_landmarks)
                self._dibujar_landmarks(frame_anotado, hand_landmarks)

        return ResultadoDeteccion(
            manos_detectadas=manos_detectadas,
            landmarks=landmarks_lista,
            frame_anotado=frame_anotado,
        )

    def _dibujar_landmarks(
        self, frame: np.ndarray, hand_landmarks: Any
    ) -> None:
        """Dibuja los 21 keypoints y conexiones de una mano.

        Args:
            frame: Frame donde dibujar (se modifica in-place).
            hand_landmarks: Landmarks de la mano detectada.
        """
        self._mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            self._mp_hands.HAND_CONNECTIONS,
            self._mp_drawing_styles.get_default_hand_landmarks_style(),
            self._mp_drawing_styles.get_default_hand_connections_style(),
        )

    def cerrar(self) -> None:
        """Libera los recursos de MediaPipe."""
        self._hands.close()
        logger.info("MediaPipe Hands cerrado correctamente.")

    def __enter__(self) -> "DetectorMediaPipe":
        """Context manager: entrada."""
        return self

    def __exit__(self, tipo_exc: object, valor_exc: object, tb: object) -> None:
        """Context manager: salida."""
        self.cerrar()
