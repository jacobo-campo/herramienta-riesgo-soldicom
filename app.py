import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import io
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Herramienta de Riesgo – Fondo SOLDICOM",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# BRAND (colores alusivos a fondosoldicom.com)
# -----------------------------
PRIMARY = "#1A3D75"     # azul
PRIMARY_2 = "#304F83"   # azul secundario
BG = "#EFF8FE"          # fondo claro azulado
TEXT = "#0F172A"
CARD = "#FFFFFF"

st.markdown(f"""
<style>
.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

h1, h2, h3, h4 {{
    color: {PRIMARY};
}}

/* Botones */
div.stButton > button {{
    background-color: {PRIMARY};
    color: white;
    border-radius: 10px;
    border: 0px;
    padding: 0.6rem 1.0rem;
    font-weight: 600;
}}
div.stButton > button:hover {{
    background-color: {PRIMARY_2};
    color: white;
}}

/* Card */
.card {{
    background: {CARD};
    border-radius: 14px;
    padding: 18px 18px 10px 18px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.10);
    border: 1px solid rgba(15, 23, 42, 0.06);
}}

/* Separador */
.soft-hr {{
    height: 1px;
    background: rgba(15, 23, 42, 0.08);
    border: none;
    margin: 18px 0;
}}

/* Badge */
.badge {{
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 13px;
    color: white;
    background: {PRIMARY};
}}

/* =========================
   FIX: labels/preguntas de widgets
   ========================= */

/* Label arriba del widget (selectbox, number_input, etc.) */
[data-testid="stWidgetLabel"] > label,
[data-testid="stWidgetLabel"] > label p,
[data-testid="stWidgetLabel"] > label span {{
    color: #0F172A !important;   /* azul oscuro */
    font-weight: 600 !important;
    opacity: 1 !important;
}}

/* Texto markdown dentro de la app (por si Streamlit lo usa para labels) */
.stMarkdown, .stMarkdown p, .stMarkdown span {{
    color: #0F172A !important;
    opacity: 1 !important;
}}

/* Help text (si aparece) */
[data-testid="stHelp"] * {{
    color: #334155 !important;
    opacity: 1 !important;
}}

/* Fallback agresivo (por si algún label queda pálido) */
section label, section label * {{
    color: #0F172A !important;
    opacity: 1 !important;
}}

/* =========================
   FIX DEFINITIVO: Subheaders (st.subheader)
   ========================= */

/* st.subheader genera h3 */
h3, h3 span, h3 div {{
    color: #0F172A !important;     /* azul oscuro */
    opacity: 1 !important;
    font-weight: 800 !important;
}}

/* Dentro de tarjetas (por seguridad) */
.card h3,
.card h3 span,
.card h3 div {{
    color: #0F172A !important;
    opacity: 1 !important;
}}

/* =========================
   FIX: Botones de descarga (PDF / Excel)
   ========================= */

div[data-testid="stDownloadButton"] > button {{
    background-color: #1A3D75 !important;   /* azul SOLDICOM */
    color: #FFFFFF !important;              /* texto blanco */
    border-radius: 10px !important;
    border: 0px !important;
    padding: 0.6rem 1.0rem !important;
    font-weight: 600 !important;
}}

div[data-testid="stDownloadButton"] > button:hover {{
    background-color: #304F83 !important;   /* azul hover */
    color: #FFFFFF !important;
}}

/* =========================
   FIX: Sidebar (menú lateral) - textos legibles
   ========================= */

/* Título del sidebar (st.header) y subtítulos */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {{
    color: #F8FAFC !important;   /* casi blanco */
    opacity: 1 !important;
}}

/* Labels de widgets en el sidebar */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] > label,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] > label p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] > label span {{
    color: #F8FAFC !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}}

/* =========================
   FIX: Dialog / Modal (Lectura rápida)
   ========================= */

div[role="dialog"] p,
div[role="dialog"] li,
div[role="dialog"] span {{
    color: #F8FAFC !important;   /* blanco suave */
    opacity: 1 !important;
}}

div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3,
div[role="dialog"] h4 {{
    color: #FFFFFF !important;
    font-weight: 700 !important;
}}

/* =========================
   FIX: Métricas de información de la EDS
   ========================= */

[data-testid="stMetric"],
[data-testid="stMetric"] label,
[data-testid="stMetric"] div,
[data-testid="stMetric"] span {{
    color: #0F172A !important;   /* azul oscuro */
    opacity: 1 !important;
}}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] span {{
    color: #0F172A !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div,
[data-testid="stMetricValue"] span {{
    color: #1A3D75 !important;   /* azul SOLDICOM */
    font-weight: 800 !important;
    opacity: 1 !important;
}}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER (logo arriba - Principal)
# -----------------------------
# -----------------------------
# RUTAS DE ARCHIVOS
# -----------------------------
BASE_DIR = Path(__file__).parent

def resolve_path(local_path: str, app_path: str) -> str:
    """
    Permite usar la app tanto en Colab como en Streamlit Cloud.
    Primero intenta usar /mnt/data; si no existe, usa assets/.
    """
    if Path(local_path).exists():
        return local_path
    return str(BASE_DIR / app_path)

LOGO_PATH = resolve_path("/mnt/data/logo-soldicom1.png", "assets/logo-soldicom1.png")
BASE_EDS_PATH = resolve_path("/mnt/data/BASE_EDS.xlsx", "assets/BASE_EDS.xlsx")
LOGO_FENDI_PATH = resolve_path("/mnt/data/logo-fendipetroleo.png", "assets/logo-fendipetroleo.png")
LOGO_COMCE_PATH = resolve_path("/mnt/data/log-comce1.png", "assets/log-comce1.png")

col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image(Image.open(LOGO_PATH), width=300)
    except Exception:
        st.write("Logo no disponible")
with col_title:
    st.title("Herramienta de identificación de riesgos de pérdida de competencia")
    st.caption("Acuerdos verticales – Distribución minorista de combustibles líquidos (Fondo SOLDICOM)")

st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

# -----------------------------
# Wizard state
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1
if "result" not in st.session_state:
    st.session_state.result = None

if "sicom_code" not in st.session_state:
    st.session_state.sicom_code = None

if "eds_info" not in st.session_state:
    st.session_state.eds_info = None

if "competitors_df" not in st.session_state:
    st.session_state.competitors_df = pd.DataFrame()

def go(step: int):
    st.session_state.step = step

def step_badge():
    st.markdown(f"<span class='badge'>Paso {st.session_state.step} de 3</span>", unsafe_allow_html=True)
    st.write("")

# -----------------------------
# Consulta de mercado relevante por código SICOM
# -----------------------------
def normalize_code(value) -> str:
    """
    Normaliza códigos SICOM/COMPETIDOR.
    Ejemplo: 610004.0 -> 610004
    """
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value


@st.cache_data(show_spinner=False)
def load_base_eds(path: str) -> pd.DataFrame:
    """
    Carga la base de mercado relevante de EDS.
    """
    df = pd.read_excel(path, dtype=str)

    required_cols = [
        "SICOM",
        "COMPETIDOR",
        "NOMBRE COMERCIAL",
        "BANDERA",
        "DEPARTAMENTO",
        "MUNICIPIO",
        "Nom_Com",
        "BANDERA_COM",
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas en BASE_EDS.xlsx: {missing_cols}")

    df = df[required_cols].copy()

    df["SICOM_NORM"] = df["SICOM"].apply(normalize_code)
    df["COMPETIDOR"] = df["COMPETIDOR"].apply(normalize_code)

    return df


def get_market_relevant_info(sicom_code: str):
    """
    Busca la EDS por SICOM y retorna:
    - información de la EDS
    - competidores del mercado relevante
    """
    df = load_base_eds(BASE_EDS_PATH)

    sicom_norm = normalize_code(sicom_code)
    subset = df[df["SICOM_NORM"] == sicom_norm].copy()

    if subset.empty:
        return None, pd.DataFrame()

    first = subset.iloc[0]

    eds_info = {
        "SICOM": sicom_norm,
        "NOMBRE COMERCIAL": first.get("NOMBRE COMERCIAL", "No disponible"),
        "BANDERA": first.get("BANDERA", "No disponible"),
        "DEPARTAMENTO": first.get("DEPARTAMENTO", "No disponible"),
        "MUNICIPIO": first.get("MUNICIPIO", "No disponible"),
    }

    competitors = subset[["COMPETIDOR", "Nom_Com", "BANDERA_COM"]].copy()
    competitors = competitors.rename(columns={
        "Nom_Com": "NOMBRE COMERCIAL"
    })

    competitors = competitors.drop_duplicates()
    competitors = competitors.sort_values(
        by=["BANDERA_COM", "NOMBRE COMERCIAL"],
        na_position="last"
    )

    return eds_info, competitors

# -----------------------------
# Model helpers
# -----------------------------
def yesno(x: str) -> float:
    return 1.0 if x == "Sí" else 0.0

def dur_scale(meses: int) -> float:
    if meses <= 12:
        return 0.0
    elif meses <= 36:
        return 0.5
    else:
        return 1.0

def compute_score(params: dict, inputs: dict) -> dict:
    weights = params["weights"]
    threshold_green = params["threshold_green"]
    threshold_yellow = params["threshold_yellow"]
    alpha = params["alpha"]
    center = params["center"]

    x = {
        "exclusividad": yesno(inputs["exclusividad"]),
        "duracion": dur_scale(inputs["duracion_meses"]),
        "clausulas_precio": yesno(inputs["clausulas_precio"]),
        "penalidades": yesno(inputs["penalidades"]),
        "datos_compartidos": yesno(inputs["datos_compartidos"]),
        "control_operativo": yesno(inputs["control_operativo"]),
    }

    max_score = sum(weights.values()) if sum(weights.values()) > 0 else 1
    raw_score = sum(weights[k] * x[k] for k in x.keys())
    score = 100.0 * raw_score / max_score

    p = 1.0 / (1.0 + np.exp(-alpha * (score - center)))

    if score <= threshold_green:
        color_hex = "#2ecc71"
        label = "RIESGO BAJO"
        bucket = "Bajo"
    elif score <= threshold_yellow:
        color_hex = "#f1c40f"
        label = "RIESGO MEDIO"
        bucket = "Medio"
    else:
        color_hex = "#e74c3c"
        label = "RIESGO ALTO"
        bucket = "Alto"

    contrib = {k: (weights[k] * x[k]) for k in x.keys()}
    df = pd.DataFrame({
        "Factor": list(contrib.keys()),
        "Activado (0/1)": [x[k] for k in contrib.keys()],
        "Peso": [weights[k] for k in contrib.keys()],
        "Contribución": [contrib[k] for k in contrib.keys()],
    }).sort_values("Contribución", ascending=False)

    top3 = df[df["Contribución"] > 0].head(3)

    return {
        "score": score,
        "p": p,
        "bucket": bucket,
        "label": label,
        "color_hex": color_hex,
        "drivers_df": df,
        "top3": top3,
        "inputs": inputs,
        "params": params,
    }

# -----------------------------
# Sidebar parameters
# -----------------------------
with st.sidebar:
    st.header("Parámetros del modelo")
    w = {
        "exclusividad": st.slider("Peso: Exclusividad", 0, 30, 15),
        "duracion": st.slider("Peso: Duración (meses)", 0, 20, 10),
        "clausulas_precio": st.slider("Peso: Restricciones de precio", 0, 25, 12),
        "penalidades": st.slider("Peso: Penalidades / costos salida", 0, 25, 12),
        "datos_compartidos": st.slider("Peso: Intercambio info sensible", 0, 20, 8),
        "control_operativo": st.slider("Peso: Control operativo", 0, 25, 10),
    }
    threshold_green = st.slider("Umbral VERDE (≤)", 0, 100, 33)
    threshold_yellow = st.slider("Umbral AMARILLO (≤)", 0, 100, 66)
    st.subheader("Calibración probabilidad")
    alpha = st.slider("Pendiente (alpha)", 0.01, 0.25, 0.08)
    center = st.slider("Centro (score p≈50%)", 20, 80, 55)

params = {
    "weights": w,
    "threshold_green": threshold_green,
    "threshold_yellow": threshold_yellow,
    "alpha": alpha,
    "center": center,
}

def build_pdf_report(
    res: dict,
    logo_path: str = None,
    eds_info: dict = None,
    competitors_df: pd.DataFrame = None
) -> io.BytesIO:
    
    """
    Genera un PDF con branding + resumen + drivers.
    Devuelve un BytesIO listo para st.download_button.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    w, h = letter

    # Header
    y = h - 50

    # Logo
    if logo_path:
        try:
            c.drawImage(ImageReader(logo_path), 40, h - 85, width=150, height=55, mask='auto')
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 13)
    c.drawString(210, h - 60, "Reporte de Riesgo – Contrato Mayorista/Minorista")

    c.setFont("Helvetica", 9)
    c.drawString(40, h - 105, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(40, h - 120, f"Puntaje: {res['score']:.1f}/100")
    c.drawString(200, h - 120, f"Probabilidad estimada: {100*res['p']:.1f}%")
    c.drawString(420, h - 120, f"Semáforo: {res['label']}")

    # Información de la EDS consultada
    y = h - 150

    if eds_info is not None:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Información de la EDS consultada")
        y -= 16

        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"SICOM: {eds_info.get('SICOM', 'N/D')}")
        y -= 12
        c.drawString(50, y, f"Nombre comercial: {eds_info.get('NOMBRE COMERCIAL', 'N/D')}")
        y -= 12
        c.drawString(50, y, f"Bandera: {eds_info.get('BANDERA', 'N/D')}")
        y -= 12
        c.drawString(50, y, f"Departamento: {eds_info.get('DEPARTAMENTO', 'N/D')}")
        y -= 12
        c.drawString(50, y, f"Municipio: {eds_info.get('MUNICIPIO', 'N/D')}")
        y -= 16

    if competitors_df is not None and not competitors_df.empty:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Competidores en el mercado relevante")
        y -= 14

        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"Número de competidores identificados: {len(competitors_df)}")
        y -= 16

        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y, "COMPETIDOR")
        c.drawString(130, y, "NOMBRE COMERCIAL")
        c.drawString(390, y, "BANDERA")
        y -= 10

        c.setFont("Helvetica", 8)

        # En PDF se muestran los primeros 15 para evitar páginas muy largas.
        # El Excel contiene la tabla completa.
        for _, row in competitors_df.head(15).iterrows():
            comp = str(row.get("COMPETIDOR", ""))
            nom = str(row.get("NOMBRE COMERCIAL", ""))
            bandera = str(row.get("BANDERA_COM", ""))

            if len(nom) > 45:
                nom = nom[:42] + "..."

            c.drawString(50, y, comp)
            c.drawString(130, y, nom)
            c.drawString(390, y, bandera)
            y -= 10

            if y < 80:
                c.showPage()
                y = h - 60

        if len(competitors_df) > 15:
            y -= 4
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(
                50,
                y,
                "Nota: el PDF muestra los primeros 15 competidores. El archivo Excel incluye la tabla completa."
            )
            y -= 14
    
    # Inputs
    y = h - 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Información diligenciada")
    y -= 16

    c.setFont("Helvetica", 9)
    for k, v in res["inputs"].items():
        c.drawString(50, y, f"- {k}: {v}")
        y -= 12
        if y < 80:
            c.showPage()
            y = h - 60

    # Drivers top
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Lectura rápida (principales drivers)")
    y -= 16

    c.setFont("Helvetica", 9)
    top3 = res["top3"]
    if top3 is None or top3.empty:
        c.drawString(50, y, "- No hay factores activados con contribución positiva (según parametrización actual).")
        y -= 12
    else:
        for _, r in top3.iterrows():
            c.drawString(50, y, f"- {r['Factor']} | peso {int(r['Peso'])} | contribución {r['Contribución']:.1f}")
            y -= 12
            if y < 80:
                c.showPage()
                y = h - 60

    # Nota
    y -= 6
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, y, "Nota: Esta herramienta prioriza contratos para revisión técnica. No constituye una determinación de infracción.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def build_excel_report(
    res: dict,
    eds_info: dict = None,
    competitors_df: pd.DataFrame = None
) -> io.BytesIO:
    
    """
    Genera un Excel con 3 hojas:
    - Resumen
    - Respuestas
    - Drivers
    """
    output = io.BytesIO()

    resumen_data = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Puntaje": round(res["score"], 2),
        "Probabilidad_%": round(100*res["p"], 2),
        "Semáforo": res["label"],
        "Bucket": res["bucket"],
    }

    if eds_info is not None:
        resumen_data.update({
            "SICOM": eds_info.get("SICOM", ""),
            "Nombre_EDS": eds_info.get("NOMBRE COMERCIAL", ""),
            "Bandera_EDS": eds_info.get("BANDERA", ""),
            "Departamento": eds_info.get("DEPARTAMENTO", ""),
            "Municipio": eds_info.get("MUNICIPIO", ""),
            "Numero_competidores": 0 if competitors_df is None else len(competitors_df),
        })

    resumen_df = pd.DataFrame([resumen_data])

    respuestas_df = pd.DataFrame([res["inputs"]]).T.reset_index()
    respuestas_df.columns = ["Variable", "Valor"]

    drivers_df = res["drivers_df"].copy()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        respuestas_df.to_excel(writer, sheet_name="Respuestas", index=False)
        drivers_df.to_excel(writer, sheet_name="Drivers", index=False)

        if eds_info is not None:
            eds_df = pd.DataFrame([eds_info])
            eds_df.to_excel(writer, sheet_name="EDS", index=False)

        if competitors_df is not None and not competitors_df.empty:
            competitors_df.to_excel(writer, sheet_name="Competidores", index=False)

        # Ajuste simple de anchos
        sheets_to_format = ["Resumen", "Respuestas", "Drivers"]

        if eds_info is not None:
            sheets_to_format.append("EDS")

        if competitors_df is not None and not competitors_df.empty:
            sheets_to_format.append("Competidores")

        for sheet in sheets_to_format:
            ws = writer.sheets[sheet]
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = min(max_len + 2, 45)

    output.seek(0)
    return output


# -----------------------------
# STEP 1: Introducción
# -----------------------------
if st.session_state.step == 1:
    step_badge()
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("Bienvenida y descripción")
    st.write("""
Esta herramienta permite **identificar y priorizar** riesgos potenciales derivados de la relación contractual entre
**distribuidores mayoristas** y **minoristas** en el sector de combustibles líquidos.

**Salida:** puntaje (0–100), probabilidad estimada y semáforo (bajo/medio/alto), con explicabilidad (drivers).
""")
    st.info("Haz clic en **Continuar** para diligenciar la información del contrato.")
    st.markdown("</div>", unsafe_allow_html=True)

    if hasattr(st, "dialog"):

        @st.dialog("Identificación de la EDS")
        def sicom_dialog():
            st.write(
                "Ingrese el **código SICOM** de la estación de servicio para consultar "
                "su mercado relevante y continuar con la evaluación del contrato."
            )

            with st.form("form_sicom_dialog"):
                sicom_input = st.text_input(
                    "Código SICOM",
                    placeholder="6 dígitos"
                )
                submit_sicom = st.form_submit_button("OK / Continuar")

            if submit_sicom:
                eds_info, competitors_df = get_market_relevant_info(sicom_input)

                if eds_info is None:
                    st.error(
                        "No se encontró información para el código SICOM ingresado. "
                        "Verifique el código e intente nuevamente."
                    )
                else:
                    st.session_state.sicom_code = normalize_code(sicom_input)
                    st.session_state.eds_info = eds_info
                    st.session_state.competitors_df = competitors_df
                    go(2)
                    st.rerun()

        if st.button("Continuar ➜"):
            sicom_dialog()

    else:
        with st.form("form_sicom_inline"):
            sicom_input = st.text_input(
                "Código SICOM",
                placeholder="Ejemplo: 610004"
            )
            submit_sicom = st.form_submit_button("OK / Continuar")

        if submit_sicom:
            eds_info, competitors_df = get_market_relevant_info(sicom_input)

            if eds_info is None:
                st.error(
                    "No se encontró información para el código SICOM ingresado. "
                    "Verifique el código e intente nuevamente."
                )
            else:
                st.session_state.sicom_code = normalize_code(sicom_input)
                st.session_state.eds_info = eds_info
                st.session_state.competitors_df = competitors_df
                go(2)
                st.rerun()

# -----------------------------
# STEP 2: Forma y Estructura
# -----------------------------
elif st.session_state.step == 2:
    step_badge()
    st.markdown('<div class="card">', unsafe_allow_html=True)
#    st.header("Ingreso de información del contrato")

    # -----------------------------
    # Información del mercado relevante
    # -----------------------------
    if st.session_state.eds_info is not None:
        eds = st.session_state.eds_info
        competitors_df = st.session_state.competitors_df

        st.subheader("Información de la EDS consultada")

#        m1, m2, m3, m4, m5 = st.columns(5)
#
#        with m1:
#            st.metric("SICOM", eds.get("SICOM", "N/D"))
#        with m2:
#            st.metric("Bandera", eds.get("BANDERA", "N/D"))
#        with m3:
#            st.metric("Departamento", eds.get("DEPARTAMENTO", "N/D"))
#        with m4:
#            st.metric("Municipio", eds.get("MUNICIPIO", "N/D"))
#        with m5:
#            st.metric("Competidores", len(competitors_df))

        st.markdown(f"""
        <div style="
            display:grid;
            grid-template-columns: repeat(5, 1fr);
            gap:12px;
            margin-top:8px;
            margin-bottom:10px;
        ">
            <div style="background:white; border-radius:12px; padding:10px 12px; border:1px solid rgba(15,23,42,0.08);">
                <div style="font-size:11px; color:#475569; font-weight:700;">SICOM</div>
                <div style="font-size:18px; color:#1A3D75; font-weight:800;">{eds.get("SICOM", "N/D")}</div>
            </div>

            <div style="background:white; border-radius:12px; padding:10px 12px; border:1px solid rgba(15,23,42,0.08);">
                <div style="font-size:11px; color:#475569; font-weight:700;">Bandera</div>
                <div style="font-size:18px; color:#1A3D75; font-weight:800;">{eds.get("BANDERA", "N/D")}</div>
            </div>

            <div style="background:white; border-radius:12px; padding:10px 12px; border:1px solid rgba(15,23,42,0.08);">
                <div style="font-size:11px; color:#475569; font-weight:700;">Departamento</div>
                <div style="font-size:18px; color:#1A3D75; font-weight:800;">{eds.get("DEPARTAMENTO", "N/D")}</div>
            </div>

            <div style="background:white; border-radius:12px; padding:10px 12px; border:1px solid rgba(15,23,42,0.08);">
                <div style="font-size:11px; color:#475569; font-weight:700;">Municipio</div>
                <div style="font-size:18px; color:#1A3D75; font-weight:800;">{eds.get("MUNICIPIO", "N/D")}</div>
            </div>

            <div style="background:white; border-radius:12px; padding:10px 12px; border:1px solid rgba(15,23,42,0.08);">
                <div style="font-size:11px; color:#475569; font-weight:700;">Competidores</div>
                <div style="font-size:18px; color:#1A3D75; font-weight:800;">{len(competitors_df)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(
            f"**Nombre comercial de la EDS:** {eds.get('NOMBRE COMERCIAL', 'No disponible')}"
        )

        st.markdown("**Competidores identificados en el mercado relevante:**")

        st.dataframe(
            competitors_df,
            width="stretch",
            hide_index=True
        )

        st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

    else:
        st.warning("No se ha ingresado un código SICOM. Vuelve al paso anterior para identificar la EDS.")
        if st.button("⟵ Volver a bienvenida"):
            go(1)
            st.rerun()
        st.stop()

    st.header("Ingreso de información del contrato")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Estructura")
        exclusividad = st.selectbox("¿Hay cláusula de exclusividad?", ["No", "Sí"])
        duracion_meses = st.number_input("Duración del contrato (meses)", min_value=0, max_value=240, value=36, step=1)
        penalidades = st.selectbox("¿Existen penalidades/costos de salida relevantes?", ["No", "Sí"])

    with c2:
        st.subheader("Conducta / incentivos")
        clausulas_precio = st.selectbox("¿Hay restricciones sobre precios/promociones o alineación obligatoria?", ["No", "Sí"])
        control_operativo = st.selectbox("¿El mayorista impone control operativo (inventario, proveedores, branding rígido, etc.)?", ["No", "Sí"])

    with c3:
        st.subheader("Información")
        datos_compartidos = st.selectbox("¿Se comparte información sensible (ventas, márgenes, estrategias locales)?", ["No", "Sí"])

    st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

    col_back, col_calc = st.columns([1, 1])
    with col_back:
        if st.button("⟵ Volver"):
            go(1)
    with col_calc:
        if st.button("Calcular"):
            inputs = {
                "exclusividad": exclusividad,
                "duracion_meses": int(duracion_meses),
                "penalidades": penalidades,
                "clausulas_precio": clausulas_precio,
                "control_operativo": control_operativo,
                "datos_compartidos": datos_compartidos,
            }
            st.session_state.result = compute_score(params=params, inputs=inputs)
            go(3)

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# STEP 3: Resultados
# -----------------------------
else:
    step_badge()
    res = st.session_state.result
    if res is None:
        st.warning("No hay resultados aún. Vuelve al formulario para calcular.")
        if st.button("Ir al formulario"):
            go(2)
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("Resultados")

        # -----------------------------
        # Información de la EDS y mercado relevante
        # -----------------------------
        eds_info = st.session_state.get("eds_info", None)
        competitors_df = st.session_state.get("competitors_df", pd.DataFrame())

        if eds_info is not None:
            st.subheader("EDS consultada y mercado relevante")

            st.markdown(
                f"""
                <div style="
                    background:#FFFFFF;
                    border:1px solid rgba(15,23,42,0.08);
                    border-radius:14px;
                    padding:14px 18px;
                    margin-bottom:12px;
                    box-shadow:0 4px 12px rgba(15,23,42,0.06);
                ">
                    <p style="margin:0; color:#0F172A; font-size:16px;">
                        <b>Nombre comercial:</b> {eds_info.get("NOMBRE COMERCIAL", "N/D")} &nbsp; | &nbsp;
                        <b>SICOM:</b> {eds_info.get("SICOM", "N/D")} &nbsp; | &nbsp;
                        <b>Bandera:</b> {eds_info.get("BANDERA", "N/D")}
                    </p>
                    <p style="margin:6px 0 0 0; color:#0F172A; font-size:16px;">
                        <b>Departamento:</b> {eds_info.get("DEPARTAMENTO", "N/D")} &nbsp; | &nbsp;
                        <b>Municipio:</b> {eds_info.get("MUNICIPIO", "N/D")} &nbsp; | &nbsp;
                        <b>Competidores identificados:</b> {len(competitors_df)}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.expander("Ver competidores del mercado relevante"):
                st.dataframe(
                    competitors_df,
                    width="stretch",
                    hide_index=True
                )

            st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)
        
        left, mid, right = st.columns([1.05, 1.2, 1.1])

        with left:
            st.subheader("Semáforo")
            st.markdown(f"""
            <div style="
                width: 320px;
                height: 320px;
                border-radius: 50%;
                background-color: {res['color_hex']};
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 10px auto 18px auto;
                box-shadow: 0 10px 24px rgba(0,0,0,0.22);
            ">
                <div style="text-align:center; color:white;">
                    <div style="font-size:28px; font-weight:800;">{res['label']}</div>
                    <div style="font-size:22px; margin-top:6px;">{res['score']:.1f} / 100</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(
                f"<p style='text-align:center; font-size:18px; margin-top:-6px;'>"
                f"<b>Probabilidad estimada:</b> {100*res['p']:.1f}%</p>",
                unsafe_allow_html=True
            )

        with mid:
            st.subheader("Detalle")
            st.write(f"**Puntaje:** {res['score']:.1f}")
            st.write(f"**Probabilidad:** {100*res['p']:.1f}%")
            st.write(f"**Clasificación:** {res['bucket']}")
            st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)
            st.subheader("Drivers (contribución)")
            st.dataframe(res["drivers_df"], width="stretch", hide_index=True)

        with right:
            st.subheader("Acciones")
            if st.button("⟵ Modificar respuestas"):
                go(2)

            st.markdown("")
            # Exportación (PDF y Excel)
            eds_info_report = st.session_state.get("eds_info", None)
            competitors_report = st.session_state.get("competitors_df", pd.DataFrame())

            pdf_buffer = build_pdf_report(
                res,
                logo_path=LOGO_PATH,
                eds_info=eds_info_report,
                competitors_df=competitors_report
            )

            xlsx_buffer = build_excel_report(
                res,
                eds_info=eds_info_report,
                competitors_df=competitors_report
            )

            st.download_button(
                label="📄 Exportar a PDF",
                data=pdf_buffer,
                file_name=f"reporte_riesgo_soldicom_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )

            st.download_button(
                label="📊 Exportar a Excel",
                data=xlsx_buffer,
                file_name=f"reporte_riesgo_soldicom_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.markdown("")

            # --- Lectura rápida (explicar resultados) ---
            top3_local = res["top3"]

            if hasattr(st, "dialog"):
                @st.dialog("Lectura rápida de resultados")
                def lectura_rapida_dialog():
                    st.write(
                        "Este resultado sintetiza los **principales elementos contractuales** que, de acuerdo con la "
                        "parametrización actual del modelo, **incrementan el riesgo potencial de afectación a la competencia**."
                    )

                    st.markdown("**Factores con mayor contribución al riesgo:**")

                    if top3_local.empty:
                        st.write(
                            "- No se identifican cláusulas o condiciones activadas que incrementen el riesgo, "
                            "según los parámetros actualmente definidos."
                        )
                    else:
                        for _, r in top3_local.iterrows():
                            st.write(
                                f"- **{r['Factor']}**: peso relativo {int(r['Peso'])} "
                                f"(contribución estimada {r['Contribución']:.1f})."
                            )

                    st.markdown(
                        """
                        **Interpretación operativa:**
                        Un mayor número de factores activados o una mayor contribución acumulada sugiere la conveniencia de
                        realizar una **revisión técnica más detallada del contrato**, considerando su contexto económico y regulatorio.
                        """
                    )

                    st.info(
                        "Nota: esta herramienta tiene un carácter preventivo y orientador. "
                        "El semáforo no constituye una determinación de infracción ni sustituye el análisis jurídico o económico de fondo."
                    )

                if st.button("📌 Lectura rápida de los resultados"):
                    lectura_rapida_dialog()

            else:
                with st.expander("📌 Lectura rápida de los resultados"):
                    st.write(
                        "Este resultado sintetiza los **principales elementos contractuales** que, de acuerdo con la "
                        "parametrización actual del modelo, **incrementan el riesgo potencial de afectación a la competencia**."
                    )

                    st.markdown("**Factores con mayor contribución al riesgo:**")

                    if top3_local.empty:
                        st.write(
                            "- No se identifican cláusulas o condiciones activadas que incrementen el riesgo, "
                            "según los parámetros actualmente definidos."
                        )
                    else:
                        for _, r in top3_local.iterrows():
                            st.write(
                                f"- **{r['Factor']}**: peso relativo {int(r['Peso'])} "
                                f"(contribución estimada {r['Contribución']:.1f})."
                            )

                    st.markdown(
                        """
                        **Interpretación operativa:**
                        Un mayor número de factores activados o una mayor contribución acumulada sugiere la conveniencia de
                        realizar una **revisión técnica más detallada del contrato**, considerando su contexto económico y regulatorio.
                        """
                    )

                    st.info(
                        "Nota: esta herramienta tiene un carácter preventivo y orientador."
                        "El semáforo no constituye una determinación de infracción ni sustituye el análisis jurídico o económico de fondo."
                    )


        st.markdown("</div>", unsafe_allow_html=True)


# ======================================================
# FOOTER – Logos institucionales (al final de todo)
# ======================================================

st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 2])

with col2:
    try:
        st.image(Image.open(LOGO_FENDI_PATH), width=220)
    except Exception:
        pass

with col3:
    try:
        st.image(Image.open(LOGO_COMCE_PATH), width=200)
    except Exception:
        pass

st.caption(
    "Herramienta desarrollada en el marco del estudio sobre acuerdos verticales "
    "en la distribución minorista de combustibles líquidos – Fondo SOLDICOM / FENDIPETRÓLEO / COMCE."
    " © 2026"
)
