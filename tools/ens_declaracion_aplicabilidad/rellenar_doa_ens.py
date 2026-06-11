#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rellena de forma interactiva la plantilla de Declaración de Aplicabilidad del
ENS (simulador BP/14 del CCN-STIC).

Flujo:
  1. Pregunta la categoría del sistema (BÁSICA / MEDIA / ALTA) y, opcionalmente,
     afina el nivel de cada dimensión de seguridad (D, I, C, A, T).
  2. Calcula qué controles aplican y DESCUENTA automáticamente (marca como
     "n.a." en la columna "Valores ajustados") los que solo aplican a una
     categoría superior a la elegida.
  3. Recorre los controles aplicables y permite escribir la justificación
     ("Cómo aplica, o por qué no aplica") y, si se desea, ajustar la
     aplicabilidad.
  4. Guarda un .xlsx nuevo conservando intactos gráficos, logos, estilos y
     fórmulas del original (se editan solo las celdas necesarias).

Uso:
    python3 rellenar_doa_ens.py [plantilla.xlsx] [-o salida.xlsx]

Requisitos: Python 3.8+. Sin dependencias externas.
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys

from doa_engine import (DoaWorkbook, required_category, DIM_CELLS,
                        _CAT_TO_LEVEL)

DIM_NAMES = {
    "D": "Disponibilidad",
    "I": "Integridad",
    "C": "Confidencialidad",
    "A": "Autenticidad",
    "T": "Trazabilidad",
}
CAT_CHOICE = {"1": "BASICA", "2": "MEDIA", "3": "ALTA"}
VALID_LEVELS = ["n.a.", "BAJO", "MEDIO", "ALTO"]


# --------------------------------------------------------------------------
# Utilidades de entrada
# --------------------------------------------------------------------------
def ask(prompt, default=None):
    suffix = " [%s]" % default if default is not None else ""
    try:
        resp = input("%s%s: " % (prompt, suffix)).strip()
    except EOFError:
        return default
    return resp if resp else default


def ask_choice(prompt, options, default=None):
    while True:
        resp = ask(prompt, default)
        if resp is None:
            continue
        resp = resp.strip()
        if resp in options:
            return resp
        print("  -> Opción no válida. Use uno de: %s" % ", ".join(options))


# --------------------------------------------------------------------------
# Pasos del asistente
# --------------------------------------------------------------------------
def step_levels():
    print("\n" + "=" * 64)
    print(" CATEGORÍA DEL SISTEMA")
    print("=" * 64)
    print("  1) BÁSICA")
    print("  2) MEDIA")
    print("  3) ALTA")
    cat = CAT_CHOICE[ask_choice("¿A qué categoría va el sistema? (1/2/3)",
                                CAT_CHOICE, default="2")]
    base_level = _CAT_TO_LEVEL[cat]
    print("\nCategoría elegida: %s  (nivel por defecto de cada dimensión: %s)"
          % (cat, base_level))

    refine = ask("¿Afinar el nivel de cada dimensión por separado? (s/N)",
                 "N").lower().startswith("s")
    levels = {}
    if not refine:
        for d in DIM_CELLS:
            levels[d] = base_level
    else:
        print("\nIntroduzca el nivel de cada dimensión "
              "(%s):" % "/".join(VALID_LEVELS))
        for d in DIM_CELLS:
            lv = ask_choice("  %s (%s)" % (DIM_NAMES[d], d),
                            VALID_LEVELS, default=base_level)
            levels[d] = lv
    return cat, levels


def step_apply(doc, levels):
    """Calcula aplicabilidad, descuenta los no aplicables y devuelve la lista
    de controles aplicables (con fórmula)."""
    applicable, discounted, fixed = [], [], []
    for ctrl in doc.controls:
        if not ctrl["formula"].strip():
            fixed.append(ctrl)            # control fijado manualmente -> no tocar
            continue
        req = required_category(ctrl["dims"], ctrl["min_cat"], levels)
        ctrl["required"] = req
        if req == "n.a.":
            discounted.append(ctrl)
        else:
            applicable.append(ctrl)

    # Escribir niveles de dimensión
    for d, cell in DIM_CELLS.items():
        doc.set_cell_string(cell, levels[d])

    # Descontar (col. I = n.a.) y reactivar los que vuelvan a aplicar
    for ctrl in discounted:
        if ctrl["applicability"] != "n.a.":
            doc.set_cell_string("I%d" % ctrl["row"], "n.a.")
    for ctrl in applicable:
        if ctrl["applicability"].strip().lower() in ("", "n.a."):
            doc.set_cell_string("I%d" % ctrl["row"], "aplica")
            ctrl["applicability"] = "aplica"

    print("\n" + "=" * 64)
    print(" RESUMEN DE APLICABILIDAD")
    print("=" * 64)
    print("  Controles aplicables          : %d" % len(applicable))
    print("  Descontados (categoría sup.)  : %d" % len(discounted))
    print("  Fijados manualmente (n.a.)    : %d" % len(fixed))
    if discounted:
        print("\n  Descontados automáticamente:")
        for c in discounted:
            print("    - %-12s %s" % (c["code"], c["desc"]))
    return applicable


def step_justify(doc, applicable):
    print("\n" + "=" * 64)
    print(" JUSTIFICACIÓN DE CONTROLES")
    print("=" * 64)
    print("Para cada control puede escribir la justificación.")
    print("  · ENTER         -> deja el valor actual y pasa al siguiente")
    print("  · 'i'           -> cambia la aplicabilidad (aplica/n.a./+R...)")
    print("  · 's'           -> saltar el resto y guardar")
    print("  · 'q'           -> salir sin guardar\n")

    total = len(applicable)
    for idx, ctrl in enumerate(applicable, 1):
        print("-" * 64)
        print("[%d/%d] %s — %s" % (idx, total, ctrl["code"], ctrl["desc"]))
        print("   Dimensiones: %s | Cat. exigida: %s | Aplicabilidad: %s"
              % (ctrl["dims_txt"].strip(), ctrl.get("required", "?"),
                 ctrl["applicability"]))
        if ctrl["justification"]:
            print("   Justificación actual: %s" % ctrl["justification"])
        resp = ask("   Justificación (o i/s/q)", default="")
        if resp == "":
            continue
        if resp.lower() == "q":
            print("Saliendo SIN guardar.")
            sys.exit(0)
        if resp.lower() == "s":
            print("Se omite el resto de controles.")
            break
        if resp.lower() == "i":
            nuevo = ask("     Nueva aplicabilidad (aplica/n.a./+R1...)",
                        ctrl["applicability"])
            doc.set_cell_string("I%d" % ctrl["row"], nuevo)
            ctrl["applicability"] = nuevo
            just = ask("     Justificación", default=ctrl["justification"])
            if just is not None:
                doc.set_cell_string("N%d" % ctrl["row"], just)
            continue
        # texto normal -> justificación
        doc.set_cell_string("N%d" % ctrl["row"], resp)


# --------------------------------------------------------------------------
# Volcado a Google Drive
# --------------------------------------------------------------------------
def _find_drive_dir():
    """Intenta localizar una carpeta sincronizada de Google Drive (Desktop)."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "Google Drive", "Mi unidad"),
        os.path.join(home, "Google Drive", "My Drive"),
        os.path.join(home, "GoogleDrive", "Mi unidad"),
        os.path.join(home, "Google Drive"),
    ]
    # Windows: unidades G:, H: que monta Google Drive for Desktop
    for letra in "GHIJ":
        candidates.append("%s:\\Mi unidad" % letra)
        candidates.append("%s:\\My Drive" % letra)
    for path in candidates:
        if os.path.isdir(path):
            return path
    return None


def subir_a_drive(local_path, destino):
    """Sube `local_path` a Google Drive.

    `destino` puede ser:
      - una ruta de carpeta local sincronizada por Google Drive for Desktop, o
      - un remoto de rclone con el formato 'remoto:carpeta' (p.ej. 'gdrive:ENS').
      - 'auto' para detectar la carpeta de Google Drive for Desktop.
    """
    nombre = os.path.basename(local_path)

    if destino == "auto":
        destino = _find_drive_dir()
        if not destino:
            print("\n[Drive] No se ha encontrado una carpeta de Google Drive "
                  "for Desktop. Use --subir-drive con una ruta o un remoto "
                  "rclone (p.ej. 'gdrive:ENS').")
            return
        print("[Drive] Carpeta de Google Drive detectada: %s" % destino)

    # Remoto rclone (contiene ':' y no es una ruta de Windows tipo C:\)
    es_rclone = (":" in destino and not os.path.isdir(destino)
                 and not (len(destino) > 1 and destino[1] == ":"))
    if es_rclone:
        if not shutil.which("rclone"):
            print("\n[Drive] rclone no está instalado. Instálelo y configure "
                  "un remoto de Google Drive (rclone config), o use una "
                  "carpeta local sincronizada.")
            return
        cmd = ["rclone", "copyto", local_path,
               destino.rstrip("/") + "/" + nombre]
        try:
            subprocess.run(cmd, check=True)
            print("[Drive] Subido a %s/%s" % (destino.rstrip('/'), nombre))
        except subprocess.CalledProcessError as e:
            print("[Drive] Error al subir con rclone: %s" % e)
        return

    # Carpeta local (sincronizada por Google Drive for Desktop)
    if not os.path.isdir(destino):
        print("\n[Drive] La carpeta destino no existe: %s" % destino)
        return
    dest_file = os.path.join(destino, nombre)
    shutil.copy2(local_path, dest_file)
    print("[Drive] Copiado a la carpeta de Drive: %s" % dest_file)
    print("        Google Drive for Desktop lo sincronizará automáticamente.")


# --------------------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_tpl = os.path.join(here, "declaracion_aplicabilidad_ENS.xlsx")

    ap = argparse.ArgumentParser(
        description="Rellena la Declaración de Aplicabilidad del ENS.")
    ap.add_argument("plantilla", nargs="?", default=default_tpl,
                    help="Ruta de la plantilla .xlsx (por defecto: junto al script)")
    ap.add_argument("-o", "--salida", help="Ruta del archivo de salida .xlsx")
    ap.add_argument("--subir-drive", dest="subir_drive", nargs="?",
                    const="auto", default=None, metavar="DESTINO",
                    help="Sube el resultado a Google Drive. Sin valor, detecta "
                         "la carpeta de Google Drive for Desktop. También admite "
                         "una ruta de carpeta o un remoto rclone (p.ej. 'gdrive:ENS').")
    args = ap.parse_args()

    if not os.path.isfile(args.plantilla):
        sys.exit("ERROR: no se encuentra la plantilla: %s" % args.plantilla)

    out = args.salida
    if not out:
        fecha = datetime.date.today().isoformat()
        out = os.path.join(os.path.dirname(args.plantilla) or ".",
                           "Declaracion_Aplicabilidad_ENS_%s.xlsx" % fecha)

    print("Plantilla: %s" % args.plantilla)
    doc = DoaWorkbook(args.plantilla)
    print("Controles detectados: %d" % len(doc.controls))

    cat, levels = step_levels()
    applicable = step_apply(doc, levels)
    step_justify(doc, applicable)

    doc.save(out)
    print("\n" + "=" * 64)
    print(" GUARDADO: %s" % out)
    print("=" * 64)
    print("Abra el archivo en Excel/LibreOffice: la categoría, los recuentos")
    print("y los gráficos se recalcularán automáticamente al abrirlo.")

    if args.subir_drive is not None:
        subir_a_drive(out, args.subir_drive)


if __name__ == "__main__":
    main()
