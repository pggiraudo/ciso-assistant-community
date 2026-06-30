"""Catálogo de elementos Magerit v3.

Contiene:
  - Las 5 dimensiones de seguridad (C, I, D, A, T).
  - Los tipos de activos (Magerit Libro II).
  - El catálogo de amenazas con las dimensiones que afectan, los tipos de
    activo a los que aplican, su probabilidad y degradación por defecto.
  - El mapeo de cada amenaza a controles de ISO/IEC 27001:2022 (Anexo A)
    y a medidas del Esquema Nacional de Seguridad (RD 311/2022).

Referencias:
  - MAGERIT v3 - Libro II: Catálogo de Elementos (CCN / Ministerio de Hacienda).
  - UNE-EN ISO/IEC 27001:2022 - Anexo A.
  - Real Decreto 311/2022 (ENS) - Anexo II: Medidas de seguridad.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Las 5 dimensiones de seguridad (Magerit / ENS)
# ---------------------------------------------------------------------------
DIMENSIONS: dict[str, str] = {
    "C": "Confidencialidad",
    "I": "Integridad",
    "D": "Disponibilidad",
    "A": "Autenticidad",
    "T": "Trazabilidad",
}

DIMENSION_DESCRIPTIONS: dict[str, str] = {
    "C": "Garantía de que la información es accesible solo a quien está autorizado.",
    "I": "Garantía de exactitud y completitud de la información y su procesado.",
    "D": "Garantía de acceso y uso de la información y los sistemas cuando se requiere.",
    "A": "Garantía de que una entidad es quien dice ser o garantiza la fuente de los datos.",
    "T": "Garantía de que las actuaciones de una entidad pueden ser imputadas a ella.",
}

# ---------------------------------------------------------------------------
# Tipos de activos (Magerit Libro II - capítulo de Tipos de activos)
# ---------------------------------------------------------------------------
ASSET_TYPES: dict[str, str] = {
    "S": "[S] Servicios",
    "D": "[D] Datos / Información",
    "SW": "[SW] Aplicaciones (software)",
    "HW": "[HW] Equipos informáticos (hardware)",
    "COM": "[COM] Redes de comunicaciones",
    "Media": "[Media] Soportes de información",
    "AUX": "[AUX] Equipamiento auxiliar",
    "L": "[L] Instalaciones",
    "P": "[P] Personal",
}

# ---------------------------------------------------------------------------
# Grupos de amenazas (Magerit Libro II - capítulo de Amenazas)
# ---------------------------------------------------------------------------
THREAT_GROUPS: dict[str, str] = {
    "N": "[N] Desastres naturales",
    "I": "[I] De origen industrial",
    "E": "[E] Errores y fallos no intencionados",
    "A": "[A] Ataques intencionados",
}

# ---------------------------------------------------------------------------
# Escalas (alineadas con ENS / Magerit, niveles 0..5)
# ---------------------------------------------------------------------------
VALUE_LEVELS: dict[int, str] = {
    0: "N/A - No aplica / Despreciable",
    1: "Muy Bajo",
    2: "Bajo",
    3: "Medio",
    4: "Alto",
    5: "Muy Alto",
}

PROBABILITY_LEVELS: dict[int, str] = {
    1: "Muy Baja",
    2: "Baja",
    3: "Media",
    4: "Alta",
    5: "Muy Alta",
}

RISK_LEVELS: dict[str, str] = {
    "Muy Bajo": "Riesgo asumible. Mantener vigilancia.",
    "Bajo": "Riesgo bajo. Tratar según disponibilidad de recursos.",
    "Medio": "Riesgo a tratar. Planificar salvaguardas.",
    "Alto": "Riesgo elevado. Requiere tratamiento prioritario.",
    "Muy Alto": "Riesgo crítico. Tratamiento inmediato e ineludible.",
}

# Madurez de las salvaguardas (modelo CMMI usado por Magerit) -> eficacia
SAFEGUARD_MATURITY: dict[str, float] = {
    "L0 - Inexistente": 0.00,
    "L1 - Inicial / ad hoc": 0.10,
    "L2 - Reproducible pero intuitivo": 0.30,
    "L3 - Proceso definido": 0.50,
    "L4 - Gestionado y medible": 0.75,
    "L5 - Optimizado": 0.95,
}

# ---------------------------------------------------------------------------
# Valoración AUTOMÁTICA de las 5 dimensiones por tipo de activo
#
# Perfil típico (C, I, D, A, T) en escala 0..5 para cada tipo de activo.
# Permite que el usuario solo tenga que introducir el activo: la aplicación
# valora por defecto las 5 dimensiones según el tipo. El usuario puede ajustar
# después cualquier valor manualmente.
# ---------------------------------------------------------------------------
ASSET_TYPE_PROFILE: dict[str, dict[str, int]] = {
    "S":     {"C": 3, "I": 4, "D": 5, "A": 3, "T": 3},  # Servicios
    "D":     {"C": 4, "I": 4, "D": 3, "A": 3, "T": 4},  # Datos / Información
    "SW":    {"C": 3, "I": 3, "D": 4, "A": 3, "T": 2},  # Aplicaciones
    "HW":    {"C": 2, "I": 2, "D": 4, "A": 1, "T": 1},  # Equipos
    "COM":   {"C": 3, "I": 3, "D": 4, "A": 2, "T": 2},  # Comunicaciones
    "Media": {"C": 3, "I": 3, "D": 4, "A": 1, "T": 1},  # Soportes
    "AUX":   {"C": 1, "I": 1, "D": 3, "A": 1, "T": 1},  # Equipamiento auxiliar
    "L":     {"C": 2, "I": 1, "D": 4, "A": 1, "T": 1},  # Instalaciones
    "P":     {"C": 3, "I": 3, "D": 3, "A": 2, "T": 2},  # Personal
}

# Ajuste del perfil según la criticidad del activo para el negocio.
CRITICALITY_ADJUST: dict[str, int] = {
    "Baja": -1,
    "Media": 0,
    "Alta": +1,
}

# Madurez de salvaguardas asignada por defecto (situación habitual de partida).
DEFAULT_SAFEGUARD_MATURITY = "L2 - Reproducible pero intuitivo"

# Palabras clave para deducir el tipo de activo a partir de su nombre.
# El orden importa: la primera coincidencia gana.
ASSET_TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Media", ["backup", "copia de seguridad", "copias de seguridad", "cinta",
               "disco extraíble", "usb", "soporte", "nas"]),
    ("COM", ["red", "wifi", "wi-fi", "firewall", "router", "switch", "vpn",
             "internet", "lan", "comunicacion", "comunicación", "enlace"]),
    ("HW", ["servidor", "ordenador", "portátil", "portatil", "pc", "equipo",
            "estación", "estacion", "móvil", "movil", "smartphone", "tablet",
            "impresora", "hardware", "cabina"]),
    ("SW", ["aplicación", "aplicacion", "app", "software", "erp", "crm",
            "programa", "correo", "email", "e-mail", "ofimática", "ofimatica",
            "sistema operativo", "web", "portal", "plataforma", "antivirus"]),
    ("D", ["base de datos", "bbdd", "bd ", "datos", "información", "informacion",
           "fichero", "documentación", "documentacion", "expediente",
           "histórico", "historico", "registro", "contabilidad", "nómina",
           "nomina", "contrato"]),
    ("S", ["servicio", "facturación", "facturacion", "atención", "atencion",
           "tienda online", "ecommerce", "e-commerce", "tramitación",
           "tramitacion"]),
    ("L", ["oficina", "edificio", "sala", "cpd", "instalación", "instalacion",
           "centro de proceso", "local", "sede", "almacén", "almacen"]),
    ("AUX", ["sai", "ups", "climatización", "climatizacion", "aire acondicionado",
             "grupo electrógeno", "electrogeno", "cableado", "alimentación",
             "alimentacion", "generador"]),
    ("P", ["personal", "empleado", "administrador", "usuario", "plantilla",
           "rrhh", "equipo humano", "técnico", "tecnico", "operador"]),
]


def guess_asset_type(name: str) -> str:
    """Deduce el tipo de activo (clave en ASSET_TYPES) a partir del nombre.

    Si no encuentra ninguna palabra clave, devuelve 'D' (Datos), el tipo más
    habitual y conservador. El usuario siempre puede corregirlo.
    """
    text = (name or "").lower()
    for asset_type, keywords in ASSET_TYPE_KEYWORDS:
        if any(kw in text for kw in keywords):
            return asset_type
    return "D"


def auto_valuation(asset_type: str, criticality: str = "Media") -> dict[str, int]:
    """Devuelve la valoración automática (C, I, D, A, T) para un tipo de activo.

    Aplica el perfil del tipo de activo ajustado por la criticidad de negocio.
    """
    base = ASSET_TYPE_PROFILE.get(asset_type, ASSET_TYPE_PROFILE["D"])
    adjust = CRITICALITY_ADJUST.get(criticality, 0)
    return {d: max(0, min(5, base[d] + adjust)) for d in DIMENSIONS}


# ---------------------------------------------------------------------------
# Catálogo de amenazas
#
# Cada amenaza define:
#   code         -> código Magerit
#   name         -> nombre
#   group        -> grupo (N/I/E/A)
#   asset_types  -> tipos de activo a los que aplica
#   dimensions   -> dimensiones de seguridad afectadas
#   prob         -> probabilidad por defecto (1..5)
#   degradation  -> degradación por defecto del valor del activo (0..1)
#   iso27001     -> controles recomendados ISO/IEC 27001:2022 (Anexo A)
#   ens          -> medidas recomendadas del ENS (RD 311/2022, Anexo II)
# ---------------------------------------------------------------------------
THREATS: list[dict] = [
    # ----- [N] Desastres naturales -----
    {
        "code": "N.1", "name": "Fuego", "group": "N",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 2, "degradation": 1.0,
        "iso27001": ["A.7.5", "A.7.8", "A.7.11"],
        "ens": ["mp.if.1", "mp.if.2", "mp.if.4"],
    },
    {
        "code": "N.2", "name": "Daños por agua", "group": "N",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.8,
        "iso27001": ["A.7.5", "A.7.8"],
        "ens": ["mp.if.1", "mp.if.5"],
    },
    {
        "code": "N.*", "name": "Desastres naturales (terremoto, tormenta, etc.)",
        "group": "N",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 1, "degradation": 1.0,
        "iso27001": ["A.7.5", "A.5.30", "A.5.29"],
        "ens": ["mp.if.1", "op.cont.1", "op.cont.2"],
    },
    # ----- [I] De origen industrial -----
    {
        "code": "I.1", "name": "Fuego (origen industrial)", "group": "I",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 2, "degradation": 1.0,
        "iso27001": ["A.7.5", "A.7.8", "A.7.11"],
        "ens": ["mp.if.1", "mp.if.2", "mp.if.4"],
    },
    {
        "code": "I.2", "name": "Daños por agua (origen industrial)", "group": "I",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.8,
        "iso27001": ["A.7.5", "A.7.8"],
        "ens": ["mp.if.1", "mp.if.5"],
    },
    {
        "code": "I.5", "name": "Avería de origen físico o lógico", "group": "I",
        "asset_types": ["HW", "SW", "Media", "AUX"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.7.13", "A.8.6", "A.8.14"],
        "ens": ["mp.eq.1", "op.exp.4", "op.cont.2"],
    },
    {
        "code": "I.6", "name": "Corte del suministro eléctrico", "group": "I",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.7.11", "A.7.12"],
        "ens": ["mp.if.3", "mp.if.4"],
    },
    {
        "code": "I.7", "name": "Condiciones inadecuadas de temperatura o humedad",
        "group": "I",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.4,
        "iso27001": ["A.7.5", "A.7.8"],
        "ens": ["mp.if.4", "mp.if.7"],
    },
    {
        "code": "I.8", "name": "Fallo de servicios de comunicaciones", "group": "I",
        "asset_types": ["COM", "S"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.7,
        "iso27001": ["A.8.20", "A.8.21", "A.5.29"],
        "ens": ["mp.com.1", "op.cont.2"],
    },
    {
        "code": "I.10", "name": "Degradación de los soportes de almacenamiento",
        "group": "I",
        "asset_types": ["Media"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.5,
        "iso27001": ["A.7.10", "A.7.14", "A.8.13"],
        "ens": ["mp.si.1", "mp.si.4"],
    },
    {
        "code": "I.11", "name": "Emanaciones electromagnéticas", "group": "I",
        "asset_types": ["HW", "Media", "COM"], "dimensions": ["C"],
        "prob": 1, "degradation": 0.3,
        "iso27001": ["A.7.5", "A.7.8"],
        "ens": ["mp.if.1", "mp.com.4"],
    },
    # ----- [E] Errores y fallos no intencionados -----
    {
        "code": "E.1", "name": "Errores de los usuarios", "group": "E",
        "asset_types": ["S", "D", "SW"], "dimensions": ["C", "I", "D"],
        "prob": 4, "degradation": 0.3,
        "iso27001": ["A.6.3", "A.8.2", "A.5.10"],
        "ens": ["mp.per.3", "op.acc.2", "op.exp.1"],
    },
    {
        "code": "E.2", "name": "Errores del administrador", "group": "E",
        "asset_types": ["S", "D", "SW", "HW", "COM"], "dimensions": ["C", "I", "D"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.8.2", "A.8.9", "A.8.15"],
        "ens": ["op.acc.4", "op.exp.2", "op.exp.8"],
    },
    {
        "code": "E.3", "name": "Errores de monitorización (log)", "group": "E",
        "asset_types": ["D"], "dimensions": ["I", "T"],
        "prob": 2, "degradation": 0.4,
        "iso27001": ["A.8.15", "A.8.16"],
        "ens": ["op.exp.8", "op.mon.1"],
    },
    {
        "code": "E.4", "name": "Errores de configuración", "group": "E",
        "asset_types": ["D", "SW", "HW", "COM"], "dimensions": ["I"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.8.9", "A.8.32"],
        "ens": ["op.exp.2", "op.exp.3"],
    },
    {
        "code": "E.8", "name": "Difusión de software dañino (accidental)", "group": "E",
        "asset_types": ["SW"], "dimensions": ["C", "I", "D"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.8.7", "A.8.8"],
        "ens": ["op.exp.6", "op.exp.4"],
    },
    {
        "code": "E.14", "name": "Escapes / fugas de información (accidental)", "group": "E",
        "asset_types": ["D", "S", "SW", "Media", "P"], "dimensions": ["C"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.5.12", "A.5.13", "A.5.14", "A.8.12"],
        "ens": ["mp.info.2", "mp.com.2"],
    },
    {
        "code": "E.15", "name": "Alteración accidental de la información", "group": "E",
        "asset_types": ["D", "SW", "Media"], "dimensions": ["I"],
        "prob": 3, "degradation": 0.4,
        "iso27001": ["A.8.10", "A.8.13", "A.5.33"],
        "ens": ["mp.info.6", "mp.si.2"],
    },
    {
        "code": "E.18", "name": "Destrucción de información (accidental)", "group": "E",
        "asset_types": ["D", "SW", "Media"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.8.13", "A.8.14"],
        "ens": ["mp.info.9", "op.cont.2"],
    },
    {
        "code": "E.19", "name": "Fugas de información", "group": "E",
        "asset_types": ["D", "S", "Media", "P"], "dimensions": ["C"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.5.12", "A.5.14", "A.8.12"],
        "ens": ["mp.info.2", "mp.com.2"],
    },
    {
        "code": "E.20", "name": "Vulnerabilidades de los programas (software)", "group": "E",
        "asset_types": ["SW"], "dimensions": ["C", "I", "D"],
        "prob": 4, "degradation": 0.5,
        "iso27001": ["A.8.8", "A.8.25", "A.8.28"],
        "ens": ["op.exp.4", "mp.sw.1", "mp.sw.2"],
    },
    {
        "code": "E.21", "name": "Errores de mantenimiento/actualización de programas",
        "group": "E",
        "asset_types": ["SW"], "dimensions": ["I", "D"],
        "prob": 3, "degradation": 0.4,
        "iso27001": ["A.8.8", "A.8.19", "A.8.32"],
        "ens": ["op.exp.4", "op.exp.5"],
    },
    {
        "code": "E.23", "name": "Errores de mantenimiento/actualización de equipos (hardware)",
        "group": "E",
        "asset_types": ["HW", "Media", "AUX"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.4,
        "iso27001": ["A.7.13", "A.8.32"],
        "ens": ["mp.eq.1", "op.exp.5"],
    },
    {
        "code": "E.24", "name": "Caída del sistema por agotamiento de recursos", "group": "E",
        "asset_types": ["S", "HW", "COM"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.8.6"],
        "ens": ["op.exp.4", "op.cont.2"],
    },
    {
        "code": "E.25", "name": "Pérdida de equipos", "group": "E",
        "asset_types": ["HW", "Media", "AUX"], "dimensions": ["D", "C"],
        "prob": 2, "degradation": 0.6,
        "iso27001": ["A.7.9", "A.7.10", "A.8.1"],
        "ens": ["mp.eq.1", "mp.si.2"],
    },
    {
        "code": "E.28", "name": "Indisponibilidad del personal", "group": "E",
        "asset_types": ["P"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.4,
        "iso27001": ["A.6.1", "A.5.2", "A.5.30"],
        "ens": ["mp.per.1", "op.cont.1"],
    },
    # ----- [A] Ataques intencionados -----
    {
        "code": "A.3", "name": "Manipulación de los registros de actividad (log)",
        "group": "A",
        "asset_types": ["D"], "dimensions": ["I", "T"],
        "prob": 2, "degradation": 0.6,
        "iso27001": ["A.8.15", "A.8.16", "A.8.17"],
        "ens": ["op.exp.8", "op.exp.10", "op.mon.1"],
    },
    {
        "code": "A.5", "name": "Suplantación de la identidad del usuario", "group": "A",
        "asset_types": ["S", "SW", "COM", "D"], "dimensions": ["C", "A", "I"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.5.16", "A.5.17", "A.8.5"],
        "ens": ["op.acc.1", "op.acc.5", "op.acc.6"],
    },
    {
        "code": "A.6", "name": "Abuso de privilegios de acceso", "group": "A",
        "asset_types": ["S", "SW", "HW", "COM", "D"], "dimensions": ["C", "I", "D"],
        "prob": 3, "degradation": 0.5,
        "iso27001": ["A.8.2", "A.8.3", "A.5.18"],
        "ens": ["op.acc.3", "op.acc.4"],
    },
    {
        "code": "A.7", "name": "Uso no previsto", "group": "A",
        "asset_types": ["S", "SW", "HW", "COM"], "dimensions": ["C", "I", "D"],
        "prob": 3, "degradation": 0.4,
        "iso27001": ["A.5.10", "A.8.19"],
        "ens": ["op.exp.1", "op.exp.7"],
    },
    {
        "code": "A.8", "name": "Difusión de software dañino (malware)", "group": "A",
        "asset_types": ["SW"], "dimensions": ["C", "I", "D"],
        "prob": 4, "degradation": 0.7,
        "iso27001": ["A.8.7", "A.8.8"],
        "ens": ["op.exp.6", "op.exp.4"],
    },
    {
        "code": "A.11", "name": "Acceso no autorizado", "group": "A",
        "asset_types": ["S", "D", "SW", "HW", "COM", "Media", "L"],
        "dimensions": ["C", "I"],
        "prob": 4, "degradation": 0.6,
        "iso27001": ["A.5.15", "A.8.3", "A.8.5", "A.7.1"],
        "ens": ["op.acc.2", "op.acc.4", "mp.if.1"],
    },
    {
        "code": "A.12", "name": "Análisis de tráfico", "group": "A",
        "asset_types": ["COM"], "dimensions": ["C"],
        "prob": 2, "degradation": 0.4,
        "iso27001": ["A.8.20", "A.8.21", "A.8.24"],
        "ens": ["mp.com.2", "mp.com.3"],
    },
    {
        "code": "A.13", "name": "Repudio", "group": "A",
        "asset_types": ["S", "D"], "dimensions": ["A", "T"],
        "prob": 2, "degradation": 0.5,
        "iso27001": ["A.8.15", "A.8.16", "A.5.16"],
        "ens": ["op.exp.8", "op.acc.6"],
    },
    {
        "code": "A.14", "name": "Interceptación de información (escucha)", "group": "A",
        "asset_types": ["COM"], "dimensions": ["C"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.8.20", "A.8.24", "A.5.14"],
        "ens": ["mp.com.2", "mp.com.3"],
    },
    {
        "code": "A.15", "name": "Modificación deliberada de la información", "group": "A",
        "asset_types": ["D", "SW", "Media", "S"], "dimensions": ["I"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.8.10", "A.8.5", "A.5.33"],
        "ens": ["mp.info.6", "op.acc.4"],
    },
    {
        "code": "A.18", "name": "Destrucción de información (deliberada)", "group": "A",
        "asset_types": ["D", "SW", "Media", "S"], "dimensions": ["D"],
        "prob": 3, "degradation": 0.7,
        "iso27001": ["A.8.13", "A.8.14", "A.8.10"],
        "ens": ["mp.info.9", "op.cont.2"],
    },
    {
        "code": "A.19", "name": "Divulgación de información", "group": "A",
        "asset_types": ["D", "S", "Media", "P"], "dimensions": ["C"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.5.12", "A.5.13", "A.5.14"],
        "ens": ["mp.info.2", "mp.info.3"],
    },
    {
        "code": "A.22", "name": "Manipulación de programas", "group": "A",
        "asset_types": ["SW"], "dimensions": ["C", "I", "D"],
        "prob": 3, "degradation": 0.6,
        "iso27001": ["A.8.4", "A.8.25", "A.8.31"],
        "ens": ["mp.sw.1", "mp.sw.2", "op.exp.4"],
    },
    {
        "code": "A.23", "name": "Manipulación de los equipos", "group": "A",
        "asset_types": ["HW", "Media", "AUX"], "dimensions": ["C", "D"],
        "prob": 2, "degradation": 0.5,
        "iso27001": ["A.7.1", "A.7.8", "A.8.1"],
        "ens": ["mp.if.1", "mp.eq.1"],
    },
    {
        "code": "A.24", "name": "Denegación de servicio (DoS/DDoS)", "group": "A",
        "asset_types": ["S", "HW", "COM"], "dimensions": ["D"],
        "prob": 4, "degradation": 0.7,
        "iso27001": ["A.8.6", "A.8.20", "A.8.21"],
        "ens": ["mp.com.1", "op.cont.2"],
    },
    {
        "code": "A.25", "name": "Robo", "group": "A",
        "asset_types": ["HW", "Media", "AUX"], "dimensions": ["D", "C"],
        "prob": 3, "degradation": 0.7,
        "iso27001": ["A.7.6", "A.7.9", "A.7.10", "A.5.14"],
        "ens": ["mp.if.1", "mp.eq.1", "mp.si.2"],
    },
    {
        "code": "A.26", "name": "Ataque destructivo (vandalismo, sabotaje, terrorismo)",
        "group": "A",
        "asset_types": ["HW", "Media", "AUX", "L"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.9,
        "iso27001": ["A.7.1", "A.7.4", "A.5.29"],
        "ens": ["mp.if.1", "mp.if.6", "op.cont.2"],
    },
    {
        "code": "A.27", "name": "Ocupación enemiga", "group": "A",
        "asset_types": ["L"], "dimensions": ["D", "C"],
        "prob": 1, "degradation": 0.8,
        "iso27001": ["A.7.1", "A.7.2", "A.7.3"],
        "ens": ["mp.if.1", "mp.if.2"],
    },
    {
        "code": "A.28", "name": "Indisponibilidad del personal (deliberada)", "group": "A",
        "asset_types": ["P"], "dimensions": ["D"],
        "prob": 2, "degradation": 0.4,
        "iso27001": ["A.6.1", "A.5.2", "A.5.30"],
        "ens": ["mp.per.1", "op.cont.1"],
    },
    {
        "code": "A.29", "name": "Extorsión", "group": "A",
        "asset_types": ["P"], "dimensions": ["C", "I", "D"],
        "prob": 1, "degradation": 0.5,
        "iso27001": ["A.6.1", "A.6.4", "A.5.4"],
        "ens": ["mp.per.1", "mp.per.2"],
    },
    {
        "code": "A.30", "name": "Ingeniería social", "group": "A",
        "asset_types": ["P"], "dimensions": ["C", "I", "D"],
        "prob": 4, "degradation": 0.5,
        "iso27001": ["A.6.3", "A.5.10"],
        "ens": ["mp.per.3", "mp.per.4"],
    },
]


def threats_for_asset_type(asset_type: str) -> list[dict]:
    """Devuelve las amenazas aplicables a un tipo de activo dado."""
    return [t for t in THREATS if asset_type in t["asset_types"]]
