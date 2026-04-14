"""
Grabador de sesión principal.

Orquesta todo el flujo de grabación: preparación, grabación,
pausa, y gestión de archivos de video. Implementa callbacks
para eventos de inicio, fin y error de grabación.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Callable

import cv2
import numpy as np

from config import (
    DURACION_GRABACION_SEGUNDOS,
    CUENTA_REGRESIVA_PREPARACION_SEGUNDOS,
    PAUSA_ENTRE_SENAS_SEGUNDOS,
    VIDEO_FPS,
    VIDEO_ANCHO,
    VIDEO_ALTO,
    VIDEO_CODEC,
    VIDEO_EXTENSION,
    DIRECTORIO_RAIZ_DATASET,
    NOMBRE_VENTANA,
    TECLA_SALIR,
    TECLA_PAUSA,
    TECLA_PAUSA_MANUAL,
    TECLA_REPETIR,
    TECLA_ESPACIO,
    DIRECTORIO_REFERENCIAS,
    TAMANO_REFERENCIA,
    ConfiguracionSesion,
)
from recorder.camera import Camara
from recorder.mediapipe_detector import DetectorMediaPipe
from data.session_log import RegistradorSesion
from ui.overlay import (
    dibujar_pantalla_preparacion,
    dibujar_pantalla_grabacion,
    dibujar_pantalla_pausa,
    dibujar_pantalla_pausa_manual,
    dibujar_pantalla_pausa_entre_senas,
    dibujar_pantalla_resumen,
)

logger = logging.getLogger(__name__)


# Tipo para callbacks de eventos
CallbackEvento = Optional[Callable[..., None]]


class EstadisticasSesion:
    """Estadísticas acumuladas de la sesión de grabación.

    Attributes:
        total_videos: Videos grabados exitosamente.
        tiempo_inicio: Timestamp de inicio de la sesión.
        senas_completadas: Set de señas que completaron todas sus repeticiones.
        carpetas_creadas: Set de carpetas creadas.
    """

    def __init__(self) -> None:
        self.total_videos: int = 0
        self.tiempo_inicio: float = time.time()
        self.senas_completadas: set[str] = set()
        self.carpetas_creadas: set[str] = set()

    @property
    def tiempo_total(self) -> float:
        """Tiempo total transcurrido en segundos."""
        return time.time() - self.tiempo_inicio


class GrabadorSesion:
    """Orquestador principal de la sesión de grabación.

    Coordina la cámara, el detector de MediaPipe, el logger CSV
    y la interfaz visual para ejecutar el flujo completo de
    grabación del dataset LSEC.

    Attributes:
        configuracion: Configuración de la sesión actual.
        camara: Abstracción de la cámara.
        detector: Detector de MediaPipe.
        logger_sesion: Logger CSV.
        estadisticas: Estadísticas de la sesión.
        _en_pausa: Indica si la sesión está en pausa.
        _solicitar_salida: Indica si se solicitó salir.
    """

    def __init__(
        self,
        configuracion: ConfiguracionSesion,
        camara: Camara,
        detector: DetectorMediaPipe,
        logger_sesion: RegistradorSesion,
    ) -> None:
        """Inicializa el grabador de sesión.

        Args:
            configuracion: Configuración de la sesión.
            camara: Instancia de cámara abierta.
            detector: Detector de MediaPipe inicializado.
            logger_sesion: Logger CSV iniciado.
        """
        self.configuracion = configuracion
        self.camara = camara
        self.detector = detector
        self.logger_sesion = logger_sesion
        self.estadisticas = EstadisticasSesion()
        self._en_pausa: bool = False
        self._solicitar_salida: bool = False

    def _retroceder_a_repeticion_anterior(
        self,
        nombre_sena: str,
        numero_repeticion_actual: int,
        repeticiones_completadas: int,
        grabacion_actual: int,
    ) -> tuple[int, int, int, bool]:
        """Retrocede a la repetición anterior para volverla a grabar.

        Returns:
            Tupla (numero_repeticion, repeticiones_completadas,
            grabacion_actual, retrocedio).
        """
        if numero_repeticion_actual <= 1:
            logger.warning(
                "No hay una repetición anterior para la seña '%s'.",
                nombre_sena,
            )
            return (
                numero_repeticion_actual,
                repeticiones_completadas,
                grabacion_actual,
                False,
            )

        repeticion_anterior = numero_repeticion_actual - 1
        ruta_video_anterior = self.configuracion.ruta_video(
            nombre_sena, repeticion_anterior
        )

        if ruta_video_anterior.exists():
            try:
                ruta_video_anterior.unlink()
                logger.info(
                    "Video eliminado para regrabar: %s",
                    ruta_video_anterior,
                )
            except OSError as error:
                logger.warning(
                    "No se pudo eliminar el video anterior '%s': %s",
                    ruta_video_anterior,
                    error,
                )
        else:
            logger.info(
                "No existe archivo previo para eliminar en %s.",
                ruta_video_anterior,
            )

        logger.info(
            "Retrocediendo a %s repetición %d.",
            nombre_sena,
            repeticion_anterior,
        )

        repeticiones_completadas = max(0, repeticiones_completadas - 1)
        self.estadisticas.total_videos = max(
            0, self.estadisticas.total_videos - 1
        )
        grabacion_actual = max(0, grabacion_actual - 2)

        return (
            repeticion_anterior,
            repeticiones_completadas,
            grabacion_actual,
            True,
        )

    def ejecutar(self) -> None:
        """Ejecuta el flujo completo de grabación.

        Itera por cada seña y cada repetición, gestionando
        la preparación, grabación y pausas entre señas.
        """
        senas = self.configuracion.lista_senas
        total_senas = len(senas)
        repeticiones_por_sena = self.configuracion.repeticiones_por_sena
        total_grabaciones = total_senas * repeticiones_por_sena

        logger.info(
            "Iniciando sesión de grabación. Participante: %s, "
            "Señas: %d, Repeticiones por seña: %d, Total videos: %d.",
            self.configuracion.nombre_participante,
            total_senas,
            repeticiones_por_sena,
            total_grabaciones,
        )

        cv2.namedWindow(NOMBRE_VENTANA, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(NOMBRE_VENTANA, VIDEO_ANCHO, VIDEO_ALTO)

        grabacion_actual = 0

        for idx_sena, nombre_sena in enumerate(senas):
            if self._solicitar_salida:
                break

            # Saltar señas ya completadas (para retomar sesiones)
            if idx_sena < self.configuracion.sena_inicio:
                grabacion_actual += repeticiones_por_sena
                continue

            # Crear carpeta de la seña
            ruta_carpeta = Path(DIRECTORIO_RAIZ_DATASET) / nombre_sena
            ruta_carpeta.mkdir(parents=True, exist_ok=True)
            self.estadisticas.carpetas_creadas.add(nombre_sena)

            # Cargar imagen de referencia si existe
            imagen_referencia = None
            ruta_ref_jpg = Path(DIRECTORIO_REFERENCIAS) / f"{nombre_sena}.jpg"
            ruta_ref_png = Path(DIRECTORIO_REFERENCIAS) / f"{nombre_sena}.png"
            
            if ruta_ref_jpg.exists():
                img = cv2.imread(str(ruta_ref_jpg))
                if img is not None:
                    imagen_referencia = cv2.resize(img, TAMANO_REFERENCIA)
            elif ruta_ref_png.exists():
                img = cv2.imread(str(ruta_ref_png))
                if img is not None:
                    imagen_referencia = cv2.resize(img, TAMANO_REFERENCIA)

            repeticiones_completadas = 0
            num_rep = 1
            repeticion_minima_permitida = (
                self.configuracion.repeticion_inicio
                if idx_sena == self.configuracion.sena_inicio
                else 1
            )

            while num_rep <= repeticiones_por_sena:
                if self._solicitar_salida:
                    break

                # Saltar repeticiones ya completadas
                if (idx_sena == self.configuracion.sena_inicio
                        and num_rep < repeticion_minima_permitida):
                    grabacion_actual += 1
                    num_rep += 1
                    continue

                grabacion_actual += 1
                progreso = grabacion_actual / total_grabaciones

                # Verificar si el video ya existe (para no sobreescribir)
                ruta_video = self.configuracion.ruta_video(
                    nombre_sena, num_rep
                )
                if ruta_video.exists():
                    logger.info("Video ya existe, saltando: %s", ruta_video)
                    self.estadisticas.total_videos += 1
                    repeticiones_completadas += 1
                    num_rep += 1
                    continue

                # Fase 1: Preparación con cuenta regresiva
                estado_preparacion = self._fase_preparacion(
                    nombre_sena, idx_sena + 1, total_senas,
                    num_rep, repeticiones_por_sena, progreso,
                    imagen_referencia,
                )

                if estado_preparacion == "salir":
                    break
                if estado_preparacion == "repetir_anterior":
                    (
                        num_rep,
                        repeticiones_completadas,
                        grabacion_actual,
                        retrocedio,
                    ) = self._retroceder_a_repeticion_anterior(
                        nombre_sena,
                        num_rep,
                        repeticiones_completadas,
                        grabacion_actual,
                    )
                    if retrocedio and idx_sena == self.configuracion.sena_inicio:
                        repeticion_minima_permitida = min(
                            repeticion_minima_permitida,
                            num_rep,
                        )
                    continue

                # Fase 2: Grabación
                estado_grabacion = self._fase_grabacion(
                    nombre_sena, ruta_video,
                    idx_sena + 1, total_senas,
                    num_rep, repeticiones_por_sena,
                    imagen_referencia,
                )

                if estado_grabacion == "repetir_anterior":
                    (
                        num_rep,
                        repeticiones_completadas,
                        grabacion_actual,
                        retrocedio,
                    ) = self._retroceder_a_repeticion_anterior(
                        nombre_sena,
                        num_rep,
                        repeticiones_completadas,
                        grabacion_actual,
                    )
                    if retrocedio and idx_sena == self.configuracion.sena_inicio:
                        repeticion_minima_permitida = min(
                            repeticion_minima_permitida,
                            num_rep,
                        )
                    continue
                elif estado_grabacion == "exito":
                    repeticiones_completadas += 1
                elif estado_grabacion == "salir":
                    break
                else: 
                    # "salir" o "error"
                    if self._solicitar_salida:
                        break

                # Fase 3: Pausa entre señas (excepto en la última)
                es_ultima = (
                    idx_sena == total_senas - 1
                    and num_rep == repeticiones_por_sena
                )
                if not es_ultima and not self._solicitar_salida:
                    estado_pausa = self._fase_pausa_entre_senas()
                    if estado_pausa == "salir":
                        self._solicitar_salida = True
                        break
                    if estado_pausa == "repetir_anterior":
                        (
                            num_rep,
                            repeticiones_completadas,
                            grabacion_actual,
                            retrocedio,
                        ) = self._retroceder_a_repeticion_anterior(
                            nombre_sena,
                            num_rep + 1,
                            repeticiones_completadas,
                            grabacion_actual,
                        )
                        if (
                            retrocedio
                            and idx_sena == self.configuracion.sena_inicio
                        ):
                            repeticion_minima_permitida = min(
                                repeticion_minima_permitida,
                                num_rep,
                            )
                        continue
                    
                num_rep += 1

            # Marcar seña como completada si todas las repeticiones terminaron
            if repeticiones_completadas == repeticiones_por_sena:
                self.estadisticas.senas_completadas.add(nombre_sena)

        # Mostrar resumen final
        self._mostrar_resumen(total_senas)

    def _fase_preparacion(
        self,
        nombre_sena: str,
        indice_sena: int,
        total_senas: int,
        numero_repeticion: int,
        total_repeticiones: int,
        progreso_general: float,
        imagen_referencia: Optional[np.ndarray] = None,
    ) -> str:
        """Ejecuta la fase de preparación con cuenta regresiva.

        Args:
            nombre_sena: Nombre de la seña.
            indice_sena: Índice de la seña (base 1).
            total_senas: Total de señas.
            numero_repeticion: Repetición actual.
            total_repeticiones: Total de repeticiones.
            progreso_general: Progreso general (0.0 a 1.0).
            imagen_referencia: Imagen de referencia (opcional).

        Returns:
            "continuar", "salir" o "repetir_anterior".
        """
        tiempo_inicio = time.time()

        while True:
            tiempo_transcurrido = time.time() - tiempo_inicio
            segundos_restantes = max(
                0,
                CUENTA_REGRESIVA_PREPARACION_SEGUNDOS
                - int(tiempo_transcurrido),
            )

            if tiempo_transcurrido >= CUENTA_REGRESIVA_PREPARACION_SEGUNDOS:
                return "continuar"

            exito, frame = self.camara.leer_frame()
            if not exito or frame is None:
                continue

            frame_ui = dibujar_pantalla_preparacion(
                frame, nombre_sena, segundos_restantes,
                indice_sena, total_senas,
                numero_repeticion, total_repeticiones,
                progreso_general,
                imagen_referencia,
            )

            cv2.imshow(NOMBRE_VENTANA, frame_ui)

            accion, tiempo_pausado = self._procesar_teclas()
            if tiempo_pausado > 0:
                tiempo_inicio += tiempo_pausado
                
            if accion == "salir":
                return "salir"
            elif accion == "repetir_anterior":
                return "repetir_anterior"

        return "continuar"

    def _fase_grabacion(
        self,
        nombre_sena: str,
        ruta_video: Path,
        indice_sena: int,
        total_senas: int,
        numero_repeticion: int,
        total_repeticiones: int,
        imagen_referencia: Optional[np.ndarray] = None,
    ) -> str:
        """Ejecuta la fase de grabación de un video.

        Args:
            nombre_sena: Nombre de la seña.
            ruta_video: Ruta donde guardar el video.
            indice_sena: Índice de la seña (base 1).
            total_senas: Total de señas.
            numero_repeticion: Repetición actual.
            total_repeticiones: Total de repeticiones.
            imagen_referencia: Imagen de referencia (opcional).

        Returns:
            "exito", "error", "salir" o "repetir_anterior".
        """
        # Crear directorio padre si no existe
        ruta_video.parent.mkdir(parents=True, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        escritor_video: Optional[cv2.VideoWriter] = None
        resultado_bucle = "exito"

        try:
            escritor_video = cv2.VideoWriter(
                str(ruta_video), fourcc, VIDEO_FPS,
                (VIDEO_ANCHO, VIDEO_ALTO),
            )

            if not escritor_video.isOpened():
                logger.error(
                    "No se pudo crear el archivo de video: %s", ruta_video
                )
                self._registrar_error(nombre_sena, numero_repeticion, ruta_video)
                return "error"

            resultado_bucle = self._bucle_grabacion(
                escritor_video, nombre_sena, ruta_video,
                indice_sena, total_senas,
                numero_repeticion, total_repeticiones,
                imagen_referencia,
            )

        except (IOError, OSError, cv2.error) as error:
            logger.error("Error durante la grabación: %s", error)
            self._registrar_error(nombre_sena, numero_repeticion, ruta_video)
            resultado_bucle = "error"

        finally:
            if escritor_video is not None:
                escritor_video.release()

        # Si no hubo éxito, eliminamos el archivo parcial si existe
        if resultado_bucle in ("repetir_anterior", "salir", "error"):
            if ruta_video.exists():
                logger.info(f"Eliminando video parcial por estado '{resultado_bucle}': {ruta_video}")
                try:
                    ruta_video.unlink()
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el video parcial: {e}")

        return resultado_bucle

    def _bucle_grabacion(
        self,
        escritor_video: cv2.VideoWriter,
        nombre_sena: str,
        ruta_video: Path,
        indice_sena: int,
        total_senas: int,
        numero_repeticion: int,
        total_repeticiones: int,
        imagen_referencia: Optional[np.ndarray] = None,
    ) -> str:
        """Bucle principal de captura de frames durante la grabación.

        Args:
            escritor_video: Writer de video OpenCV.
            nombre_sena: Nombre de la seña.
            ruta_video: Ruta del video.
            indice_sena: Índice de la seña.
            total_senas: Total de señas.
            numero_repeticion: Repetición actual.
            total_repeticiones: Total de repeticiones.
            imagen_referencia: Imagen de referencia (opcional).

        Returns:
            "exito", "salir" o "repetir_anterior"
        """
        frames_grabados = 0
        frames_con_manos = 0
        tiempo_inicio = time.time()

        while True:
            tiempo_transcurrido = time.time() - tiempo_inicio
            if tiempo_transcurrido >= DURACION_GRABACION_SEGUNDOS:
                break

            exito, frame = self.camara.leer_frame()
            if not exito or frame is None:
                continue

            # Detectar manos con MediaPipe
            resultado = self.detector.detectar(frame)

            if resultado.hay_deteccion:
                frames_con_manos += 1

            # Escribir el frame ORIGINAL (sin overlay) al video
            escritor_video.write(frame)
            frames_grabados += 1

            # Calcular progreso
            progreso = tiempo_transcurrido / DURACION_GRABACION_SEGUNDOS

            # Dibujar UI sobre el frame con keypoints
            frame_ui = dibujar_pantalla_grabacion(
                resultado.frame_anotado, nombre_sena,
                progreso, frames_grabados,
                resultado.hay_deteccion,
                indice_sena, total_senas,
                numero_repeticion, total_repeticiones,
                imagen_referencia,
            )

            cv2.imshow(NOMBRE_VENTANA, frame_ui)

            accion, tiempo_pausado = self._procesar_teclas()
            if tiempo_pausado > 0:
                tiempo_inicio += tiempo_pausado

            if accion == "salir":
                return "salir"
            elif accion == "repetir_anterior":
                return "repetir_anterior"

        # Calcular duración real y tasa de detección
        duracion_real = time.time() - tiempo_inicio
        tasa_deteccion = (
            (frames_con_manos / frames_grabados * 100)
            if frames_grabados > 0
            else 0.0
        )

        # Registrar en CSV
        self.logger_sesion.registrar_grabacion(
            nombre_participante=self.configuracion.nombre_participante,
            nombre_sena=nombre_sena,
            numero_repeticion=numero_repeticion,
            ruta_video=str(ruta_video),
            duracion_segundos=duracion_real,
            cuadros_totales=frames_grabados,
            tasa_deteccion_mediapipe=tasa_deteccion,
            cuadros_con_manos_detectadas=frames_con_manos,
            estado="completado",
        )

        self.estadisticas.total_videos += 1
        logger.info(
            "Video guardado: %s (frames: %d, detección: %.1f%%)",
            ruta_video, frames_grabados, tasa_deteccion,
        )

        return "exito"

    def _fase_pausa_entre_senas(self) -> str:
        """Ejecuta la pausa automática entre señas.

        Returns:
            "continuar", "salir" o "repetir_anterior".
        """
        tiempo_inicio = time.time()

        while True:
            tiempo_transcurrido = time.time() - tiempo_inicio
            if tiempo_transcurrido >= PAUSA_ENTRE_SENAS_SEGUNDOS:
                break

            segundos_restantes = max(
                0,
                PAUSA_ENTRE_SENAS_SEGUNDOS - int(tiempo_transcurrido),
            )

            exito, frame = self.camara.leer_frame()
            if not exito or frame is None:
                continue

            frame_ui = dibujar_pantalla_pausa_entre_senas(
                frame, segundos_restantes,
            )
            cv2.imshow(NOMBRE_VENTANA, frame_ui)

            accion, tiempo_pausado = self._procesar_teclas()
            if tiempo_pausado > 0:
                tiempo_inicio += tiempo_pausado
                
            if accion == "salir":
                return "salir"
            if accion == "repetir_anterior":
                return "repetir_anterior"

        return "continuar"

    def _procesar_teclas(self) -> tuple[str, float]:
        """Procesa las teclas presionadas por el usuario.

        Returns:
            Tupla (accion, tiempo_pausado_segundos) donde accion es
            "continuar", "salir" o "repetir_anterior".
        """
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == TECLA_SALIR:
            logger.info("Usuario solicitó salir (tecla Q).")
            self._solicitar_salida = True
            return "salir", 0.0

        if tecla == TECLA_REPETIR:
            logger.info(
                "Usuario solicitó repetir la toma anterior (tecla R)."
            )
            return "repetir_anterior", 0.0

        if tecla in (TECLA_PAUSA, TECLA_PAUSA_MANUAL, TECLA_ESPACIO):
            tiempo_pausado = self._gestionar_pausa(tecla)
            if self._solicitar_salida:
                return "salir", tiempo_pausado
            return "continuar", tiempo_pausado

        return "continuar", 0.0

    def _gestionar_pausa(self, tecla_activacion: int) -> float:
        """Gestiona el estado de pausa de la sesión y congela timers.
        
        Args:
            tecla_activacion: La tecla que disparó la pausa.
            
        Returns:
            Tiempo total que la sesión estuvo en pausa (segundos).
        """
        logger.info("Sesión en pausa.")
        tiempo_pausa_inicio = time.time()

        while True:
            exito, frame = self.camara.leer_frame()
            if not exito or frame is None:
                frame = np.zeros(
                    (VIDEO_ALTO, VIDEO_ANCHO, 3), dtype=np.uint8
                )

            if tecla_activacion == TECLA_PAUSA:
                frame_pausa = dibujar_pantalla_pausa(frame)
            else:
                frame_pausa = dibujar_pantalla_pausa_manual(frame)
                
            cv2.imshow(NOMBRE_VENTANA, frame_pausa)

            tecla = cv2.waitKey(100) & 0xFF

            # Para reanudar:
            # - Si fue con ESC, se reanuda con ESC
            # - Si fue con P o Espacio, se reanuda con P o Espacio
            if tecla_activacion == TECLA_PAUSA and tecla == TECLA_PAUSA:
                logger.info("Sesión reanudada (ESC).")
                break
            elif tecla_activacion in (TECLA_PAUSA_MANUAL, TECLA_ESPACIO) and tecla in (TECLA_PAUSA_MANUAL, TECLA_ESPACIO):
                logger.info("Sesión reanudada (Manual).")
                break

            if tecla == TECLA_SALIR:
                logger.info("Usuario solicitó salir desde pausa.")
                self._solicitar_salida = True
                break
                
        return time.time() - tiempo_pausa_inicio

    def _registrar_error(
        self, nombre_sena: str, numero_repeticion: int, ruta_video: Path
    ) -> None:
        """Registra un error de grabación en el CSV.

        Args:
            nombre_sena: Nombre de la seña.
            numero_repeticion: Repetición actual.
            ruta_video: Ruta del video fallido.
        """
        self.logger_sesion.registrar_grabacion(
            nombre_participante=self.configuracion.nombre_participante,
            nombre_sena=nombre_sena,
            numero_repeticion=numero_repeticion,
            ruta_video=str(ruta_video),
            duracion_segundos=0.0,
            cuadros_totales=0,
            tasa_deteccion_mediapipe=0.0,
            cuadros_con_manos_detectadas=0,
            estado="error",
        )

    def _mostrar_resumen(self, total_senas: int) -> None:
        """Muestra la pantalla de resumen final.

        Args:
            total_senas: Total de señas planificadas.
        """
        logger.info("=" * 50)
        logger.info("RESUMEN DE SESIÓN")
        logger.info("=" * 50)
        logger.info(
            "Videos grabados: %d", self.estadisticas.total_videos
        )
        logger.info(
            "Tiempo total: %.0f segundos",
            self.estadisticas.tiempo_total,
        )
        logger.info(
            "Señas completadas: %d de %d",
            len(self.estadisticas.senas_completadas), total_senas,
        )
        logger.info(
            "Carpetas creadas: %d",
            len(self.estadisticas.carpetas_creadas),
        )
        logger.info("=" * 50)

        # Mostrar pantalla de resumen visual
        exito, frame = self.camara.leer_frame()
        if not exito or frame is None:
            frame = np.zeros(
                (VIDEO_ALTO, VIDEO_ANCHO, 3), dtype=np.uint8
            )

        frame_resumen = dibujar_pantalla_resumen(
            frame,
            self.estadisticas.total_videos,
            self.estadisticas.tiempo_total,
            len(self.estadisticas.senas_completadas),
            total_senas,
            len(self.estadisticas.carpetas_creadas),
        )

        cv2.imshow(NOMBRE_VENTANA, frame_resumen)
        cv2.waitKey(0)


def crear_sesion_grabacion(
    configuracion: ConfiguracionSesion,
    camara: Camara,
    detector: DetectorMediaPipe,
    logger_sesion: RegistradorSesion,
) -> GrabadorSesion:
    """Factory: crea una instancia de GrabadorSesion configurada.

    Args:
        configuracion: Configuración de la sesión.
        camara: Cámara abierta.
        detector: Detector de MediaPipe.
        logger_sesion: Logger CSV.

    Returns:
        Instancia de GrabadorSesion lista para ejecutar.
    """
    return GrabadorSesion(
        configuracion=configuracion,
        camara=camara,
        detector=detector,
        logger_sesion=logger_sesion,
    )
