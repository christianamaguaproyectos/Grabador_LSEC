"""Registrador de sesion CSV para el sistema de grabacion LSEC.

Registra metadatos de cada video capturado durante una sesion de grabacion.
Diseñado para ser resiliente: vacia el bufer despues de cada escritura para que
los datos se preserven incluso si el programa termina abruptamente.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import ARCHIVO_LOG_SESION

logger = logging.getLogger(__name__)

# Definiciones de columnas para el CSV de la sesion
COLUMNAS_CSV: list[str] = [
    "timestamp",
    "nombre_participante",
    "nombre_sena",
    "numero_repeticion",
    "ruta_video",
    "duracion_segundos",
    "cuadros_totales",
    "tasa_deteccion_mediapipe",
    "cuadros_con_manos_detectadas",
    "estado",
]


class RegistradorSesion:
    """Gestiona el archivo de log CSV de la sesion.

    Escribe una fila por intento de grabacion con metadatos sobre la captura.
    Utiliza el vaciado inmediato para evitar la perdida de datos en caso de una terminacion inesperada.

    Atributos:
        ruta_log: Ruta al archivo de log CSV.
        _archivo: Manejador de archivo abierto para el CSV.
        _escritor: Instancia de DictWriter de CSV.
        _conteo_filas: Numero de filas escritas en esta sesion.
    """

    def __init__(self, ruta_log = ARCHIVO_LOG_SESION) -> None:
        """Inicializa el registrador de sesion.

        Args:
            ruta_log: Ruta al archivo de log CSV (Path o str).
        """
        self.ruta_log: Path = Path(ruta_log)
        self._archivo: Optional[object] = None
        self._escritor: Optional[csv.DictWriter] = None
        self._conteo_filas: int = 0

    def __enter__(self) -> "RegistradorSesion":
        """Abre el archivo CSV para escritura (entrada del gestor de contexto)."""
        self._abrir()
        return self

    def __exit__(self, tipo_exc, valor_exc, traza_exc) -> None:
        """Cierra el archivo CSV (salida del gestor de contexto)."""
        self.cerrar()

    def _abrir(self) -> None:
        """Abre el archivo CSV, creandolo con encabezados si no existe."""
        existe_archivo = self.ruta_log.exists() and self.ruta_log.stat().st_size > 0

        # Abrir en modo de adicion para no sobrescribir sesiones anteriores
        self._archivo = open(
            self.ruta_log, mode="a", newline="", encoding="utf-8"
        )
        self._escritor = csv.DictWriter(self._archivo, fieldnames=COLUMNAS_CSV)

        if not existe_archivo:
            self._escritor.writeheader()
            self._archivo.flush()
            logger.info("Creado nuevo archivo de log: %s", self.ruta_log)
        else:
            logger.info(
                "Anexando al archivo de log existente: %s", self.ruta_log
            )

    def registrar_grabacion(
        self,
        nombre_participante: str,
        nombre_sena: str,
        numero_repeticion: int,
        ruta_video: str,
        duracion_segundos: float,
        cuadros_totales: int,
        tasa_deteccion_mediapipe: float,
        cuadros_con_manos_detectadas: int,
        estado: str = "completado",
    ) -> None:
        """Registra una entrada de grabacion unica en el CSV.

        Args:
            nombre_participante: Nombre del participante.
            nombre_sena: Nombre de la sena que se esta grabando.
            numero_repeticion: Numero de repeticion actual.
            ruta_video: Ruta relativa al archivo de video guardado.
            duracion_segundos: Duracion real de la grabacion en segundos.
            cuadros_totales: Numero total de cuadros capturados.
            tasa_deteccion_mediapipe: Porcentaje de cuadros con deteccion de manos (0-100).
            cuadros_con_manos_detectadas: Numero de cuadros donde se detectaron manos.
            estado: Estado de la grabacion (completado/omitido/error).
        """
        if self._escritor is None:
            logger.error("RegistradorSesion no esta abierto. Llama a _abrir() primero.")
            return

        fila = {
            "timestamp": datetime.now().isoformat(),
            "nombre_participante": nombre_participante,
            "nombre_sena": nombre_sena,
            "numero_repeticion": numero_repeticion,
            "ruta_video": ruta_video,
            "duracion_segundos": round(duracion_segundos, 3),
            "cuadros_totales": cuadros_totales,
            "tasa_deteccion_mediapipe": round(tasa_deteccion_mediapipe, 2),
            "cuadros_con_manos_detectadas": cuadros_con_manos_detectadas,
            "estado": estado,
        }

        self._escritor.writerow(fila)
        # Flush inmediato para preservar datos ante una terminacion abrupta
        self._archivo.flush()
        self._conteo_filas += 1

        logger.debug(
            "Registrado: %s / %s rep%d [%s]",
            nombre_sena,
            nombre_participante,
            numero_repeticion,
            estado,
        )

    def obtener_conteo_filas(self) -> int:
        """Devuelve el numero de filas escritas en esta sesion.

        Returns:
            Numero de filas escritas desde que se abrio el registrador.
        """
        return self._conteo_filas

    def cerrar(self) -> None:
        """Cierra el manejador de archivo CSV de forma segura."""
        if self._archivo is not None:
            try:
                self._archivo.flush()
                self._archivo.close()
                logger.info(
                    "Log de sesion cerrado. %d registros escritos.", self._conteo_filas
                )
            except (IOError, OSError) as e:
                logger.error("Error al cerrar el archivo de log: %s", e)
            finally:
                self._archivo = None
                self._escritor = None
