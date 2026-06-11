@echo off
REM ---------------------------------------------------------------------------
REM Instalador guiado (Windows) para el asistente de Declaracion de
REM Aplicabilidad del ENS. Comprueba e instala Python 3 y rclone usando winget,
REM y ayuda a conectar tu Google Drive. No instala nada sin preguntar.
REM ---------------------------------------------------------------------------
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ==^> 1) Comprobando Python 3
where py >nul 2>nul && (set "PYOK=1") || (where python >nul 2>nul && set "PYOK=1")
if defined PYOK (
  echo   OK: Python ya esta instalado.
) else (
  echo   !! No se ha encontrado Python 3.
  where winget >nul 2>nul
  if !errorlevel! == 0 (
    set /p R=  Instalar Python 3 ahora con winget? [s/N]:
    if /I "!R!"=="s" winget install -e --id Python.Python.3.12
  ) else (
    echo   Instalalo desde https://www.python.org/downloads/  ^(marca "Add Python to PATH"^)
    start "" "https://www.python.org/downloads/"
  )
)

echo.
echo ==^> 2) Comprobando rclone ^(para subir a Google Drive^)
where rclone >nul 2>nul
if !errorlevel! == 0 (
  echo   OK: rclone ya esta instalado.
) else (
  echo   !! No se ha encontrado rclone.
  where winget >nul 2>nul
  if !errorlevel! == 0 (
    set /p R=  Instalar rclone ahora con winget? [s/N]:
    if /I "!R!"=="s" winget install -e --id Rclone.Rclone
  ) else (
    echo   Descargalo desde https://rclone.org/downloads/
    start "" "https://rclone.org/downloads/"
  )
)

echo.
echo ==^> 3) Conectar tu Google Drive con rclone
where rclone >nul 2>nul
if !errorlevel! == 0 (
  rclone listremotes 2>nul | findstr /b /c:"gdrive:" >nul
  if !errorlevel! == 0 (
    echo   OK: Ya tienes un remoto "gdrive:" configurado.
  ) else (
    echo   Cuando rclone pregunte, responde:
    echo     n  ^| name: gdrive ^| Storage: drive
    echo     client_id / client_secret: Enter ^(vacio^)
    echo     scope: 1  ^| el resto: Enter
    echo     Use auto config? y  -^> se abre el navegador para iniciar sesion
    echo     Shared Drive? n  ^| confirmar: y  ^| salir: q
    set /p R=  Lanzar "rclone config" ahora? [s/N]:
    if /I "!R!"=="s" rclone config
  )
) else (
  echo   !! rclone no disponible: podras generar el archivo, pero tendras que subirlo a Drive a mano.
)

echo.
echo ==^> Instalacion finalizada. Ahora ejecuta ejecutar.bat
pause
endlocal
