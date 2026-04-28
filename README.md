# Grabador LSEC - Dataset de Lengua de Señas Ecuatoriana

Sistema de grabación automática de señas para construir un dataset de **Lengua de Señas Ecuatoriana (LSEC)**.

> **Tesis:** "Prototipo de Asistencia Digital Bidireccional con Reconocimiento de Gestos y Avatar Signante para la Orientación de Personas Sordas en Entornos de Atención al Cliente" — ESPE 2026.

---

## Requisitos del Sistema

- **Sistema Operativo:** Windows 10/11
- **Python:** 3.10 o superior
- **Cámara:** Webcam USB o integrada
- **RAM:** Mínimo 4 GB (recomendado 8 GB)
- **Espacio en disco:** ~5 GB para el dataset completo (100 señas × 30 repeticiones)

---

## Instalación Paso a Paso

### 1. Clonar o descargar el proyecto

Coloque la carpeta `grabador_lsec` en la ubicación deseada.

### 2. Crear entorno virtual

Abra una terminal (PowerShell o CMD) y navegue a la carpeta del proyecto:

```powershell
cd grabador_lsec
python -m venv venv
```

### 3. Activar el entorno virtual

```powershell
venv\Scripts\activate
```

> **Nota:** Si recibe un error de permisos, ejecute primero:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Instalar dependencias

```powershell
pip install -r requirements.txt
```

---

## Cómo Preparar `lista_senas.txt`

El archivo `lista_senas.txt` contiene la lista de señas a grabar, **una seña por línea**.

### Formato

```
hola
gracias
por_favor
buenos_dias
```

### Reglas

- Una seña por línea
- Sin líneas vacías (se ignoran automáticamente)
- Los espacios se reemplazan por guiones bajos (`_`)
- Se convierten a minúsculas automáticamente
- Ya se incluye un archivo con **100 señas** predefinidas

---

## Cómo Ejecutar

```powershell
cd grabador_lsec
venv\Scripts\activate
python main.py
```

### Flujo de Ejecución

1. **Verificación de cámara:** El sistema comprueba que la cámara esté disponible
2. **Carga de señas:** Lee `lista_senas.txt` y valida el contenido
3. **Registro de participante:** Solicita el nombre (sin espacios)
4. **Detección de sesión previa:** Si hay grabaciones previas, ofrece continuar
5. **Inicio de grabación:** Sigue el flujo automático seña por seña

### Controles Durante la Grabación

| Tecla | Acción |
|-------|--------|
| `ESC` | Pausar / Reanudar la grabación |
| `Q`   | Salir del programa (guarda todo el progreso) |

---

## Estructura de Carpetas del Dataset Generado

```
grabador_lsec/
├── dataset/
│   ├── hola/
│   │   ├── christian_rep01.mp4
│   │   ├── christian_rep02.mp4
│   │   ├── ...
│   │   └── christian_rep30.mp4
│   ├── gracias/
│   │   ├── christian_rep01.mp4
│   │   └── ...
│   ├── por_favor/
│   │   └── ...
│   └── ... (100 carpetas, una por seña)
├── session_log.csv          # Registro de toda la sesión
├── grabador_lsec.log        # Log técnico del sistema
└── ...
```

### Formato del CSV de Sesión

El archivo `session_log.csv` contiene:

| Columna | Descripción |
|---------|-------------|
| `timestamp` | Fecha y hora de la grabación |
| `nombre_participante` | Nombre del participante |
| `nombre_sena` | Nombre de la seña grabada |
| `numero_repeticion` | Número de repetición (1-30) |
| `ruta_video` | Ruta del archivo de video |
| `duracion_segundos` | Duración real de la grabación |
| `total_frames` | Cantidad de frames capturados |
| `tasa_deteccion_mediapipe` | % de frames con manos detectadas |
| `frames_manos_detectadas` | Frames donde se detectaron manos |
| `estado` | completado / saltado / error |

---

## Qué Hacer si la Cámara No Se Detecta

1. **Verifique la conexión:** Asegúrese de que la cámara esté conectada
2. **Cierre otras aplicaciones:** Teams, Zoom, Skype u otras apps que usen la cámara
3. **Pruebe con otro índice:** Edite `INDICE_CAMARA` en `config.py` (pruebe con 1, 2, etc.)
4. **Verifique drivers:** Abra la app "Cámara" de Windows para verificar que funciona
5. **Reinicie:** Desconecte y reconecte la cámara, luego reinicie el programa

### Verificar la cámara manualmente

```python
import cv2
cap = cv2.VideoCapture(0)  # Cambie 0 por 1, 2, etc.
print("Cámara disponible:", cap.isOpened())
cap.release()
```

---

## Cómo Retomar una Sesión Interrumpida

El sistema **detecta automáticamente** sesiones previas:

1. Ejecute `python main.py` normalmente
2. Ingrese el **mismo nombre** del participante
3. El sistema escaneará las carpetas del dataset
4. Encontrará los videos existentes y determinará dónde continuar
5. Mostrará un mensaje como:
   ```
   Sesión previa detectada.
   Videos existentes: 450
   Retomando desde: seña 'agua', repetición 16
   ```

### Importante

- Use **exactamente el mismo nombre** de participante
- No modifique los nombres de los archivos de video
- No elimine archivos de la carpeta `dataset/`
- El archivo `session_log.csv` se mantiene con registros acumulados

---

## Interfaz Visual

### Pantalla de Preparación
- Fondo semitransparente sobre imagen de cámara
- Nombre de la seña en MAYÚSCULAS al centro
- Cuenta regresiva de 5 segundos
- Indicadores de progreso (seña actual, repetición, barra general)

### Pantalla de Grabación
- Imagen de cámara EN VIVO
- Keypoints de MediaPipe dibujados en tiempo real (21 puntos por mano)
- Indicador rojo "GRABANDO"
- Barra de progreso de grabación (0 → 3 segundos)
- Estado de detección de manos (verde = detectadas, naranja = sin detección)

### Pantalla de Resumen
- Total de videos grabados
- Tiempo total de sesión
- Señas completadas
- Instrucciones para continuar

---

## Configuración Avanzada

Todos los parámetros se encuentran en `config.py`:

| Parámetro | Valor por defecto | Descripción |
|-----------|-------------------|-------------|
| `DURACION_GRABACION_SEGUNDOS` | 3 | Duración de cada video |
| `CUENTA_REGRESIVA_PREPARACION_SEGUNDOS` | 5 | Cuenta regresiva antes de grabar |
| `PAUSA_ENTRE_SENAS_SEGUNDOS` | 2 | Pausa entre grabaciones |
| `REPETICIONES_POR_SENA` | 30 | Repeticiones por cada seña |
| `VIDEO_FPS` | 30 | Frames por segundo |
| `VIDEO_ANCHO` | 640 | Ancho del video en pixeles |
| `VIDEO_ALTO` | 480 | Alto del video en pixeles |
| `INDICE_CAMARA` | 0 | Índice de la cámara |
| `MEDIAPIPE_CONFIANZA_DETECCION_MINIMA` | 0.7 | Confianza mínima de detección |

---

## Distribución para Usuarios Finales

El programa puede empaquetarse como un ejecutable Windows que **no requiere Python instalado**.

### Generar el Ejecutable

1. Asegúrese de tener el entorno virtual configurado con las dependencias instaladas
2. Ejecute el script de build:

```powershell
.\build.bat
```

3. El ejecutable se generará en `dist\GrabadorLSEC\`

### Distribución Portátil (Carpeta)

Copie la carpeta completa `dist\GrabadorLSEC\` a la máquina destino. El usuario solo necesita ejecutar `GrabadorLSEC.exe`.

Contenido de la carpeta distribuible:

```
GrabadorLSEC/
├── GrabadorLSEC.exe          # Ejecutable principal
├── lista_senas.txt           # Editable: lista de señas
├── referencias/              # Editable: imágenes de referencia
├── _internal/                # Dependencias (NO modificar)
└── ...                       # Otros archivos de PyInstaller
```

### Crear Instalador Windows (Opcional)

Para generar un instalador `setup.exe` profesional:

1. Instale [Inno Setup 6+](https://jrsoftware.org/isinfo.php)
2. Abra `installer\setup.iss` en Inno Setup
3. Presione **Compile** (Ctrl+F9)
4. El instalador se generará en `installer\Output\`

El instalador incluye:
- Acceso directo en el escritorio y menú inicio
- Desinstalador automático
- Soporte para español e inglés

### Archivos Editables por el Usuario

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `lista_senas.txt` | Junto al `.exe` | Agregar/quitar señas (una por línea) |
| `referencias/` | Junto al `.exe` | Imágenes PNG/JPG de referencia visual |

---

## Estructura del Proyecto (Desarrolladores)

```
grabador_lsec/
├── main.py                    # Punto de entrada
├── config.py                  # Configuración centralizada
├── requirements.txt           # Dependencias Python
├── grabador_lsec.spec         # Config de PyInstaller
├── build.bat                  # Script de build automatizado
├── lista_senas.txt            # 100 señas predefinidas
├── recorder/                  # Módulos de grabación
│   ├── camera.py              # Abstracción de cámara
│   ├── mediapipe_detector.py  # Detector de manos
│   └── session_recorder.py    # Orquestador de sesión
├── ui/
│   └── overlay.py             # Interfaz visual OpenCV
├── utils/
│   ├── paths.py               # Resolución de rutas (PyInstaller)
│   └── validators.py          # Validaciones de entrada
├── data/
│   └── session_log.py         # Logger CSV de sesión
├── referencias/               # Imágenes de referencia (~97 PNG)
└── installer/
    └── setup.iss              # Script de Inno Setup
```

---

## Licencia

Proyecto académico — ESPE 2026. Uso exclusivo para fines de investigación.

