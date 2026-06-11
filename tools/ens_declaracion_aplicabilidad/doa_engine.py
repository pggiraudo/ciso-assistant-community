# -*- coding: utf-8 -*-
"""
Motor para la Declaración de Aplicabilidad del ENS (simulador BP/14 del CCN).

No depende de librerías externas: edita el .xlsx directamente a nivel XML,
modificando SOLO las celdas necesarias y conservando intactos el resto del
libro (gráficos, logos, estilos, fórmulas).
"""
import re
import shutil
import zipfile

# Orden de niveles de seguridad
_RANK = {"BASICA": 1, "MEDIA": 2, "ALTA": 3}
_LEVEL_TO_CAT = {"BAJO": "BASICA", "MEDIO": "MEDIA", "ALTO": "ALTA"}
_CAT_TO_LEVEL = {"BASICA": "BAJO", "MEDIA": "MEDIO", "ALTA": "ALTO"}

# Celdas de los niveles por dimensión en la hoja Controles
DIM_CELLS = {"D": "I6", "I": "J6", "C": "K6", "A": "L6", "T": "M6"}

CONTROL_SHEET = "Controles"
FIRST_ROW, LAST_ROW = 13, 102


def _xml_escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def _xml_unescape(text):
    return (text.replace("&quot;", '"').replace("&lt;", "<")
                .replace("&gt;", ">").replace("&amp;", "&"))


def system_category(levels):
    """Categoría global del sistema (réplica de H6): ALTA/MEDIA/BASICA."""
    vals = [levels.get(d) for d in DIM_CELLS]
    if "ALTO" in vals:
        return "ALTA"
    if "MEDIO" in vals:
        return "MEDIA"
    return "BASICA"  # la fórmula original devuelve BASICA como caso final


def classify_formula(formula):
    """Clasifica la fórmula de la columna H (Cat. Sistema) en (dims, min_cat).

    dims: 'SYSTEM' (depende de la categoría global) o conjunto de dimensiones
          {'D','I','C','A','T'} que la determinan.
    min_cat: categoría mínima a la que el control empieza a aplicar
             ('BASICA', 'MEDIA' o 'ALTA'); por debajo => n.a.
    """
    f = (formula or "").strip()
    # Fórmulas basadas en la categoría global del sistema (SI_CAT / $H$6)
    if "SI_CAT" in f or "$H$6" in f:
        if 'SI_CAT="MEDIA"' in f.replace(" ", "") or '$H$6="MEDIA"' in f.replace(" ", ""):
            return ("SYSTEM", "ALTA")          # n.a. si BASICA o MEDIA
        if '"BASICA"' in f:
            return ("SYSTEM", "MEDIA")          # n.a. si BASICA
        return ("SYSTEM", "BASICA")             # = SI_CAT
    # Fórmulas basadas en dimensiones concretas (I6=D, J6=I, K6=C, L6=A, M6=T)
    cell_to_dim = {v: k for k, v in DIM_CELLS.items()}
    dims = {cell_to_dim[c] for c in re.findall(r"[IJKLM]6", f) if c in cell_to_dim}
    min_cat = "BASICA" if '"BASICA"' in f else "MEDIA"
    return (dims, min_cat)


def required_category(dims, min_cat, levels):
    """Categoría exigida a un control dados los niveles de dimensión.

    Devuelve 'BASICA'/'MEDIA'/'ALTA' o 'n.a.' si el control no aplica.
    """
    if dims == "SYSTEM":
        cat = system_category(levels)
    else:
        ranks = [_RANK[_LEVEL_TO_CAT[levels[d]]]
                 for d in dims if levels.get(d) in _LEVEL_TO_CAT]
        if not ranks:
            return "n.a."
        cat = {1: "BASICA", 2: "MEDIA", 3: "ALTA"}[max(ranks)]
    if _RANK[cat] < _RANK[min_cat]:
        return "n.a."
    return cat


# --------------------------------------------------------------------------
# Acceso/edición del .xlsx a bajo nivel (sin reescribir todo el paquete)
# --------------------------------------------------------------------------
class DoaWorkbook:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self._sheet_file = self._resolve_sheet_file(CONTROL_SHEET)
        self._sheet_xml = self.zip.read("xl/" + self._sheet_file).decode("utf-8")
        self._shared = self._read_shared_strings()
        self.controls = self._parse_controls()

    def _resolve_sheet_file(self, name):
        wb = self.zip.read("xl/workbook.xml").decode("utf-8")
        rels = self.zip.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        sheets = re.findall(r'<sheet[^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb)
        relmap = dict(re.findall(
            r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
        for sname, rid in sheets:
            if sname == name:
                return relmap[rid].lstrip("/").replace("xl/", "")
        raise KeyError("Hoja %r no encontrada" % name)

    def _read_shared_strings(self):
        try:
            ss = self.zip.read("xl/sharedStrings.xml").decode("utf-8")
        except KeyError:
            return []
        return [''.join(re.findall(r"<t[^>]*>(.*?)</t>", blob, re.S))
                for blob in re.findall(r"<si>(.*?)</si>", ss, re.S)]

    def _cell_text(self, cell_xml):
        """Texto de una celda <c ...> ya sea shared, inline o string."""
        if cell_xml is None:
            return ""
        t = re.search(r'\bt="([^"]+)"', cell_xml)
        ttype = t.group(1) if t else None
        if ttype == "s":
            idx = re.search(r"<v>(\d+)</v>", cell_xml)
            return self._shared[int(idx.group(1))] if idx else ""
        if ttype == "inlineStr":
            return ''.join(re.findall(r"<t[^>]*>(.*?)</t>", cell_xml, re.S))
        m = re.search(r"<v>(.*?)</v>", cell_xml, re.S)
        return m.group(1) if m else ""

    def _row_xml(self, row):
        m = re.search(r'<row r="%d"[ >].*?</row>' % row, self._sheet_xml, re.S)
        return m.group(0) if m else ""

    def _cell_xml(self, ref):
        row = int(re.search(r"\d+", ref).group(0))
        rowxml = self._row_xml(row)
        m = re.search(r'<c r="%s"[ >].*?(?:/>|</c>)' % ref, rowxml, re.S)
        return m.group(0) if m else None

    def _parse_controls(self):
        """Lista de controles reales (omite cabeceras de bloque)."""
        controls = []
        for row in range(FIRST_ROW, LAST_ROW + 1):
            rowxml = self._row_xml(row)
            if not rowxml:
                continue
            def cell(col):
                m = re.search(r'<c r="%s%d"[ >].*?(?:/>|</c>)' % (col, row),
                              rowxml, re.S)
                return m.group(0) if m else None
            dims_txt = self._cell_text(cell("E"))
            if not dims_txt.strip():
                continue  # cabecera de bloque (sin dimensiones) -> no es control
            hcell = cell("H")
            hf = re.search(r"<f>(.*?)</f>", hcell, re.S) if hcell else None
            formula = ("=" + _xml_unescape(hf.group(1))) if hf else ""
            dims, min_cat = classify_formula(formula)
            controls.append({
                "row": row,
                "code": self._cell_text(cell("C")),
                "desc": self._cell_text(cell("D")),
                "dims_txt": dims_txt,
                "formula": formula,
                "dims": dims,
                "min_cat": min_cat,
                "applicability": self._cell_text(cell("I")),
                "justification": self._cell_text(cell("N")),
            })
        return controls

    # ---- escritura ----
    def set_cell_string(self, ref, value):
        """Fija una celda como cadena inline, conservando su estilo (s)."""
        value = "" if value is None else str(value)
        old = self._cell_xml(ref)
        s_attr = ""
        if old:
            sm = re.search(r'\bs="(\d+)"', old)
            if sm:
                s_attr = ' s="%s"' % sm.group(1)
        if value == "":
            new = '<c r="%s"%s/>' % (ref, s_attr)
        else:
            new = ('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">'
                   '%s</t></is></c>' % (ref, s_attr, _xml_escape(value)))
        if old:
            self._sheet_xml = self._sheet_xml.replace(old, new, 1)
        else:
            # insertar dentro de la fila (raro: las celdas suelen existir)
            row = int(re.search(r"\d+", ref).group(0))
            self._sheet_xml = re.sub(
                r'(<row r="%d"[^>]*>)' % row, r"\1" + new, self._sheet_xml, 1)

    def save(self, out_path):
        # forzar recálculo al abrir (H, recuentos, gráficos)
        wb = self.zip.read("xl/workbook.xml").decode("utf-8")
        wb = re.sub(r"<calcPr[^>]*/>",
                    '<calcPr calcId="0" fullCalcOnLoad="1"/>', wb)
        if "<calcPr" not in wb:
            wb = wb.replace("</workbook>",
                            '<calcPr calcId="0" fullCalcOnLoad="1"/></workbook>')
        replaced = {
            "xl/" + self._sheet_file: self._sheet_xml.encode("utf-8"),
            "xl/workbook.xml": wb.encode("utf-8"),
        }
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in self.zip.infolist():
                data = replaced.get(item.filename)
                if data is None:
                    data = self.zip.read(item.filename)
                zout.writestr(item, data)
