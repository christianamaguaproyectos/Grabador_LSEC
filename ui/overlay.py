"""
Overlay visual para la interfaz del grabador LSEC.

Dibuja todos los elementos visuales sobre los frames de cámara:
textos informativos, barras de progreso, indicadores de estado
y pantallas de preparación/grabación.
"""

from typing import Optional
import cv2
import numpy as np

from config import (
    FUENTE,
    FUENTE_NEGRITA,
    COLOR_EXITO,
    COLOR_ADVERTENCIA,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_FONDO,
    COLOR_BARRA_PROGRESO,
    COLOR_BARRA_FONDO,
    COLOR_GRABANDO,
    COLOR_PAUSA,
    TAMANO_FUENTE_TITULO,
    TAMANO_FUENTE_SUBTITULO,
    TAMANO_FUENTE_INFO,
    TAMANO_FUENTE_INDICADOR,
    GROSOR_TITULO,
    GROSOR_SUBTITULO,
    GROSOR_INFO,
    GROSOR_INDICADOR,
    BARRA_ALTO,
    BARRA_MARGEN_INFERIOR,
    BARRA_MARGEN_LATERAL,
    OVERLAY_OPACIDAD,
    VIDEO_ANCHO,
    VIDEO_ALTO,
)


def aplicar_overlay_oscuro(frame: np.ndarray) -> np.ndarray:
    """Aplica un fondo semitransparente oscuro sobre el frame.

    Args:
        frame: Frame original.

    Returns:
        Frame con overlay oscuro aplicado.
    """
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (VIDEO_ANCHO, VIDEO_ALTO), COLOR_FONDO, -1)
    return cv2.addWeighted(overlay, OVERLAY_OPACIDAD, frame, 1 - OVERLAY_OPACIDAD, 0)


def dibujar_texto_centrado(
    frame: np.ndarray,
    texto: str,
    posicion_y: int,
    tamano: float = TAMANO_FUENTE_TITULO,
    color: tuple = COLOR_INFO,
    grosor: int = GROSOR_TITULO,
) -> None:
    """Dibuja texto centrado horizontalmente en el frame.

    Args:
        frame: Frame donde dibujar.
        texto: Texto a mostrar.
        posicion_y: Posición vertical (Y).
        tamano: Tamaño de la fuente.
        color: Color del texto (BGR).
        grosor: Grosor del texto.
    """
    (ancho_texto, _), _ = cv2.getTextSize(texto, FUENTE_NEGRITA, tamano, grosor)
    posicion_x = (VIDEO_ANCHO - ancho_texto) // 2
    cv2.putText(
        frame, texto, (posicion_x, posicion_y),
        FUENTE_NEGRITA, tamano, color, grosor, cv2.LINE_AA,
    )


def dibujar_barra_progreso(
    frame: np.ndarray,
    progreso: float,
    posicion_y: int = -1,
    color: tuple = COLOR_BARRA_PROGRESO,
    etiqueta: str = "",
) -> None:
    """Dibuja una barra de progreso horizontal.

    Args:
        frame: Frame donde dibujar.
        progreso: Valor entre 0.0 y 1.0.
        posicion_y: Posición Y de la barra (-1 = parte inferior).
        color: Color de la barra de progreso.
        etiqueta: Texto opcional a mostrar sobre la barra.
    """
    if posicion_y < 0:
        posicion_y = VIDEO_ALTO - BARRA_MARGEN_INFERIOR

    x_inicio = BARRA_MARGEN_LATERAL
    x_fin = VIDEO_ANCHO - BARRA_MARGEN_LATERAL
    y_inicio = posicion_y
    y_fin = posicion_y + BARRA_ALTO

    # Fondo de la barra
    cv2.rectangle(frame, (x_inicio, y_inicio), (x_fin, y_fin), COLOR_BARRA_FONDO, -1)

    # Progreso
    progreso_clamped = max(0.0, min(1.0, progreso))
    ancho_progreso = int((x_fin - x_inicio) * progreso_clamped)
    if ancho_progreso > 0:
        cv2.rectangle(
            frame, (x_inicio, y_inicio),
            (x_inicio + ancho_progreso, y_fin), color, -1,
        )

    # Borde
    cv2.rectangle(frame, (x_inicio, y_inicio), (x_fin, y_fin), COLOR_INFO, 1)

    # Etiqueta centrada en la barra
    if etiqueta:
        (ancho_texto, alto_texto), _ = cv2.getTextSize(
            etiqueta, FUENTE, TAMANO_FUENTE_INFO, GROSOR_INFO,
        )
        texto_x = (x_inicio + x_fin - ancho_texto) // 2
        texto_y = y_inicio + (BARRA_ALTO + alto_texto) // 2
        cv2.putText(
            frame, etiqueta, (texto_x, texto_y),
            FUENTE, TAMANO_FUENTE_INFO, COLOR_INFO, GROSOR_INFO, cv2.LINE_AA,
        )


def dibujar_pantalla_preparacion(
    frame: np.ndarray,
    nombre_sena: str,
    segundos_restantes: int,
    indice_sena: int,
    total_senas: int,
    numero_repeticion: int,
    total_repeticiones: int,
    progreso_general: float,
    imagen_referencia: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Dibuja la pantalla de preparación antes de cada grabación.

    Args:
        frame: Frame de cámara actual.
        nombre_sena: Nombre de la seña a grabar.
        segundos_restantes: Segundos restantes de cuenta regresiva.
        indice_sena: Índice actual de la seña (base 1).
        total_senas: Total de señas.
        numero_repeticion: Número de repetición actual.
        total_repeticiones: Total de repeticiones.
        progreso_general: Progreso general (0.0 a 1.0).

    Returns:
        Frame con la pantalla de preparación dibujada.
    """
    frame_overlay = aplicar_overlay_oscuro(frame)

    # Nombre de la seña en mayúsculas al centro
    dibujar_texto_centrado(
        frame_overlay, nombre_sena.upper(),
        VIDEO_ALTO // 2 - 40, TAMANO_FUENTE_TITULO, COLOR_INFO, GROSOR_TITULO,
    )

    # Cuenta regresiva
    texto_cuenta = f"Preparate... {segundos_restantes} segundos"
    dibujar_texto_centrado(
        frame_overlay, texto_cuenta,
        VIDEO_ALTO // 2 + 30, TAMANO_FUENTE_SUBTITULO,
        COLOR_ADVERTENCIA, GROSOR_SUBTITULO,
    )

    # Indicador de seña (esquina superior izquierda)
    texto_sena = f"Sena {indice_sena} de {total_senas}"
    cv2.putText(
        frame_overlay, texto_sena, (15, 30),
        FUENTE, TAMANO_FUENTE_INDICADOR, COLOR_INFO, GROSOR_INDICADOR, cv2.LINE_AA,
    )

    # Indicador de repetición (esquina superior derecha)
    texto_rep = f"Rep {numero_repeticion} de {total_repeticiones}"
    (ancho_texto, _), _ = cv2.getTextSize(
        texto_rep, FUENTE, TAMANO_FUENTE_INDICADOR, GROSOR_INDICADOR,
    )
    cv2.putText(
        frame_overlay, texto_rep, (VIDEO_ANCHO - ancho_texto - 15, 30),
        FUENTE, TAMANO_FUENTE_INDICADOR, COLOR_INFO, GROSOR_INDICADOR, cv2.LINE_AA,
    )

    # Barra de progreso general
    etiqueta_progreso = f"Progreso: {progreso_general * 100:.0f}%"
    dibujar_barra_progreso(frame_overlay, progreso_general, etiqueta=etiqueta_progreso)

    if imagen_referencia is not None:
        dibujar_imagen_referencia(frame_overlay, imagen_referencia)

    return frame_overlay


def dibujar_pantalla_grabacion(
    frame: np.ndarray,
    nombre_sena: str,
    progreso_grabacion: float,
    frames_grabados: int,
    manos_detectadas: bool,
    indice_sena: int,
    total_senas: int,
    numero_repeticion: int,
    total_repeticiones: int,
    imagen_referencia: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Dibuja la pantalla durante la grabación activa.

    Muestra la imagen de cámara en vivo con indicadores de grabación,
    detección de manos y progreso.

    Args:
        frame: Frame de cámara con keypoints de MediaPipe dibujados.
        nombre_sena: Nombre de la seña que se está grabando.
        progreso_grabacion: Progreso de la grabación actual (0.0 a 1.0).
        frames_grabados: Cantidad de frames grabados hasta ahora.
        manos_detectadas: Si se detectaron manos en el frame actual.
        indice_sena: Índice de la seña actual (base 1).
        total_senas: Total de señas.
        numero_repeticion: Repetición actual.
        total_repeticiones: Total de repeticiones.

    Returns:
        Frame con la interfaz de grabación dibujada.
    """
    frame_ui = frame.copy()

    # Indicador de grabación (esquina superior izquierda)
    # Círculo rojo parpadeante
    cv2.circle(frame_ui, (20, 25), 8, COLOR_GRABANDO, -1)
    texto_grabando = f"GRABANDO - {nombre_sena.upper()}"
    cv2.putText(
        frame_ui, texto_grabando, (35, 32),
        FUENTE, TAMANO_FUENTE_INDICADOR, COLOR_GRABANDO,
        GROSOR_INDICADOR, cv2.LINE_AA,
    )

    # Indicador de seña y repetición (debajo del indicador de grabación)
    texto_progreso = (
        f"Sena {indice_sena}/{total_senas} | "
        f"Rep {numero_repeticion}/{total_repeticiones}"
    )
    cv2.putText(
        frame_ui, texto_progreso, (15, 60),
        FUENTE, TAMANO_FUENTE_INFO, COLOR_INFO, GROSOR_INFO, cv2.LINE_AA,
    )

    # Contador de frames (esquina superior derecha)
    texto_frames = f"Frames: {frames_grabados}"
    (ancho_texto, _), _ = cv2.getTextSize(
        texto_frames, FUENTE, TAMANO_FUENTE_INFO, GROSOR_INFO,
    )
    cv2.putText(
        frame_ui, texto_frames, (VIDEO_ANCHO - ancho_texto - 15, 60),
        FUENTE, TAMANO_FUENTE_INFO, COLOR_INFO, GROSOR_INFO, cv2.LINE_AA,
    )

    # Indicador de detección de manos
    if manos_detectadas:
        texto_manos = "Manos detectadas"
        color_manos = COLOR_EXITO
    else:
        texto_manos = "Sin deteccion"
        color_manos = COLOR_ADVERTENCIA

    (ancho_texto, _), _ = cv2.getTextSize(
        texto_manos, FUENTE, TAMANO_FUENTE_INFO, GROSOR_INFO,
    )
    cv2.putText(
        frame_ui, texto_manos, (VIDEO_ANCHO - ancho_texto - 15, 30),
        FUENTE, TAMANO_FUENTE_INFO, color_manos, GROSOR_INFO, cv2.LINE_AA,
    )

    # Barra de progreso de la grabación actual
    segundos_transcurridos = progreso_grabacion * 3  # DURACION_GRABACION_SEGUNDOS
    etiqueta = f"{segundos_transcurridos:.1f}s / 3.0s"
    dibujar_barra_progreso(
        frame_ui, progreso_grabacion,
        color=COLOR_GRABANDO, etiqueta=etiqueta,
    )

    if imagen_referencia is not None:
        dibujar_imagen_referencia(frame_ui, imagen_referencia)

    return frame_ui


def dibujar_pantalla_pausa(frame: np.ndarray) -> np.ndarray:
    """Dibuja la pantalla de pausa sobre el frame actual.

    Args:
        frame: Frame de cámara actual.

    Returns:
        Frame con la pantalla de pausa.
    """
    frame_overlay = aplicar_overlay_oscuro(frame)

    dibujar_texto_centrado(
        frame_overlay, "PAUSA",
        VIDEO_ALTO // 2 - 30, TAMANO_FUENTE_TITULO, COLOR_PAUSA, GROSOR_TITULO,
    )

    dibujar_texto_centrado(
        frame_overlay, "Presiona ESC para continuar",
        VIDEO_ALTO // 2 + 30, TAMANO_FUENTE_SUBTITULO,
        COLOR_INFO, GROSOR_SUBTITULO,
    )

    dibujar_texto_centrado(
        frame_overlay, "Presiona Q para salir",
        VIDEO_ALTO // 2 + 70, TAMANO_FUENTE_INFO,
        COLOR_ADVERTENCIA, GROSOR_INFO,
    )

    return frame_overlay


def dibujar_pantalla_pausa_manual(frame: np.ndarray) -> np.ndarray:
    """Dibuja la pantalla de pausa manual sobre el frame actual.

    Args:
        frame: Frame de cámara actual.

    Returns:
        Frame con la pantalla de pausa manual.
    """
    frame_overlay = aplicar_overlay_oscuro(frame)

    dibujar_texto_centrado(
        frame_overlay, "EN PAUSA",
        VIDEO_ALTO // 2 - 30, TAMANO_FUENTE_TITULO, COLOR_PAUSA, GROSOR_TITULO,
    )

    dibujar_texto_centrado(
        frame_overlay, "Presiona P o Espacio para reanudar",
        VIDEO_ALTO // 2 + 30, TAMANO_FUENTE_SUBTITULO,
        COLOR_INFO, GROSOR_SUBTITULO,
    )

    return frame_overlay


def dibujar_imagen_referencia(frame: np.ndarray, imagen_referencia: np.ndarray) -> None:
    """Dibuja la imagen de referencia en la esquina superior derecha.

    Args:
        frame: Frame original.
        imagen_referencia: Imagen redimensionada de la seña.
    """
    alto_ref, ancho_ref = imagen_referencia.shape[:2]
    
    margen_x = 15
    margen_y = 80  # Debajo del texto superior derecho

    x_inicio = VIDEO_ANCHO - ancho_ref - margen_x
    y_inicio = margen_y
    x_fin = x_inicio + ancho_ref
    y_fin = y_inicio + alto_ref

    # Asegurar que no se sale de los límites
    if x_inicio < 0 or y_inicio < 0 or x_fin > VIDEO_ANCHO or y_fin > VIDEO_ALTO:
        return

    # Usar ROI para superponer
    frame[y_inicio:y_fin, x_inicio:x_fin] = imagen_referencia

    # Borde de la imagen
    cv2.rectangle(frame, (x_inicio, y_inicio), (x_fin, y_fin), COLOR_INFO, 1)


def dibujar_pantalla_pausa_entre_senas(
    frame: np.ndarray,
    segundos_restantes: int,
) -> np.ndarray:
    """Dibuja pantalla durante la pausa automática entre señas.

    Args:
        frame: Frame de cámara actual.
        segundos_restantes: Segundos restantes de pausa.

    Returns:
        Frame con la pantalla de pausa entre señas.
    """
    frame_overlay = aplicar_overlay_oscuro(frame)

    dibujar_texto_centrado(
        frame_overlay, "Descanso...",
        VIDEO_ALTO // 2 - 20, TAMANO_FUENTE_SUBTITULO,
        COLOR_INFO, GROSOR_SUBTITULO,
    )

    dibujar_texto_centrado(
        frame_overlay, f"Siguiente en {segundos_restantes}s",
        VIDEO_ALTO // 2 + 30, TAMANO_FUENTE_SUBTITULO,
        COLOR_ADVERTENCIA, GROSOR_SUBTITULO,
    )

    return frame_overlay


def dibujar_pantalla_resumen(
    frame: np.ndarray,
    total_videos: int,
    tiempo_total_segundos: float,
    senas_completadas: int,
    total_senas: int,
    carpetas_creadas: int,
) -> np.ndarray:
    """Dibuja la pantalla de resumen final de la sesión.

    Args:
        frame: Frame de cámara o frame negro.
        total_videos: Total de videos grabados.
        tiempo_total_segundos: Tiempo total en segundos.
        senas_completadas: Número de señas completadas.
        total_senas: Total de señas planificadas.
        carpetas_creadas: Número de carpetas creadas.

    Returns:
        Frame con el resumen final.
    """
    frame_resumen = aplicar_overlay_oscuro(frame)

    dibujar_texto_centrado(
        frame_resumen, "SESION FINALIZADA",
        80, TAMANO_FUENTE_TITULO, COLOR_EXITO, GROSOR_TITULO,
    )

    # Calcular minutos y segundos
    minutos = int(tiempo_total_segundos // 60)
    segundos = int(tiempo_total_segundos % 60)

    lineas_resumen = [
        f"Videos grabados: {total_videos}",
        f"Tiempo total: {minutos}m {segundos}s",
        f"Senas completadas: {senas_completadas} de {total_senas}",
        f"Carpetas creadas: {carpetas_creadas}",
    ]

    y_inicio = 160
    espacio_entre_lineas = 45
    for i, linea in enumerate(lineas_resumen):
        dibujar_texto_centrado(
            frame_resumen, linea,
            y_inicio + i * espacio_entre_lineas,
            TAMANO_FUENTE_SUBTITULO, COLOR_INFO, GROSOR_SUBTITULO,
        )

    # Instrucciones para continuar
    dibujar_texto_centrado(
        frame_resumen, "Para continuar en otra sesion,",
        VIDEO_ALTO - 100, TAMANO_FUENTE_INFO, COLOR_ADVERTENCIA, GROSOR_INFO,
    )
    dibujar_texto_centrado(
        frame_resumen, "ejecute el programa nuevamente con el mismo nombre.",
        VIDEO_ALTO - 75, TAMANO_FUENTE_INFO, COLOR_ADVERTENCIA, GROSOR_INFO,
    )
    dibujar_texto_centrado(
        frame_resumen, "Presione cualquier tecla para cerrar.",
        VIDEO_ALTO - 40, TAMANO_FUENTE_INFO, COLOR_INFO, GROSOR_INFO,
    )

    return frame_resumen
