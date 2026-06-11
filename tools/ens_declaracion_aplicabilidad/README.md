# Asistente para la Declaración de Aplicabilidad del ENS

Programa interactivo que rellena la plantilla del **simulador de Declaración de
Aplicabilidad del ENS** (BP/14 del CCN-STIC).

## Qué hace

1. **Pregunta la categoría del sistema** (BÁSICA / MEDIA / ALTA) y, opcionalmente,
   permite afinar el nivel de cada dimensión de seguridad: **D**isponibilidad,
   **I**ntegridad, **C**onfidencialidad, **A**utenticidad y **T**razabilidad.
2. **Calcula qué controles aplican** replicando exactamente la lógica de la
   plantilla y **descuenta automáticamente** (marca como `n.a.` en la columna
   "Valores ajustados") los controles que solo aplican a una categoría superior
   a la elegida. Por ejemplo, si el sistema es **MEDIA**, se descuentan los
   controles exclusivos de **ALTA**.
3. **Recorre los controles aplicables** y permite escribir la justificación
   ("Cómo aplica, o por qué no aplica") y, si se desea, ajustar la aplicabilidad.
4. **Guarda un `.xlsx` nuevo** conservando intactos los gráficos, logos, estilos
   y fórmulas del original: solo se editan las celdas necesarias a nivel XML.
   El archivo fuerza el recálculo al abrirse, de modo que la categoría, los
   recuentos y los gráficos se actualizan solos en Excel/LibreOffice.

## Requisitos

- Python 3.8 o superior. **Sin dependencias externas** (no necesita `openpyxl`).

## Inicio rápido (doble clic)

Para no escribir comandos, usa los scripts de arranque incluidos:

- **Windows:** doble clic en `ejecutar.bat`
- **Mac / Linux:** doble clic (o `bash ejecutar.sh`) en `ejecutar.sh`

Antes de usarlos:

1. Copia tu plantilla en esta misma carpeta con el nombre
   `declaracion_aplicabilidad_ENS.xlsx` (o edita la variable `PLANTILLA` dentro
   del script).
2. (Opcional) Para que suba a Google Drive, deja configurado un remoto de
   `rclone` (ver más abajo). El destino se controla con la variable
   `DRIVE_DESTINO` al inicio del script; déjala vacía para no subir nada.

## Uso (línea de comandos)

```bash
python3 rellenar_doa_ens.py /ruta/a/declaracion_aplicabilidad_ENS.xlsx -o salida.xlsx
```

- Si no se indica plantilla, se busca `declaracion_aplicabilidad_ENS.xlsx` junto
  al script.
- Si no se indica `-o`, se genera `Declaracion_Aplicabilidad_ENS_<fecha>.xlsx`.

### Volcado a Google Drive

El resultado puede subirse automáticamente a Google Drive:

```bash
# 1) Detecta la carpeta de Google Drive for Desktop y copia ahí el resultado
python3 rellenar_doa_ens.py plantilla.xlsx --subir-drive

# 2) Carpeta concreta (lo más sencillo y fiable): apunta a tu unidad de Drive
python3 rellenar_doa_ens.py plantilla.xlsx --subir-drive "/ruta/Google Drive/Mi unidad/ENS"

# 3) Mediante rclone (si tienes un remoto de Drive configurado con 'rclone config')
python3 rellenar_doa_ens.py plantilla.xlsx --subir-drive "gdrive:Declaracion de Aplicabilidad"
```

> La forma más sencilla es tener **Google Drive for Desktop** instalado y, o
> bien usar `--subir-drive` (autodetección), o bien guardar directamente con
> `-o` dentro de tu carpeta de Drive (que se sincroniza sola). Para máquinas sin
> Drive for Desktop, usa un remoto de `rclone`.

Durante el recorrido de controles:

| Tecla        | Acción                                             |
|--------------|----------------------------------------------------|
| `ENTER`      | Deja el valor actual y pasa al siguiente control   |
| texto        | Escribe la justificación del control               |
| `i`          | Cambia la aplicabilidad (`aplica` / `n.a.` / `+R1`…) |
| `s`          | Salta el resto de controles y guarda               |
| `q`          | Sale sin guardar                                   |

## Ficheros

- `rellenar_doa_ens.py` — asistente interactivo (punto de entrada).
- `doa_engine.py` — motor: lógica de categoría por control y editor XML del `.xlsx`.

## Notas

- La plantilla `.xlsx` **no se incluye** en el repositorio (`.gitignore`) porque
  puede contener datos de la organización.
- Algunos controles vienen con la fórmula de categoría sustituida por un valor
  fijo `n.a.` (decisión manual de la organización). El programa los respeta y no
  los modifica automáticamente.
- La lógica de categoría se ha verificado de forma exhaustiva: reproduce la
  semántica de las fórmulas de la plantilla en las 1024 combinaciones posibles
  de niveles de las 5 dimensiones, sin discrepancias.
- El programa **no ajusta automáticamente los refuerzos** (`+R1`, `+R2`…) de los
  controles que sí aplican, ya que su correspondencia por nivel no está en las
  fórmulas de la plantilla. Puede ajustarlos manualmente con la opción `i`.
