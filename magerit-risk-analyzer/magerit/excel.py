"""Exportación del análisis de riesgos Magerit a Excel (.xlsx).

Genera un libro con varias hojas:
  - Portada / Resumen ejecutivo
  - Inventario y valoración de activos (5 dimensiones)
  - Registro de riesgos (intrínseco y residual)
  - Validación de las 5 dimensiones
  - Controles ISO 27001 recomendados
  - Medidas ENS recomendadas
"""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from . import catalog, engine
from .engine import Asset, RiskItem

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(color="1F4E78", bold=True, size=16)
SUBTITLE_FONT = Font(color="1F4E78", bold=True, size=12)
BOLD = Font(bold=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

LEVEL_COLORS = {
    "Muy Bajo": "C6EFCE",
    "Bajo": "A9D08E",
    "Medio": "FFEB9C",
    "Alto": "F8CBAD",
    "Muy Alto": "FF7C80",
}


def _style_header(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        c = ws.cell(row=row, column=col)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER


def _level_fill(level: str) -> PatternFill | None:
    color = LEVEL_COLORS.get(level)
    return PatternFill("solid", fgColor=color) if color else None


def _autofit(ws, widths: dict[int, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


# ---------------------------------------------------------------------------
# Hojas
# ---------------------------------------------------------------------------
def _sheet_cover(wb: Workbook, company: str, risks: list[RiskItem],
                 assets: list[Asset]) -> None:
    ws = wb.active
    ws.title = "Resumen"
    ws.sheet_view.showGridLines = False

    ws["A1"] = "Análisis de Riesgos - Metodología MAGERIT"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = "ISO/IEC 27001:2022 · Esquema Nacional de Seguridad (RD 311/2022)"
    ws["A2"].font = SUBTITLE_FONT

    rows = [
        ("Organización:", company or "—"),
        ("Nº de activos analizados:", len(assets)),
        ("Nº de escenarios de riesgo:", len(risks)),
    ]
    r = 4
    for label, value in rows:
        ws.cell(row=r, column=1, value=label).font = BOLD
        ws.cell(row=r, column=2, value=value)
        r += 1

    # Distribución de riesgo intrínseco vs residual
    r += 1
    ws.cell(row=r, column=1, value="Distribución de escenarios por nivel de riesgo").font = SUBTITLE_FONT
    r += 1
    headers = ["Nivel", "Riesgo inherente", "Riesgo residual", "Descripción"]
    for i, h in enumerate(headers, start=1):
        ws.cell(row=r, column=i, value=h)
    _style_header(ws, r, len(headers))

    intr = engine.summary_by_level(risks, residual=False)
    resid = engine.summary_by_level(risks, residual=True)
    for lvl in ["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"]:
        r += 1
        ws.cell(row=r, column=1, value=lvl).border = BORDER
        ws.cell(row=r, column=2, value=intr.get(lvl, 0)).border = BORDER
        ws.cell(row=r, column=3, value=resid.get(lvl, 0)).border = BORDER
        ws.cell(row=r, column=4, value=catalog.RISK_LEVELS.get(lvl, "")).border = BORDER
        fill = _level_fill(lvl)
        if fill:
            ws.cell(row=r, column=1).fill = fill
        for c in range(1, 5):
            ws.cell(row=r, column=c).alignment = LEFT if c == 4 else CENTER

    r += 2
    ws.cell(row=r, column=1, value="Top 5 riesgos residuales").font = SUBTITLE_FONT
    r += 1
    th = ["Activo", "Amenaza", "Nivel residual", "Puntuación"]
    for i, h in enumerate(th, start=1):
        ws.cell(row=r, column=i, value=h)
    _style_header(ws, r, len(th))
    for rk in engine.top_risks(risks, n=5, residual=True):
        r += 1
        ws.cell(row=r, column=1, value=rk.asset.name).border = BORDER
        ws.cell(row=r, column=2, value=f"[{rk.threat['code']}] {rk.threat['name']}").border = BORDER
        cell = ws.cell(row=r, column=3, value=rk.residual_level)
        cell.border = BORDER
        cell.alignment = CENTER
        fill = _level_fill(rk.residual_level)
        if fill:
            cell.fill = fill
        ws.cell(row=r, column=4, value=rk.residual_score).border = BORDER

    _autofit(ws, {1: 32, 2: 42, 3: 18, 4: 14})


def _sheet_assets(wb: Workbook, assets: list[Asset]) -> None:
    ws = wb.create_sheet("Activos")
    headers = ["ID", "Activo", "Tipo", "Responsable", "Descripción",
               "C", "I", "D", "A", "T", "Valor máx.", "Madurez salvaguardas"]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    for a in assets:
        ws.append([
            a.asset_id, a.name, catalog.ASSET_TYPES.get(a.asset_type, a.asset_type),
            a.owner, a.description, a.C, a.I, a.D, a.A, a.T, a.max_value(),
            a.safeguard_maturity,
        ])
        row = ws.max_row
        for col in range(1, len(headers) + 1):
            ws.cell(row=row, column=col).border = BORDER
            if 6 <= col <= 11:
                ws.cell(row=row, column=col).alignment = CENTER

    ws.freeze_panes = "A2"
    _autofit(ws, {1: 10, 2: 34, 3: 30, 4: 18, 5: 38,
                  6: 5, 7: 5, 8: 5, 9: 5, 10: 5, 11: 11, 12: 30})


def _sheet_risks(wb: Workbook, risks: list[RiskItem]) -> None:
    ws = wb.create_sheet("Riesgos")
    headers = ["ID activo", "Activo", "Tipo", "Cód. amenaza", "Amenaza",
               "Grupo", "Dimensiones", "Valor activo", "Degradación %",
               "Probabilidad", "Impacto", "Riesgo inherente", "Nivel inherente",
               "Eficacia salvaguardas %", "Riesgo residual", "Nivel residual",
               "Controles ISO 27001", "Medidas ENS"]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    for r in risks:
        ws.append([
            r.asset.asset_id, r.asset.name,
            catalog.ASSET_TYPES.get(r.asset.asset_type, r.asset.asset_type),
            r.threat["code"], r.threat["name"],
            catalog.THREAT_GROUPS.get(r.threat["group"], r.threat["group"]),
            ", ".join(r.affected_dimensions),
            r.asset_value, round(r.degradation * 100),
            r.probability, r.impact, r.intrinsic_score, r.intrinsic_level,
            round(r.safeguard_efficacy * 100), r.residual_score, r.residual_level,
            ", ".join(r.iso27001), ", ".join(r.ens),
        ])
        row = ws.max_row
        for col in range(1, len(headers) + 1):
            ws.cell(row=row, column=col).border = BORDER
            if col in (6, 7) or 8 <= col <= 16:
                ws.cell(row=row, column=col).alignment = CENTER
        # colorear niveles
        intr_fill = _level_fill(r.intrinsic_level)
        if intr_fill:
            ws.cell(row=row, column=13).fill = intr_fill
        resid_fill = _level_fill(r.residual_level)
        if resid_fill:
            ws.cell(row=row, column=16).fill = resid_fill

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    _autofit(ws, {1: 10, 2: 28, 3: 26, 4: 11, 5: 38, 6: 24, 7: 12, 8: 11,
                  9: 12, 10: 12, 11: 9, 12: 13, 13: 14, 14: 16, 15: 13, 16: 14,
                  17: 30, 18: 24})


def _sheet_dimensions(wb: Workbook, assets: list[Asset], risks: list[RiskItem]) -> None:
    ws = wb.create_sheet("5 Dimensiones")
    ws["A1"] = "Validación de las 5 dimensiones de seguridad (Magerit / ENS)"
    ws["A1"].font = SUBTITLE_FONT

    validation = engine.validate_dimensions(assets)
    risk_by_dim = engine.summary_by_dimension(risks, residual=True)

    headers = ["Dim.", "Dimensión", "Descripción", "Activos valorados",
               "Valor máx.", "Valor medio", "Riesgo residual máx.", "Cubierta"]
    start = 3
    for i, h in enumerate(headers, start=1):
        ws.cell(row=start, column=i, value=h)
    _style_header(ws, start, len(headers))

    r = start
    for dim, info in validation["per_dimension"].items():
        r += 1
        ws.cell(row=r, column=1, value=dim)
        ws.cell(row=r, column=2, value=info["name"])
        ws.cell(row=r, column=3, value=catalog.DIMENSION_DESCRIPTIONS.get(dim, ""))
        ws.cell(row=r, column=4, value=f"{info['assets_valued']} / {info['total_assets']}")
        ws.cell(row=r, column=5, value=info["max"])
        ws.cell(row=r, column=6, value=info["avg"])
        ws.cell(row=r, column=7, value=round(risk_by_dim.get(dim, 0.0), 1))
        ws.cell(row=r, column=8, value="Sí" if info["covered"] else "No")
        for col in range(1, len(headers) + 1):
            ws.cell(row=r, column=col).border = BORDER
            ws.cell(row=r, column=col).alignment = LEFT if col == 3 else CENTER
        if not info["covered"]:
            ws.cell(row=r, column=8).fill = PatternFill("solid", fgColor="FF7C80")

    # Avisos
    if validation["warnings"]:
        r += 2
        ws.cell(row=r, column=1, value="Avisos:").font = BOLD
        for w in validation["warnings"]:
            r += 1
            ws.cell(row=r, column=1, value="• " + w)

    _autofit(ws, {1: 6, 2: 18, 3: 60, 4: 18, 5: 11, 6: 12, 7: 18, 8: 10})


def _sheet_controls(wb: Workbook, risks: list[RiskItem]) -> None:
    ws = wb.create_sheet("Controles ISO-ENS")
    ws["A1"] = "Controles y medidas recomendados (riesgo residual ≥ Medio)"
    ws["A1"].font = SUBTITLE_FONT

    rec = engine.recommended_controls(risks, min_level="Medio")

    ws.cell(row=3, column=1, value="ISO/IEC 27001:2022 - Anexo A").font = BOLD
    ws.cell(row=3, column=4, value="ENS - RD 311/2022 (Anexo II)").font = BOLD

    for i, h in enumerate(["Control", "Nº de riesgos"], start=1):
        ws.cell(row=4, column=i, value=h)
    for i, h in enumerate(["Medida", "Nº de riesgos"], start=4):
        ws.cell(row=4, column=i, value=h)
    _style_header(ws, 4, 2)
    for col in (4, 5):
        c = ws.cell(row=4, column=col)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER

    iso_items = list(rec["iso27001"].items())
    ens_items = list(rec["ens"].items())
    for idx in range(max(len(iso_items), len(ens_items))):
        row = 5 + idx
        if idx < len(iso_items):
            ws.cell(row=row, column=1, value=iso_items[idx][0]).border = BORDER
            ws.cell(row=row, column=2, value=iso_items[idx][1]).border = BORDER
            ws.cell(row=row, column=2).alignment = CENTER
        if idx < len(ens_items):
            ws.cell(row=row, column=4, value=ens_items[idx][0]).border = BORDER
            ws.cell(row=row, column=5, value=ens_items[idx][1]).border = BORDER
            ws.cell(row=row, column=5).alignment = CENTER

    _autofit(ws, {1: 16, 2: 14, 3: 4, 4: 16, 5: 14})


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def build_workbook(company: str, assets: list[Asset], risks: list[RiskItem]) -> Workbook:
    wb = Workbook()
    _sheet_cover(wb, company, risks, assets)
    _sheet_assets(wb, assets)
    _sheet_risks(wb, risks)
    _sheet_dimensions(wb, assets, risks)
    _sheet_controls(wb, risks)
    return wb


def to_bytes(company: str, assets: list[Asset], risks: list[RiskItem]) -> bytes:
    """Devuelve el .xlsx como bytes (para descarga en Streamlit)."""
    wb = build_workbook(company, assets, risks)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
