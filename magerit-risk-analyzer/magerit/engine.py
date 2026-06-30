"""Motor de cálculo de riesgos según la metodología Magerit v3.

Flujo:
  1. El usuario aporta los activos con su valoración en las 5 dimensiones
     (C, I, D, A, T) en una escala 0..5.
  2. Para cada activo se expanden las amenazas aplicables a su tipo
     (catálogo Magerit).
  3. Para cada par (activo, amenaza) se calcula:
       - Impacto    = f(valor del activo en las dimensiones afectadas,
                        degradación de la amenaza)
       - Riesgo intrínseco = matriz Impacto x Probabilidad
       - Riesgo residual   = riesgo intrínseco reducido por la eficacia
                             de las salvaguardas implantadas.

El modelo es cualitativo (niveles 1..5) y trazable, de forma que el
resultado sea explicable y exportable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import catalog


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------
@dataclass
class Asset:
    """Activo aportado por el usuario.

    Las valoraciones C/I/D/A/T van de 0 (no aplica) a 5 (muy alto).
    """

    asset_id: str
    name: str
    asset_type: str  # clave en catalog.ASSET_TYPES
    owner: str = ""
    description: str = ""
    C: int = 0
    I: int = 0
    D: int = 0
    A: int = 0
    T: int = 0
    safeguard_maturity: str = "L0 - Inexistente"

    def dimension_value(self, dim: str) -> int:
        return int(getattr(self, dim, 0) or 0)

    def max_value(self) -> int:
        return max(self.dimension_value(d) for d in catalog.DIMENSIONS)


@dataclass
class RiskItem:
    """Resultado del análisis para un par (activo, amenaza)."""

    asset: Asset
    threat: dict
    affected_dimensions: list[str]
    asset_value: int          # valor relevante del activo (1..5)
    degradation: float        # 0..1
    probability: int          # 1..5
    impact: int               # 1..5
    intrinsic_score: int      # 1..25
    intrinsic_level: str
    safeguard_efficacy: float  # 0..1
    residual_score: float     # 0..25
    residual_level: str
    iso27001: list[str] = field(default_factory=list)
    ens: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Funciones de nivel
# ---------------------------------------------------------------------------
def score_to_level(score: float) -> str:
    """Convierte una puntuación de riesgo (0..25) a nivel cualitativo."""
    if score <= 0:
        return "Muy Bajo"
    if score <= 4:
        return "Muy Bajo"
    if score <= 8:
        return "Bajo"
    if score <= 12:
        return "Medio"
    if score <= 16:
        return "Alto"
    return "Muy Alto"


def compute_impact(asset_value: int, degradation: float) -> int:
    """Impacto (1..5) = valor del activo degradado por la amenaza.

    Si el activo no tiene valor en las dimensiones afectadas, el impacto es 0
    (la amenaza no es relevante para ese activo).
    """
    if asset_value <= 0 or degradation <= 0:
        return 0
    impact = asset_value * degradation
    return max(1, min(5, round(impact)))


def relevant_asset_value(asset: Asset, dimensions: list[str]) -> tuple[int, list[str]]:
    """Valor del activo en las dimensiones afectadas por la amenaza.

    Se toma el máximo valor entre las dimensiones afectadas y se devuelven
    las dimensiones que efectivamente están valoradas (>0).
    """
    valued = [(asset.dimension_value(d), d) for d in dimensions]
    affected = [d for v, d in valued if v > 0]
    value = max((v for v, _ in valued), default=0)
    return value, affected


# ---------------------------------------------------------------------------
# Análisis
# ---------------------------------------------------------------------------
def analyze_asset(asset: Asset) -> list[RiskItem]:
    """Genera la lista de riesgos para un activo."""
    items: list[RiskItem] = []
    efficacy = catalog.SAFEGUARD_MATURITY.get(asset.safeguard_maturity, 0.0)

    for threat in catalog.threats_for_asset_type(asset.asset_type):
        value, affected = relevant_asset_value(asset, threat["dimensions"])
        if value <= 0 or not affected:
            # La amenaza no afecta a ninguna dimensión valorada de este activo.
            continue

        degradation = float(threat["degradation"])
        probability = int(threat["prob"])
        impact = compute_impact(value, degradation)
        if impact <= 0:
            continue

        intrinsic_score = impact * probability
        intrinsic_level = score_to_level(intrinsic_score)

        residual_score = intrinsic_score * (1.0 - efficacy)
        residual_level = score_to_level(residual_score)

        items.append(
            RiskItem(
                asset=asset,
                threat=threat,
                affected_dimensions=affected,
                asset_value=value,
                degradation=degradation,
                probability=probability,
                impact=impact,
                intrinsic_score=intrinsic_score,
                intrinsic_level=intrinsic_level,
                safeguard_efficacy=efficacy,
                residual_score=round(residual_score, 1),
                residual_level=residual_level,
                iso27001=list(threat.get("iso27001", [])),
                ens=list(threat.get("ens", [])),
            )
        )
    return items


def analyze(assets: list[Asset]) -> list[RiskItem]:
    """Analiza una cartera de activos y devuelve el registro de riesgos."""
    risks: list[RiskItem] = []
    for asset in assets:
        risks.extend(analyze_asset(asset))
    return risks


# ---------------------------------------------------------------------------
# Validación de las 5 dimensiones
# ---------------------------------------------------------------------------
def validate_dimensions(assets: list[Asset]) -> dict:
    """Valida la cobertura de las 5 dimensiones de seguridad.

    Devuelve, por dimensión: cuántos activos la tienen valorada (>0), el valor
    máximo y medio, y una lista de avisos (activos sin ninguna dimensión
    valorada, etc.).
    """
    result: dict = {"per_dimension": {}, "warnings": []}

    for dim, dim_name in catalog.DIMENSIONS.items():
        values = [a.dimension_value(dim) for a in assets]
        valued = [v for v in values if v > 0]
        result["per_dimension"][dim] = {
            "name": dim_name,
            "assets_valued": len(valued),
            "total_assets": len(assets),
            "max": max(values) if values else 0,
            "avg": round(sum(valued) / len(valued), 2) if valued else 0.0,
            "covered": len(valued) > 0,
        }

    for asset in assets:
        if asset.max_value() <= 0:
            result["warnings"].append(
                f"El activo '{asset.name}' ({asset.asset_id}) no tiene ninguna "
                f"dimensión valorada (>0); quedará fuera del análisis."
            )

    missing = [
        catalog.DIMENSIONS[d]
        for d, info in result["per_dimension"].items()
        if not info["covered"]
    ]
    if missing:
        result["warnings"].append(
            "Ninguna valoración encontrada para la(s) dimensión(es): "
            + ", ".join(missing)
            + ". Revisa si aplican a tu organización."
        )

    return result


# ---------------------------------------------------------------------------
# Resúmenes
# ---------------------------------------------------------------------------
_LEVEL_ORDER = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"]


def summary_by_level(risks: list[RiskItem], residual: bool = False) -> dict[str, int]:
    """Cuenta de riesgos por nivel (intrínseco o residual)."""
    counts = {lvl: 0 for lvl in _LEVEL_ORDER}
    for r in risks:
        lvl = r.residual_level if residual else r.intrinsic_level
        counts[lvl] = counts.get(lvl, 0) + 1
    return counts


def summary_by_dimension(risks: list[RiskItem], residual: bool = False) -> dict[str, float]:
    """Riesgo máximo por dimensión de seguridad."""
    out = {d: 0.0 for d in catalog.DIMENSIONS}
    for r in risks:
        score = r.residual_score if residual else r.intrinsic_score
        for d in r.affected_dimensions:
            out[d] = max(out[d], score)
    return out


def top_risks(risks: list[RiskItem], n: int = 10, residual: bool = False) -> list[RiskItem]:
    """Devuelve los N riesgos más altos."""
    key = (lambda r: r.residual_score) if residual else (lambda r: r.intrinsic_score)
    return sorted(risks, key=key, reverse=True)[:n]


def recommended_controls(risks: list[RiskItem], min_level: str = "Medio") -> dict:
    """Agrega los controles ISO 27001 y medidas ENS recomendados.

    Solo se consideran los riesgos cuyo nivel residual sea >= min_level.
    Devuelve un diccionario con conteos por control/medida.
    """
    threshold = _LEVEL_ORDER.index(min_level)
    iso_counts: dict[str, int] = {}
    ens_counts: dict[str, int] = {}

    for r in risks:
        if _LEVEL_ORDER.index(r.residual_level) < threshold:
            continue
        for c in r.iso27001:
            iso_counts[c] = iso_counts.get(c, 0) + 1
        for m in r.ens:
            ens_counts[m] = ens_counts.get(m, 0) + 1

    return {
        "iso27001": dict(sorted(iso_counts.items(), key=lambda x: (-x[1], x[0]))),
        "ens": dict(sorted(ens_counts.items(), key=lambda x: (-x[1], x[0]))),
    }
