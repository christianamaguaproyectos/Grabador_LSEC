; ══════════════════════════════════════════════════════════
; Inno Setup Script - Grabador LSEC
;
; Genera un instalador profesional para Windows que:
; - Instala GrabadorLSEC.exe y dependencias
; - Copia recursos editables (lista_senas.txt, referencias/)
; - Crea acceso directo en escritorio y menú inicio
; - Incluye desinstalador
;
; Requisito: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Compilar: Abrir este archivo en Inno Setup y presionar Compile
; ══════════════════════════════════════════════════════════

#define MyAppName "Grabador LSEC"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ESPE 2026 - Tesis de Grado"
#define MyAppURL "https://github.com/camagua/grabador_lsec"
#define MyAppExeName "GrabadorLSEC.exe"
#define MyAppDescription "Sistema de grabación de Lengua de Señas Ecuatoriana para dataset de investigación"

[Setup]
; NOTA: Genere un nuevo AppId para cada aplicación distinta.
; No use este mismo AppId en otros instaladores.
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppComments={#MyAppDescription}

; Directorio de instalación por defecto
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Archivos de salida del instalador
OutputDir=Output
OutputBaseFilename=GrabadorLSEC_Setup_{#MyAppVersion}

; Compresión
Compression=lzma2
SolidCompression=yes

; Permisos - no requiere admin (instala en AppData si no hay permisos)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Apariencia
WizardStyle=modern
; SetupIconFile=..\assets\icon.ico  ; Descomentar cuando se tenga icono

; Otras opciones
AllowNoIcons=yes
LicenseFile=
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Iconos adicionales:"; Flags: checkedonce

[Files]
; Todos los archivos de la carpeta dist/GrabadorLSEC (incluyendo subcarpetas)
Source: "..\dist\GrabadorLSEC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Acceso directo en menú inicio
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

; Acceso directo en escritorio (opcional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

[Run]
; Opción para ejecutar después de instalar
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
; Limpiar archivos generados durante el uso
Type: filesandirs; Name: "{app}\dataset"
Type: files; Name: "{app}\session_log.csv"
Type: files; Name: "{app}\grabador_lsec.log"
