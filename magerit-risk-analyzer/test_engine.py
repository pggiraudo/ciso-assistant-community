"""Pruebas mínimas del motor de análisis Magerit.

Ejecutar con:  python3 test_engine.py
"""

from magerit import catalog, engine, excel
from magerit.engine import Asset
from magerit.sample_data import SAMPLE_ASSETS


def test_five_dimensions_defined():
    assert set(catalog.DIMENSIONS) == {"C", "I", "D", "A", "T"}


def test_score_to_level():
    assert engine.score_to_level(0) == "Muy Bajo"
    assert engine.score_to_level(4) == "Muy Bajo"
    assert engine.score_to_level(8) == "Bajo"
    assert engine.score_to_level(12) == "Medio"
    assert engine.score_to_level(16) == "Alto"
    assert engine.score_to_level(25) == "Muy Alto"


def test_asset_without_value_generates_no_risk():
    a = Asset("X", "Vacío", "S", C=0, I=0, D=0, A=0, T=0)
    assert engine.analyze_asset(a) == []


def test_safeguards_reduce_residual_risk():
    base = Asset("S1", "Servicio", "S", C=5, I=5, D=5, A=5, T=5,
                 safeguard_maturity="L0 - Inexistente")
    hardened = Asset("S2", "Servicio", "S", C=5, I=5, D=5, A=5, T=5,
                     safeguard_maturity="L5 - Optimizado")
    base_risk = sum(r.residual_score for r in engine.analyze_asset(base))
    hard_risk = sum(r.residual_score for r in engine.analyze_asset(hardened))
    assert hard_risk < base_risk


def test_validation_detects_all_dimensions_covered():
    val = engine.validate_dimensions(SAMPLE_ASSETS)
    assert all(info["covered"] for info in val["per_dimension"].values())


def test_excel_export_produces_bytes():
    risks = engine.analyze(SAMPLE_ASSETS)
    data = excel.to_bytes("Demo", SAMPLE_ASSETS, risks)
    assert data[:2] == b"PK"  # xlsx es un zip
    assert len(data) > 5000


def test_threats_map_to_iso_and_ens():
    for t in catalog.THREATS:
        assert t["iso27001"], f"{t['code']} sin controles ISO"
        assert t["ens"], f"{t['code']} sin medidas ENS"
        assert set(t["dimensions"]).issubset(set(catalog.DIMENSIONS))
        assert set(t["asset_types"]).issubset(set(catalog.ASSET_TYPES))


if __name__ == "__main__":
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS  {name}")
            passed += 1
    print(f"\n{passed} pruebas superadas.")
