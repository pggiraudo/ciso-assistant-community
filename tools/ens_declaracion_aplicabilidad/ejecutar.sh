#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Arranque del asistente de Declaración de Aplicabilidad del ENS (Mac / Linux).
# Doble clic (o ejecutar en el Terminal). Sube el resultado a Google Drive.
# ---------------------------------------------------------------------------

# === Configuración (ajústala si hace falta) ===============================
# Nombre de la plantilla (debe estar en esta misma carpeta):
PLANTILLA="declaracion_aplicabilidad_ENS.xlsx"
# Destino en Google Drive vía rclone (remoto:carpeta). Déjalo vacío ("") para
# NO subir a Drive y solo guardar el archivo en esta carpeta.
DRIVE_DESTINO="gdrive:Declaracion de Aplicabilidad"
# ==========================================================================

# Situarse en la carpeta del script
cd "$(dirname "$0")" || exit 1

# Buscar Python 3
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "ERROR: no se ha encontrado Python 3. Instálalo desde https://www.python.org/downloads/"
  read -r -p "Pulsa Enter para salir..."
  exit 1
fi

if [ ! -f "$PLANTILLA" ]; then
  echo "ERROR: no se encuentra la plantilla '$PLANTILLA' en esta carpeta."
  echo "Copia aquí tu archivo .xlsx o edita la variable PLANTILLA en este script."
  read -r -p "Pulsa Enter para salir..."
  exit 1
fi

if [ -n "$DRIVE_DESTINO" ]; then
  "$PY" rellenar_doa_ens.py "$PLANTILLA" --subir-drive "$DRIVE_DESTINO"
else
  "$PY" rellenar_doa_ens.py "$PLANTILLA"
fi

echo
read -r -p "Listo. Pulsa Enter para cerrar..."
