"""
Punto de entrada principal del Grabador LSEC.

Sistema de grabación automática de señas para construir un dataset
de Lengua de Señas Ecuatoriana (LSEC).

Tesis: "Prototipo de Asistencia Digital Bidireccional con Reconocimiento
de Gestos y Avatar Signante para la Orientación de Personas Sordas en
Entornos de Atención al Cliente" - ESPE 2026.

Uso:
    python main.py
"""

import logging
import signal
import sys
from pathlib import Path

import cv2

from config import (
    ARCHIVO_LISTA_SENAS,
    ARCHIVO_LOG_SESION,
    DIRECTORIO_RAIZ_DATASET,
    NOMBRE_VENTANA,
    REPETICIONES_POR_SENA,
    ConfiguracionSesion,
)
from utils.validators import (
    validar_camara,
    validar_nombre_participante,
    cargar_lista_senas,
    validar_directorio_dataset,
)
from recorder.camera import Camara
from recorder.mediapipe_detector import DetectorMediaPipe
from recorder.session_recorder import crear_sesion_grabacion
from data.session_log import RegistradorSesion


def configurar_logging() -> None:
    """Configura el sistema de logging con formato y nivel apropiados."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                "grabador_lsec.log", encoding="utf-8", mode="a"
            ),
        ],
    )


def mostrar_banner() -> None:
    """Muestra el banner de bienvenida del sistema."""
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║        GRABADOR LSEC - Dataset de Señas              ║
    ║        Lengua de Señas Ecuatoriana                    ║
    ║                                                      ║
    ║        ESPE 2026 - Tesis de Grado                    ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def solicitar_nombre_participante() -> str:
    """Solicita y valida el nombre del participante por consola.

    Returns:
        Nombre del participante validado.
    """
    while True:
        nombre = input(
            "\n  Ingrese el nombre del participante (sin espacios): "
        ).strip()

        es_valido, mensaje_error = validar_nombre_participante(nombre)

        if es_valido:
            print(f"  Participante registrado: {nombre}")
            return nombre

        print(f"  Error: {mensaje_error}")
        print("  Intente de nuevo.\n")


def solicitar_repeticiones_por_sena(valor_defecto: int) -> int:
    """Solicita la cantidad de repeticiones por seña para esta sesión.

    Args:
        valor_defecto: Repeticiones por defecto.

    Returns:
        Número de repeticiones por seña elegido por el usuario.
    """
    print("\n  Configuración de repeticiones")
    while True:
        entrada = input(
            f"  Repeticiones por seña [{valor_defecto}]: "
        ).strip()

        if not entrada:
            return valor_defecto

        if entrada.isdigit() and int(entrada) > 0:
            return int(entrada)

        print("  Error: Ingrese un número entero mayor que cero.")


def mostrar_senas_disponibles(lista_senas: list[str]) -> None:
    """Muestra el listado completo de señas con índices base 1."""
    print("\n  Lista de señas disponibles:")
    for indice, sena in enumerate(lista_senas, start=1):
        print(f"    {indice:>3}. {sena}")


def solicitar_senas_a_grabar(lista_senas: list[str]) -> list[str]:
    """Permite elegir qué señas grabar en la sesión.

    Opciones:
        1) Todas las señas.
        2) Un rango por índice (ej: 10-20).
        3) Selección puntual por índices o nombres separados por coma.

    Args:
        lista_senas: Lista completa de señas disponibles.

    Returns:
        Lista de señas seleccionadas para grabar.
    """
    total = len(lista_senas)
    mapa_senas = {sena: sena for sena in lista_senas}

    print("\n  Selección de señas")
    print(f"  Total disponibles: {total}")

    ver_lista = input(
        "  ¿Desea ver todas las señas con índice? [s/N]: "
    ).strip().lower()
    if ver_lista == "s":
        mostrar_senas_disponibles(lista_senas)

    while True:
        print("\n  Elija qué señas grabar:")
        print("    1) Todas")
        print("    2) Rango por índice (ej: 10-25)")
        print("    3) Selección puntual (ej: 1,4,9 o hola,gracias)")
        opcion = input("  Opción [1]: ").strip() or "1"

        if opcion == "1":
            return lista_senas

        if opcion == "2":
            entrada = input("  Ingrese rango inicio-fin: ").strip()
            if "-" not in entrada:
                print("  Error: Formato inválido. Use inicio-fin.")
                continue

            try:
                inicio_txt, fin_txt = entrada.split("-", 1)
                inicio = int(inicio_txt.strip())
                fin = int(fin_txt.strip())
            except ValueError:
                print("  Error: El rango debe contener números válidos.")
                continue

            if inicio < 1 or fin < 1 or inicio > fin or fin > total:
                print(
                    f"  Error: Use un rango entre 1 y {total}, con inicio <= fin."
                )
                continue

            return lista_senas[inicio - 1:fin]

        if opcion == "3":
            entrada = input(
                "  Ingrese índices o nombres separados por coma: "
            ).strip()
            partes = [parte.strip().lower() for parte in entrada.split(",")]
            partes = [parte for parte in partes if parte]

            if not partes:
                print("  Error: Debe ingresar al menos una seña.")
                continue

            seleccion: list[str] = []
            vistos: set[str] = set()

            if all(parte.isdigit() for parte in partes):
                indices = [int(parte) for parte in partes]
                fuera_de_rango = [i for i in indices if i < 1 or i > total]
                if fuera_de_rango:
                    print(
                        f"  Error: Hay índices fuera de rango (1 a {total})."
                    )
                    continue

                for indice in indices:
                    sena = lista_senas[indice - 1]
                    if sena not in vistos:
                        vistos.add(sena)
                        seleccion.append(sena)
                return seleccion

            no_encontradas = [sena for sena in partes if sena not in mapa_senas]
            if no_encontradas:
                print(
                    "  Error: Señas no encontradas: "
                    + ", ".join(no_encontradas)
                )
                continue

            for sena in partes:
                if sena not in vistos:
                    vistos.add(sena)
                    seleccion.append(mapa_senas[sena])
            return seleccion

        print("  Error: Opción inválida. Use 1, 2 o 3.")


def detectar_sesion_previa(
    nombre_participante: str,
    lista_senas: list[str],
    repeticiones_por_sena: int,
) -> tuple[int, int]:
    """Detecta si existe una sesión previa para retomar.

    Analiza el archivo CSV de sesión para determinar dónde
    se quedó la grabación anterior.

    Args:
        nombre_participante: Nombre del participante.
        lista_senas: Lista completa de señas.
        repeticiones_por_sena: Repeticiones objetivo por cada seña.

    Returns:
        Tupla (indice_sena, numero_repeticion) desde donde continuar.
    """
    logger = logging.getLogger(__name__)
    ruta_log = Path(ARCHIVO_LOG_SESION)

    if not ruta_log.exists():
        return 0, 1

    # Revisar qué videos ya existen en el dataset
    videos_existentes: dict[str, set[int]] = {}

    for sena in lista_senas:
        ruta_carpeta = Path(DIRECTORIO_RAIZ_DATASET) / sena
        if ruta_carpeta.exists():
            for archivo in ruta_carpeta.glob(
                f"{nombre_participante}_rep*{'.mp4'}"
            ):
                nombre_archivo = archivo.stem
                try:
                    # Extraer número de repetición del nombre
                    parte_rep = nombre_archivo.split("_rep")[1]
                    num_rep = int(parte_rep)
                    if sena not in videos_existentes:
                        videos_existentes[sena] = set()
                    videos_existentes[sena].add(num_rep)
                except (IndexError, ValueError):
                    continue

    if not videos_existentes:
        return 0, 1

    # Encontrar el punto donde retomar

    for idx, sena in enumerate(lista_senas):
        reps = videos_existentes.get(sena, set())
        if len(reps) < repeticiones_por_sena:
            # Esta seña tiene repeticiones pendientes
            siguiente_rep = 1
            for r in range(1, repeticiones_por_sena + 1):
                if r not in reps:
                    siguiente_rep = r
                    break

            total_existentes = sum(
                len(reps) for reps in videos_existentes.values()
            )
            logger.info(
                "Sesión previa detectada. Videos existentes: %d. "
                "Retomando desde seña '%s' (índice %d), repetición %d.",
                total_existentes, sena, idx, siguiente_rep,
            )
            print(
                f"\n  Sesión previa detectada."
                f"\n  Videos existentes: {total_existentes}"
                f"\n  Retomando desde: seña '{sena}', repetición {siguiente_rep}"
            )
            return idx, siguiente_rep

    # Todas las señas están completas
    logger.info("Todas las señas ya fueron grabadas para '%s'.", nombre_participante)
    print(f"\n  Todas las señas ya están grabadas para '{nombre_participante}'.")
    return len(lista_senas), 1


def main() -> None:
    """Función principal del grabador LSEC."""
    configurar_logging()
    logger = logging.getLogger(__name__)

    # Manejador de señales para cierre limpio
    def manejador_senal(sig: int, frame: object) -> None:
        logger.info("Señal de interrupción recibida. Cerrando...")
        cv2.destroyAllWindows()
        sys.exit(0)

    signal.signal(signal.SIGINT, manejador_senal)

    mostrar_banner()

    # Paso 1: Verificar cámara
    print("  [1/4] Verificando cámara...")
    if not validar_camara():
        print("\n  ERROR: No se detectó ninguna cámara.")
        print("  Verifique que la cámara esté conectada y no esté")
        print("  siendo usada por otra aplicación.")
        sys.exit(1)
    print("  Cámara detectada correctamente.")

    # Paso 2: Cargar lista de señas
    print(f"\n  [2/4] Cargando lista de señas desde '{ARCHIVO_LISTA_SENAS}'...")
    try:
        lista_senas = cargar_lista_senas()
        print(f"  Se cargaron {len(lista_senas)} señas.")
    except FileNotFoundError as error:
        print(f"\n  ERROR: {error}")
        print(f"  Cree el archivo '{ARCHIVO_LISTA_SENAS}' con una seña por línea.")
        sys.exit(1)
    except ValueError as error:
        print(f"\n  ERROR: {error}")
        sys.exit(1)

    # Paso 3: Configuración personalizada
    print("\n  [3/5] Configuración de sesión")
    repeticiones_por_sena = solicitar_repeticiones_por_sena(
        REPETICIONES_POR_SENA
    )
    lista_senas_seleccionadas = solicitar_senas_a_grabar(lista_senas)
    print(
        "  Configuración aplicada: "
        f"{len(lista_senas_seleccionadas)} señas, "
        f"{repeticiones_por_sena} repeticiones por seña."
    )

    # Paso 4: Solicitar nombre del participante
    print("\n  [4/5] Registro de participante")
    nombre_participante = solicitar_nombre_participante()

    # Paso 5: Detectar sesión previa
    print("\n  [5/5] Verificando sesiones previas...")
    sena_inicio, rep_inicio = detectar_sesion_previa(
        nombre_participante,
        lista_senas_seleccionadas,
        repeticiones_por_sena,
    )

    if sena_inicio >= len(lista_senas_seleccionadas):
        print("\n  No hay grabaciones pendientes. ¡Sesión completa!")
        sys.exit(0)

    # Validar directorio del dataset
    validar_directorio_dataset(DIRECTORIO_RAIZ_DATASET)

    # Configurar sesión
    configuracion = ConfiguracionSesion(
        nombre_participante=nombre_participante,
        lista_senas=lista_senas_seleccionadas,
        repeticiones_por_sena=repeticiones_por_sena,
        repeticion_inicio=rep_inicio,
        sena_inicio=sena_inicio,
    )

    # Mostrar resumen antes de iniciar
    print("\n  " + "=" * 50)
    print(f"  Participante:     {nombre_participante}")
    print(f"  Total señas:      {len(lista_senas_seleccionadas)}")
    print(f"  Repeticiones:     {repeticiones_por_sena} por seña")
    print(f"  Inicio desde:     seña {sena_inicio + 1}, rep {rep_inicio}")
    print("  " + "=" * 50)
    print("\n  Controles:")
    print("    ESC  = Pausar/Reanudar")
    print("    R    = Repetir toma anterior")
    print("    Q    = Salir")
    print("\n  Presione ENTER para comenzar la grabación...")
    input()

    # Iniciar sesión de grabación con context managers
    try:
        with Camara() as camara, \
             DetectorMediaPipe() as detector, \
             RegistradorSesion() as logger_sesion:

            if not camara.esta_abierta():
                logger.error("No se pudo abrir la cámara.")
                print("  ERROR: No se pudo abrir la cámara.")
                sys.exit(1)

            sesion = crear_sesion_grabacion(
                configuracion, camara, detector, logger_sesion
            )

            sesion.ejecutar()

    except KeyboardInterrupt:
        logger.info("Interrupción del usuario (Ctrl+C).")
        print("\n\n  Sesión interrumpida por el usuario.")
    except Exception as error:
        logger.exception("Error inesperado: %s", error)
        print(f"\n  ERROR inesperado: {error}")
    finally:
        cv2.destroyAllWindows()
        print("\n  Grabador LSEC finalizado.")
        print("  Los datos se guardaron en el CSV de sesión.")


if __name__ == "__main__":
    main()
