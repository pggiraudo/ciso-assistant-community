@echo off
REM ---------------------------------------------------------------------------
REM Arranque del asistente de Declaracion de Aplicabilidad del ENS (Windows).
REM Doble clic sobre este archivo. Sube el resultado a Google Drive.
REM ---------------------------------------------------------------------------
setlocal

REM === Configuracion (ajustala si hace falta) ================================
REM Nombre de la plantilla (debe estar en esta misma carpeta):
set "PLANTILLA=declaracion_aplicabilidad_ENS.xlsx"
REM Destino en Google Drive via rclone (remoto:carpeta). Dejalo vacio para
REM NO subir a Drive y solo guardar el archivo en esta carpeta.
set "DRIVE_DESTINO=gdrive:Declaracion de Aplicabilidad"
REM ==========================================================================

cd /d "%~dp0"

REM Buscar Python (py launcher o python)
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo ERROR: no se ha encontrado Python 3. Instalalo desde https://www.python.org/downloads/
  echo Marca "Add Python to PATH" durante la instalacion.
  pause
  exit /b 1
)

if not exist "%PLANTILLA%" (
  echo ERROR: no se encuentra la plantilla "%PLANTILLA%" en esta carpeta.
  echo Copia aqui tu archivo .xlsx o edita la variable PLANTILLA en este script.
  pause
  exit /b 1
)

if defined DRIVE_DESTINO (
  %PY% rellenar_doa_ens.py "%PLANTILLA%" --subir-drive "%DRIVE_DESTINO%"
) else (
  %PY% rellenar_doa_ens.py "%PLANTILLA%"
)

echo.
echo Listo.
pause
endlocal
