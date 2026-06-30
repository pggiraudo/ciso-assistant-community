"""Analizador de Riesgos MAGERIT - ISO 27001 & ENS.

Aplicación Streamlit. El usuario solo tiene que introducir los activos (con su
valoración en las 5 dimensiones de seguridad). La aplicación:

  - Expande automáticamente las amenazas Magerit aplicables a cada activo.
  - Calcula el riesgo intrínseco y residual.
  - Valida las 5 dimensiones de seguridad (C, I, D, A, T).
  - Mapea los riesgos a controles ISO/IEC 27001:2022 y medidas del ENS.
  - Exporta todo a Excel.

Ejecución:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from magerit import catalog, engine, excel
from magerit.engine import Asset
from magerit.sample_data import SAMPLE_ASSETS

st.set_page_config(
    page_title="Analizador de Riesgos MAGERIT · ISO 27001 & ENS",
    page_icon="🛡️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Utilidades de conversión DataFrame <-> Asset
# ---------------------------------------------------------------------------
ASSET_TYPE_LABELS = list(catalog.ASSET_TYPES.values())
LABEL_TO_KEY = {v: k for k, v in catalog.ASSET_TYPES.items()}
KEY_TO_LABEL = dict(catalog.ASSET_TYPES)
MATURITY_OPTIONS = list(catalog.SAFEGUARD_MATURITY.keys())

COLUMNS = [
    "ID", "Activo", "Tipo", "Responsable", "Descripción",
    "C", "I", "D", "A", "T", "Salvaguardas",
]


def assets_to_df(assets: list[Asset]) -> pd.DataFrame:
    rows = []
    for a in assets:
        rows.append({
            "ID": a.asset_id,
            "Activo": a.name,
            "Tipo": KEY_TO_LABEL.get(a.asset_type, ASSET_TYPE_LABELS[0]),
            "Responsable": a.owner,
            "Descripción": a.description,
            "C": a.C, "I": a.I, "D": a.D, "A": a.A, "T": a.T,
            "Salvaguardas": a.safeguard_maturity,
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def empty_df(n: int = 5) -> pd.DataFrame:
    rows = [{
        "ID": "", "Activo": "", "Tipo": ASSET_TYPE_LABELS[0],
        "Responsable": "", "Descripción": "",
        "C": 0, "I": 0, "D": 0, "A": 0, "T": 0,
        "Salvaguardas": MATURITY_OPTIONS[0],
    } for _ in range(n)]
    return pd.DataFrame(rows, columns=COLUMNS)


def _clean_int(value, default: int = 0) -> int:
    try:
        v = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(0, min(5, v))


def df_to_assets(df: pd.DataFrame) -> list[Asset]:
    assets: list[Asset] = []
    for idx, row in df.iterrows():
        name = str(row.get("Activo", "") or "").strip()
        if not name:
            continue  # fila vacía
        asset_type_label = str(row.get("Tipo", ASSET_TYPE_LABELS[0]))
        asset_type = LABEL_TO_KEY.get(asset_type_label, "S")
        maturity = str(row.get("Salvaguardas", MATURITY_OPTIONS[0]))
        if maturity not in catalog.SAFEGUARD_MATURITY:
            maturity = MATURITY_OPTIONS[0]
        asset_id = str(row.get("ID", "") or "").strip() or f"A-{idx + 1:02d}"
        assets.append(Asset(
            asset_id=asset_id,
            name=name,
            asset_type=asset_type,
            owner=str(row.get("Responsable", "") or "").strip(),
            description=str(row.get("Descripción", "") or "").strip(),
            C=_clean_int(row.get("C")),
            I=_clean_int(row.get("I")),
            D=_clean_int(row.get("D")),
            A=_clean_int(row.get("A")),
            T=_clean_int(row.get("T")),
            safeguard_maturity=maturity,
        ))
    return assets


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
if "assets_df" not in st.session_state:
    st.session_state.assets_df = empty_df(0)

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🛡️ Configuración")
    company = st.text_input("Organización", value="Mi Empresa, S.L.")

    st.markdown("### Valoración automática")
    default_criticality = st.select_slider(
        "Criticidad de negocio por defecto",
        options=["Baja", "Media", "Alta"],
        value="Media",
        help="La app valora las 5 dimensiones según el tipo de activo y esta criticidad.",
    )
    default_maturity = st.selectbox(
        "Madurez de salvaguardas por defecto",
        options=MATURITY_OPTIONS,
        index=MATURITY_OPTIONS.index(catalog.DEFAULT_SAFEGUARD_MATURITY),
        help="Nivel de madurez actual de las salvaguardas (reduce el riesgo residual).",
    )

    st.markdown("### Cargar activos")
    if st.button("📋 Cargar ejemplo (PYME)", use_container_width=True):
        st.session_state.assets_df = assets_to_df(SAMPLE_ASSETS)
        st.rerun()
    if st.button("🧹 Vaciar tabla", use_container_width=True):
        st.session_state.assets_df = empty_df()
        st.rerun()

    uploaded = st.file_uploader("Importar CSV de activos", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = "" if col in ("ID", "Activo", "Responsable", "Descripción") else 0
            st.session_state.assets_df = df[COLUMNS]
            st.success("CSV cargado.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudo leer el CSV: {exc}")

    st.download_button(
        "⬇️ Plantilla CSV",
        data=empty_df(0).to_csv(index=False).encode("utf-8"),
        file_name="plantilla_activos.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("ℹ️ Escala de valoración (0-5)"):
        for k, v in catalog.VALUE_LEVELS.items():
            st.markdown(f"**{k}** · {v}")

# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------
st.title("Analizador de Riesgos MAGERIT")
st.caption(
    "ISO/IEC 27001:2022 · Esquema Nacional de Seguridad (RD 311/2022) · "
    "Metodología MAGERIT v3 · Validación de las 5 dimensiones C-I-D-A-T"
)

st.markdown(
    "**Solo tienes que escribir tus activos** (uno por línea). La aplicación deduce "
    "el tipo, **calcula automáticamente las 5 dimensiones de seguridad** (C-I-D-A-T), "
    "identifica las amenazas y calcula el **riesgo inherente** y el **riesgo residual**."
)

# ---------------------------------------------------------------------------
# 1. Entrada rápida de activos (uno por línea)
# ---------------------------------------------------------------------------
st.subheader("1️⃣ Escribe tus activos")

st.markdown(
    "Escribe **un activo por línea**. Puedes pegar una lista entera de golpe. "
    "Opcionalmente puedes precisar el tipo y la criticidad separando con `|`:  "
    "`Nombre | Tipo | Criticidad`."
)

quick_text = st.text_area(
    "Activos (uno por línea)",
    height=160,
    placeholder=(
        "Servidor principal\n"
        "Base de datos de clientes\n"
        "ERP corporativo\n"
        "Correo electrónico\n"
        "Copias de seguridad\n"
        "Red corporativa y WiFi\n"
        "Servicio de facturación online | S | Alta"
    ),
)
cqa, cqb = st.columns(2)
if cqa.button("🔄 Generar tabla (reemplazar)", use_container_width=True, type="primary"):
    new_assets = engine.assets_from_lines(quick_text, default_criticality, default_maturity)
    if new_assets:
        st.session_state.assets_df = assets_to_df(new_assets)
        st.rerun()
    else:
        st.warning("Escribe al menos un activo (una línea con texto).")
if cqb.button("➕ Añadir a la tabla", use_container_width=True):
    new_assets = engine.assets_from_lines(quick_text, default_criticality, default_maturity)
    if new_assets:
        combined = pd.concat(
            [st.session_state.assets_df, assets_to_df(new_assets)], ignore_index=True)
        st.session_state.assets_df = combined
        st.rerun()
    else:
        st.warning("Escribe al menos un activo (una línea con texto).")

st.info(
    "💡 Tipos que detecta automáticamente: servidor/portátil→Hardware, "
    "base de datos/documentación→Datos, ERP/correo/web→Aplicaciones, "
    "red/WiFi/firewall→Comunicaciones, copia de seguridad→Soportes, "
    "oficina/CPD→Instalaciones, personal→Personal, servicio/facturación→Servicios. "
    "Puedes corregir el tipo y los valores en la tabla de abajo.",
    icon="ℹ️",
)

# ---------------------------------------------------------------------------
# 2. Tabla de activos (revisar / ajustar) — valoración ya calculada
# ---------------------------------------------------------------------------
st.subheader("2️⃣ Revisa y ajusta (opcional)")

with st.expander("¿Qué significan las 5 dimensiones?"):
    cols = st.columns(5)
    for col, (dim, name) in zip(cols, catalog.DIMENSIONS.items()):
        col.markdown(f"**{dim} · {name}**")
        col.caption(catalog.DIMENSION_DESCRIPTIONS[dim])

st.caption(
    "Los valores C-I-D-A-T ya están calculados automáticamente. Solo edítalos si "
    "quieres afinarlos."
)

edited_df = st.data_editor(
    st.session_state.assets_df,
    num_rows="dynamic",
    use_container_width=True,
    key="asset_editor",
    column_config={
        "ID": st.column_config.TextColumn("ID", width="small"),
        "Activo": st.column_config.TextColumn("Activo", required=False, width="medium"),
        "Tipo": st.column_config.SelectboxColumn(
            "Tipo (Magerit)", options=ASSET_TYPE_LABELS, width="medium"),
        "Responsable": st.column_config.TextColumn("Responsable", width="small"),
        "Descripción": st.column_config.TextColumn("Descripción", width="large"),
        "C": st.column_config.NumberColumn("C", min_value=0, max_value=5, step=1, width="small",
                                           help="Confidencialidad (0-5)"),
        "I": st.column_config.NumberColumn("I", min_value=0, max_value=5, step=1, width="small",
                                           help="Integridad (0-5)"),
        "D": st.column_config.NumberColumn("D", min_value=0, max_value=5, step=1, width="small",
                                           help="Disponibilidad (0-5)"),
        "A": st.column_config.NumberColumn("A", min_value=0, max_value=5, step=1, width="small",
                                           help="Autenticidad (0-5)"),
        "T": st.column_config.NumberColumn("T", min_value=0, max_value=5, step=1, width="small",
                                           help="Trazabilidad (0-5)"),
        "Salvaguardas": st.column_config.SelectboxColumn(
            "Madurez salvaguardas", options=MATURITY_OPTIONS, width="medium",
            help="Nivel de madurez actual de las salvaguardas (reduce el riesgo residual)"),
    },
)
st.session_state.assets_df = edited_df

assets = df_to_assets(edited_df)
st.caption(f"Activos válidos detectados: **{len(assets)}**")

# ---------------------------------------------------------------------------
# 3. Análisis
# ---------------------------------------------------------------------------
st.subheader("3️⃣ Análisis de riesgos")
run = st.button("🚀 Calcular análisis de riesgos", type="primary", use_container_width=True)

if run:
    if not assets:
        st.warning("Escribe al menos un activo en el paso 1 y pulsa «Generar tabla».")
    else:
        st.session_state.risks = engine.analyze(assets)
        st.session_state.analyzed_assets = assets
        st.session_state.company = company

if st.session_state.get("risks") and st.session_state.get("analyzed_assets"):
    risks = st.session_state.risks
    analyzed_assets = st.session_state.analyzed_assets
    company = st.session_state.get("company", company)

    if not risks:
        st.warning(
            "No se generaron escenarios de riesgo. Asegúrate de valorar (>0) las "
            "dimensiones de tus activos."
        )
    else:
        # --- Métricas ---
        intr = engine.summary_by_level(risks, residual=False)
        resid = engine.summary_by_level(risks, residual=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Escenarios de riesgo", len(risks))
        c2.metric("Riesgo Alto/Muy Alto (inherente)",
                  intr["Alto"] + intr["Muy Alto"])
        c3.metric("Riesgo Alto/Muy Alto (residual)",
                  resid["Alto"] + resid["Muy Alto"],
                  delta=(resid["Alto"] + resid["Muy Alto"]) - (intr["Alto"] + intr["Muy Alto"]))
        c4.metric("Activos analizados", len(analyzed_assets))

        # --- Distribución por nivel ---
        st.markdown("#### Distribución por nivel de riesgo")
        dist = pd.DataFrame({
            "Inherente": intr,
            "Residual": resid,
        }).reindex(["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"])
        st.bar_chart(dist)

        # --- Validación 5 dimensiones ---
        st.markdown("#### ✅ Validación de las 5 dimensiones de seguridad")
        validation = engine.validate_dimensions(analyzed_assets)
        risk_by_dim = engine.summary_by_dimension(risks, residual=True)
        dim_rows = []
        for dim, info in validation["per_dimension"].items():
            dim_rows.append({
                "Dim.": dim,
                "Dimensión": info["name"],
                "Activos valorados": f"{info['assets_valued']} / {info['total_assets']}",
                "Valor máx.": info["max"],
                "Valor medio": info["avg"],
                "Riesgo residual máx.": round(risk_by_dim.get(dim, 0.0), 1),
                "Cubierta": "✅" if info["covered"] else "❌",
            })
        st.dataframe(pd.DataFrame(dim_rows), use_container_width=True, hide_index=True)
        for w in validation["warnings"]:
            st.warning(w)

        # --- Registro de riesgos ---
        st.markdown("#### Registro de riesgos")
        risk_rows = []
        for r in risks:
            risk_rows.append({
                "Activo": r.asset.name,
                "Amenaza": f"[{r.threat['code']}] {r.threat['name']}",
                "Dimensiones": ", ".join(r.affected_dimensions),
                "Prob.": r.probability,
                "Impacto": r.impact,
                "R. inherente": r.intrinsic_score,
                "Nivel inher.": r.intrinsic_level,
                "Eficacia salv. %": round(r.safeguard_efficacy * 100),
                "R. residual": r.residual_score,
                "Nivel resid.": r.residual_level,
                "ISO 27001": ", ".join(r.iso27001),
                "ENS": ", ".join(r.ens),
            })
        risk_df = pd.DataFrame(risk_rows)

        level_filter = st.multiselect(
            "Filtrar por nivel de riesgo residual",
            options=["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"],
            default=["Muy Alto", "Alto", "Medio"],
        )
        shown = risk_df[risk_df["Nivel resid."].isin(level_filter)] if level_filter else risk_df

        def _color(val):
            colors = {"Muy Bajo": "#C6EFCE", "Bajo": "#A9D08E", "Medio": "#FFEB9C",
                      "Alto": "#F8CBAD", "Muy Alto": "#FF7C80"}
            return f"background-color: {colors.get(val, '')}"

        st.dataframe(
            shown.style.map(_color, subset=["Nivel inher.", "Nivel resid."]),
            use_container_width=True, hide_index=True, height=420,
        )

        # --- Controles recomendados ---
        st.markdown("#### 🛠️ Controles y medidas recomendados (riesgo residual ≥ Medio)")
        rec = engine.recommended_controls(risks, min_level="Medio")
        col_iso, col_ens = st.columns(2)
        with col_iso:
            st.markdown("**ISO/IEC 27001:2022 (Anexo A)**")
            if rec["iso27001"]:
                st.dataframe(
                    pd.DataFrame(
                        [{"Control": k, "Nº riesgos": v} for k, v in rec["iso27001"].items()]),
                    use_container_width=True, hide_index=True, height=300,
                )
            else:
                st.info("Sin riesgos relevantes.")
        with col_ens:
            st.markdown("**ENS - RD 311/2022 (Anexo II)**")
            if rec["ens"]:
                st.dataframe(
                    pd.DataFrame(
                        [{"Medida": k, "Nº riesgos": v} for k, v in rec["ens"].items()]),
                    use_container_width=True, hide_index=True, height=300,
                )
            else:
                st.info("Sin riesgos relevantes.")

        # --- Exportar Excel ---
        st.subheader("4️⃣ Exportar")
        xlsx = excel.to_bytes(company, analyzed_assets, risks)
        st.download_button(
            "⬇️ Descargar análisis en Excel (.xlsx)",
            data=xlsx,
            file_name=f"analisis_riesgos_magerit_{company.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

st.divider()
st.caption(
    "Modelo cualitativo de apoyo basado en MAGERIT v3. Los catálogos de amenazas "
    "y los mapeos a ISO 27001 / ENS son orientativos y deben ser revisados por un "
    "analista de seguridad antes de su uso formal."
)
