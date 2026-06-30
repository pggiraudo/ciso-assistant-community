# 🛡️ Analizador de Riesgos MAGERIT — ISO 27001 & ENS

Aplicación en **Python / Streamlit** para realizar un **análisis de riesgos**
de una empresa siguiendo la metodología **MAGERIT v3**, alineada con
**ISO/IEC 27001:2022** y el **Esquema Nacional de Seguridad (RD 311/2022)**.

> **El usuario solo tiene que introducir los activos.** La aplicación identifica
> automáticamente las amenazas aplicables, calcula el riesgo intrínseco y
> residual, valida las **5 dimensiones de seguridad** y propone los controles
> ISO 27001 y medidas del ENS, exportando todo a **Excel**.

---

## ✨ Características

- **Entrada mínima**: el usuario solo introduce sus activos y los valora en las
  5 dimensiones (escala 0–5). El resto es automático.
- **Las 5 dimensiones de seguridad** (Magerit / ENS):
  - **C** — Confidencialidad
  - **I** — Integridad
  - **D** — Disponibilidad
  - **A** — Autenticidad
  - **T** — Trazabilidad
- **Catálogo MAGERIT v3** de tipos de activos y amenazas
  (`[N]` desastres naturales, `[I]` origen industrial, `[E]` errores,
  `[A]` ataques intencionados).
- **Modelo completo**: riesgo **intrínseco** y **residual** (aplicando la
  madurez de las salvaguardas, modelo CMMI L0–L5).
- **Validación de las 5 dimensiones**: comprueba que todas estén cubiertas y
  muestra el riesgo máximo por dimensión.
- **Mapeo a ISO 27001:2022 (Anexo A)** y **medidas del ENS (RD 311/2022)** por
  cada amenaza.
- **Exportación a Excel** con varias hojas (resumen ejecutivo, inventario,
  registro de riesgos coloreado, validación de dimensiones y controles).
- Carga de cartera de ejemplo, importación/exportación CSV.

---

## 🚀 Instalación y ejecución

```bash
cd magerit-risk-analyzer

# (recomendado) entorno virtual
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Se abrirá en el navegador (por defecto `http://localhost:8501`).

---

## 📋 Cómo se usa

1. **Introduce tus activos** en la tabla (o pulsa *Cargar ejemplo (PYME)* / importa un CSV).
   - Indica el **tipo** de activo (Magerit) y valora cada dimensión de **0 a 5**.
   - Opcionalmente, indica la **madurez de las salvaguardas** actuales (reduce el riesgo residual).
2. Pulsa **🚀 Calcular análisis de riesgos**.
3. Revisa la **distribución de riesgo**, la **validación de las 5 dimensiones**,
   el **registro de riesgos** y los **controles recomendados**.
4. Pulsa **⬇️ Descargar análisis en Excel**.

### Escala de valoración (0–5)

| Valor | Nivel |
|-------|-------|
| 0 | N/A — No aplica / Despreciable |
| 1 | Muy Bajo |
| 2 | Bajo |
| 3 | Medio |
| 4 | Alto |
| 5 | Muy Alto |

---

## 🧮 Modelo de cálculo

Modelo cualitativo y trazable (niveles 1–5):

```
Impacto            = f(valor del activo en las dimensiones afectadas, degradación de la amenaza)
Riesgo intrínseco  = Impacto (1-5) × Probabilidad (1-5)      → 1-25
Riesgo residual    = Riesgo intrínseco × (1 − eficacia de las salvaguardas)
```

Niveles de riesgo: **Muy Bajo** (≤4) · **Bajo** (≤8) · **Medio** (≤12) ·
**Alto** (≤16) · **Muy Alto** (>16).

Eficacia de salvaguardas según madurez (CMMI): L0 = 0 %, L1 = 10 %, L2 = 30 %,
L3 = 50 %, L4 = 75 %, L5 = 95 %.

---

## 📁 Estructura

```
magerit-risk-analyzer/
├── app.py                 # Interfaz Streamlit
├── requirements.txt
├── README.md
└── magerit/
    ├── catalog.py         # Dimensiones, tipos de activo, amenazas y mapeos ISO/ENS
    ├── engine.py          # Motor de cálculo (intrínseco y residual) + validación
    ├── excel.py           # Exportación a Excel (.xlsx)
    └── sample_data.py     # Cartera de activos de ejemplo
```

---

## ⚠️ Aviso

Herramienta de **apoyo**. Los catálogos de amenazas y los mapeos a ISO 27001 /
ENS son **orientativos** y deben ser revisados y adaptados por un analista de
seguridad antes de su uso formal en un proceso de certificación o cumplimiento.

Referencias: MAGERIT v3 (Libros I, II y III), UNE-EN ISO/IEC 27001:2022,
Real Decreto 311/2022 (ENS).
