"""
Configuración centralizada del sistema de grabación LSEC.

Todas las constantes y parámetros del sistema se definen aquí.
CERO magic numbers en el resto del código.
"""

import cv2
from dataclasses import dataclass, field
from pathlib import Path


# ═══════════════════════════════════════
# CONFIGURACIÓN DE GRABACIÓN
# ═══════════════════════════════════════

DURACION_GRABACION_SEGUNDOS: int = 3
CUENTA_REGRESIVA_PREPARACION_SEGUNDOS: int = 5
PAUSA_ENTRE_SENAS_SEGUNDOS: int = 2
REPETICIONES_POR_SENA: int = 30

# ═══════════════════════════════════════
# CONFIGURACIÓN DE VIDEO
# ═══════════════════════════════════════

VIDEO_FPS: int = 30
VIDEO_ANCHO: int = 640
VIDEO_ALTO: int = 480
VIDEO_CODEC: str = "mp4v"
VIDEO_EXTENSION: str = ".mp4"

# ═══════════════════════════════════════
# RUTAS Y ARCHIVOS
# ═══════════════════════════════════════

DIRECTORIO_RAIZ_DATASET: str = "dataset"
ARCHIVO_LISTA_SENAS: str = "lista_senas.txt"
ARCHIVO_LOG_SESION: str = "session_log.csv"
DIRECTORIO_REFERENCIAS: str = "referencias"

# ═══════════════════════════════════════
# CONFIGURACIÓN DE REFERENCIAS
# ═══════════════════════════════════════

TAMANO_REFERENCIA: tuple = (150, 150)

# ═══════════════════════════════════════
# CONFIGURACIÓN DE CÁMARA
# ═══════════════════════════════════════

INDICE_CAMARA: int = 0

# ═══════════════════════════════════════
# CONFIGURACIÓN DE MEDIAPIPE
# ═══════════════════════════════════════

MEDIAPIPE_CONFIANZA_DETECCION_MINIMA: float = 0.7
MEDIAPIPE_CONFIANZA_SEGUIMIENTO_MINIMA: float = 0.5
NUMERO_MAXIMO_MANOS: int = 2

# ═══════════════════════════════════════
# CONFIGURACIÓN DE INTERFAZ (UI)
# ═══════════════════════════════════════

FUENTE = cv2.FONT_HERSHEY_SIMPLEX
FUENTE_NEGRITA = cv2.FONT_HERSHEY_DUPLEX

# Colores en formato BGR (OpenCV)
COLOR_EXITO: tuple = (0, 255, 0)       # Verde
COLOR_ADVERTENCIA: tuple = (0, 165, 255)  # Naranja
COLOR_ERROR: tuple = (0, 0, 255)       # Rojo
COLOR_INFO: tuple = (255, 255, 255)    # Blanco
COLOR_FONDO: tuple = (40, 40, 40)      # Gris oscuro
COLOR_BARRA_PROGRESO: tuple = (0, 200, 255)  # Amarillo-naranja
COLOR_BARRA_FONDO: tuple = (80, 80, 80)     # Gris
COLOR_GRABANDO: tuple = (0, 0, 255)    # Rojo para indicador de grabación
COLOR_PAUSA: tuple = (255, 200, 0)     # Azul claro para pausa

# Tamaños de fuente
TAMANO_FUENTE_TITULO: float = 2.0
TAMANO_FUENTE_SUBTITULO: float = 1.0
TAMANO_FUENTE_INFO: float = 0.6
TAMANO_FUENTE_INDICADOR: float = 0.7

# Grosor de línea
GROSOR_TITULO: int = 3
GROSOR_SUBTITULO: int = 2
GROSOR_INFO: int = 1
GROSOR_INDICADOR: int = 2

# Barra de progreso
BARRA_ALTO: int = 25
BARRA_MARGEN_INFERIOR: int = 40
BARRA_MARGEN_LATERAL: int = 30

# Overlay semitransparente
OVERLAY_OPACIDAD: float = 0.6

# ═══════════════════════════════════════
# NOMBRE DE VENTANA
# ═══════════════════════════════════════

NOMBRE_VENTANA: str = "Grabador LSEC - Dataset Lengua de Senas Ecuatoriana"

# ═══════════════════════════════════════
# TECLAS DE CONTROL
# ═══════════════════════════════════════

TECLA_SALIR: int = ord('q')
TECLA_PAUSA: int = 27  # ESC
TECLA_PAUSA_MANUAL: int = ord('p')
TECLA_REPETIR: int = ord('r')
TECLA_ESPACIO: int = 32


@dataclass
class ConfiguracionSesion:
    """Configuración específica de una sesión de grabación.

    Attributes:
        nombre_participante: Nombre del participante (sin espacios).
        lista_senas: Lista de señas a grabar.
        repeticiones_por_sena: Número de repeticiones a realizar por cada seña.
        repeticion_inicio: Número de repetición desde la cual iniciar.
        sena_inicio: Índice de la seña desde la cual iniciar.
    """

    nombre_participante: str = ""
    lista_senas: list[str] = field(default_factory=list)
    repeticiones_por_sena: int = REPETICIONES_POR_SENA
    repeticion_inicio: int = 1
    sena_inicio: int = 0

    def ruta_dataset(self) -> Path:
        """Retorna la ruta raíz del dataset."""
        return Path(DIRECTORIO_RAIZ_DATASET)

    def ruta_video(self, nombre_sena: str, numero_repeticion: int) -> Path:
        """Genera la ruta completa para un archivo de video.

        Args:
            nombre_sena: Nombre de la seña.
            numero_repeticion: Número de repetición.

        Returns:
            Ruta completa del archivo de video.
        """
        nombre_archivo = (
            f"{self.nombre_participante}_rep{numero_repeticion:02d}"
            f"{VIDEO_EXTENSION}"
        )
        return self.ruta_dataset() / nombre_sena / nombre_archivo
