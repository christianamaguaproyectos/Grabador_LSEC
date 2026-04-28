@echo off
REM ══════════════════════════════════════════════════════════
REM  Build Script - Grabador LSEC
REM  Genera el ejecutable distribuible con PyInstaller
REM ══════════════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║       BUILD - Grabador LSEC                     ║
echo  ║       Generando ejecutable distribuible...       ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ─── Verificar entorno virtual ────────────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo  ERROR: No se encontro el entorno virtual.
    echo  Ejecute primero:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    exit /b 1
)

REM ─── Activar entorno virtual ──────────────────────────────
echo  [1/5] Activando entorno virtual...
call venv\Scripts\activate.bat

REM ─── Instalar PyInstaller si no existe ────────────────────
echo  [2/5] Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo  ERROR: No se pudo instalar PyInstaller.
        exit /b 1
    )
)
echo  PyInstaller OK.

REM ─── Limpiar build anterior ───────────────────────────────
echo  [3/5] Limpiando build anterior...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM ─── Ejecutar PyInstaller ─────────────────────────────────
echo  [4/5] Ejecutando PyInstaller...
echo.
pyinstaller grabador_lsec.spec --noconfirm
echo.

if errorlevel 1 (
    echo  ERROR: PyInstaller fallo. Revise los errores arriba.
    exit /b 1
)

REM ─── Copiar recursos editables ────────────────────────────
echo  [5/5] Copiando recursos editables...

REM Copiar lista de señas
copy /y "lista_senas.txt" "dist\GrabadorLSEC\" >nul
echo  - lista_senas.txt copiado

REM Copiar carpeta de referencias
if exist "referencias" (
    xcopy /s /i /y "referencias" "dist\GrabadorLSEC\referencias" >nul
    echo  - referencias/ copiado
)

REM ─── Resumen ──────────────────────────────────────────────
echo.
echo  ══════════════════════════════════════════════════
echo  BUILD COMPLETADO EXITOSAMENTE
echo  ══════════════════════════════════════════════════
echo.
echo  Ubicacion del ejecutable:
echo    dist\GrabadorLSEC\GrabadorLSEC.exe
echo.
echo  Para distribuir, copie toda la carpeta:
echo    dist\GrabadorLSEC\
echo.
echo  Contenido de la carpeta distribuible:
dir /b "dist\GrabadorLSEC\GrabadorLSEC.exe" 2>nul
dir /b "dist\GrabadorLSEC\lista_senas.txt" 2>nul
dir /b "dist\GrabadorLSEC\referencias" 2>nul
echo.
echo  Para crear un instalador, use Inno Setup con:
echo    installer\setup.iss
echo.
pause
