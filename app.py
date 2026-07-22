import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
from PIL import Image
import io
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

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

.badge {{
    display:inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 13px;
    color: #166534 !important;         /* verde oscuro para el texto */
    background: #DCFCE7 !important;    /* verde claro de fondo */
    border: 1px solid #86EFAC;         /* borde verde suave */
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
   FIX DEFINITIVO: Dialog / Modal
   - Ventana SICOM paso 1
   - Ventana Lectura rápida paso 3
   ========================= */

/* IMPORTANTE:
   No pintar el contenedor externo del modal con azul sólido.
   Ese contenedor ocupa toda la pantalla. Por eso antes se veía
   un rectángulo azul oscuro cubriendo todo el aplicativo.
*/
div[data-baseweb="modal"],
div[data-testid="stDialog"],
div[data-testid="stModal"],
div[data-baseweb="modal"] > div,
div[data-testid="stDialog"] > div,
div[data-testid="stModal"] > div {{
    background-color: transparent !important;
    background: transparent !important;
}}

/* Capa flotante/transparente: deja ver el aplicativo detrás */
div[data-baseweb="modal"]::before,
div[data-testid="stDialog"]::before,
div[data-testid="stModal"]::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.38) !important;
    pointer-events: none;
    z-index: -1;
}}

/* Caja real de la ventana emergente */
div[role="dialog"] {{
    background-color: #0F172A !important;
    color: #F8FAFC !important;
    border-radius: 22px !important;
    border: 1px solid rgba(148, 163, 184, 0.45) !important;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.35) !important;
}}

/* Asegura que solo la caja del modal sea oscura, no todo el fondo */
div[role="dialog"] > div,
div[role="dialog"] section,
div[role="dialog"] div[data-testid="stVerticalBlock"],
div[role="dialog"] div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: transparent !important;
    background: transparent !important;
}}

/* Texto dentro de la caja flotante */
div[role="dialog"] p,
div[role="dialog"] span,
div[role="dialog"] li,
div[role="dialog"] label,
div[role="dialog"] strong,
div[role="dialog"] div[data-testid="stMarkdownContainer"],
div[role="dialog"] div[data-testid="stMarkdownContainer"] * {{
    color: #F8FAFC !important;
    opacity: 1 !important;
}}

/* Títulos de ventanas flotantes */
div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3,
div[role="dialog"] h4 {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
}}

/* Campo del código SICOM dentro del modal */
div[role="dialog"] input {{
    color: #F8FAFC !important;
    background-color: #1E293B !important;
    border: 1px solid #64748B !important;
    border-radius: 10px !important;
}}

div[role="dialog"] input::placeholder {{
    color: #CBD5E1 !important;
    opacity: 1 !important;
}}

/* Botones dentro de ventanas flotantes */
div[role="dialog"] button {{
    color: #FFFFFF !important;
    border-color: #64748B !important;
}}

/* Nota dentro de lectura rápida */
div[role="dialog"] .modal-note {{
    background-color: #1E497D !important;
    border-radius: 14px !important;
    padding: 22px 24px !important;
    margin-top: 18px !important;
}}

div[role="dialog"] .modal-note,
div[role="dialog"] .modal-note * {{
    color: #F8FAFC !important;
    opacity: 1 !important;
}}

div[role="dialog"] .modal-note strong {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
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

/* =========================
   OCULTAR MENÚ SUPERIOR STREAMLIT
   ========================= */

/* Oculta menú de tres puntos */
#MainMenu {{
    visibility: hidden !important;
}}

/* Oculta footer nativo */
footer {{
    visibility: hidden !important;
}}

/* Oculta header superior */
header {{
    visibility: hidden !important;
}}

/* =========================
   FIX: Expander de competidores
   ========================= */

/* Contenedor general del expander */
[data-testid="stExpander"] {{
    background-color: #FFFFFF !important;
    border: 1px solid rgba(15, 23, 42, 0.10) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}}

/* Barra/cabecera del expander */
[data-testid="stExpander"] details summary {{
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
}}

/* Texto dentro de la barra */
[data-testid="stExpander"] details summary p,
[data-testid="stExpander"] details summary span,
[data-testid="stExpander"] details summary div {{
    color: #0F172A !important;
    opacity: 1 !important;
}}

/* Hover del expander */
[data-testid="stExpander"] details summary:hover {{
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}}

/* =========================
   Tabla HTML de competidores
   ========================= */

.competitors-table-wrap {{
    background: #FFFFFF !important;
    border-radius: 12px;
    padding: 10px;
    margin-top: 8px;
    border: 1px solid rgba(15,23,42,0.10);
    overflow-x: auto;
}}

.competitors-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    color: #0F172A !important;
    background: #FFFFFF !important;
}}

.competitors-table th {{
    background: #EFF8FE !important;
    color: #1A3D75 !important;
    font-weight: 800;
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid #CBD5E1;
}}

.competitors-table td {{
    color: #0F172A !important;
    padding: 9px 10px;
    border-bottom: 1px solid #E2E8F0;
}}

.competitors-table tr:nth-child(even) {{
    background: #F8FAFC !important;
}}

.competitors-table tr:hover {{
    background: #EAF4FF !important;
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
#LOGO_FENDI_PATH = resolve_path("/mnt/data/logo-fendipetroleo.png", "assets/logo-fendipetroleo.png")
#LOGO_COMCE_PATH = resolve_path("/mnt/data/log-comce1.png", "assets/log-comce1.png")
LOGO_SOMOSUNO_PATH = resolve_path("/mnt/data/logo-somosuno.png", "assets/logo-somosuno.png")

# Ancla superior para forzar que la vista vuelva arriba al cargar y al cambiar de paso.
st.markdown("<div id='app-top-anchor'></div>", unsafe_allow_html=True)

col_logo, col_title = st.columns([1, 4], vertical_alignment="center")
with col_logo:
    try:
        st.image(Image.open(LOGO_PATH), width=300)
    except Exception:
        st.write("Logo no disponible")
with col_title:
#    st.title("Herramienta de identificación de riesgos de pérdida de competencia")
    st.markdown(
        f'<h1 style="color:{PRIMARY} !important; font-weight:800;">Herramienta de identificación de riesgos de pérdida de competencia</h1>',
        unsafe_allow_html=True
    )
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

if "_scroll_to_top" not in st.session_state:
    st.session_state["_scroll_to_top"] = True

def go(step: int):
    st.session_state.step = step
    st.session_state["_scroll_to_top"] = True

def reset_app():
    st.session_state.step = 1
    st.session_state.result = None
    st.session_state.sicom_code = None
    st.session_state.eds_info = None
    st.session_state.competitors_df = pd.DataFrame()
    st.session_state["_scroll_to_top"] = True

# Fuerza la vista al inicio de la página al cargar y después de cada cambio de paso.
# La bandera evita que la app se devuelva arriba mientras el usuario diligencia widgets del formulario.
def scroll_to_top_if_needed():
    """Fuerza la vista al inicio de la herramienta.

    Se ejecuta en carga inicial y después de cada cambio de paso. La repetición
    con varios tiempos corrige la restauración automática de scroll del navegador
    y de Streamlit después de un st.rerun().
    """
    if not st.session_state.get("_scroll_to_top", False):
        return

    components.html(
        """
        <script>
        (function () {
            const forceTop = () => {
                try {
                    const doc = window.parent.document;
                    const win = window.parent;

                    // Ventana principal
                    win.scrollTo({ top: 0, left: 0, behavior: 'instant' });
                    win.scrollTo(0, 0);
                    doc.documentElement.scrollTop = 0;
                    doc.body.scrollTop = 0;

                    // Contenedores internos usados por distintas versiones de Streamlit
                    const selectors = [
                        '[data-testid="stAppViewContainer"]',
                        '[data-testid="stMain"]',
                        '[data-testid="stMainBlockContainer"]',
                        '[data-testid="block-container"]',
                        'section.main',
                        'main',
                        '.main',
                        '.stApp',
                        'div[data-testid="stVerticalBlock"]'
                    ];

                    selectors.forEach((selector) => {
                        doc.querySelectorAll(selector).forEach((el) => {
                            try {
                                el.scrollTop = 0;
                                el.scrollLeft = 0;
                                if (typeof el.scrollTo === 'function') {
                                    el.scrollTo({ top: 0, left: 0, behavior: 'instant' });
                                    el.scrollTo(0, 0);
                                }
                            } catch (e) {}
                        });
                    });

                    // Ancla superior de la app
                    const anchor = doc.querySelector('#app-top-anchor');
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: 'instant', block: 'start', inline: 'nearest' });
                    }
                } catch (e) {}
            };

            // Ejecutar varias veces para ganarle a la restauración automática del navegador/Streamlit
            forceTop();
            [50, 150, 300, 600, 1000, 1500, 2500, 4000, 6000].forEach((t) => {
                window.setTimeout(forceTop, t);
            });
        })();
        </script>
        """,
        height=0,
        width=0,
    )

    st.session_state["_scroll_to_top"] = False

scroll_to_top_if_needed()

def step_badge():
    st.markdown(f"<span class='badge'>Paso {st.session_state.step} de 3</span>", unsafe_allow_html=True)
    st.write("")

# -----------------------------
# Consulta de mercado relevante por código SICOM
# -----------------------------
def normalize_code(value) -> str:
    """
    Normaliza códigos SICOM:
    - elimina decimales tipo 610004.0
    - quita espacios
    - conserva como texto
    """
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value.zfill(6)

def clean_text(value) -> str:
    """
    Limpia textos para comparar banderas.
    """
    if pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip().upper()

def clean_verticalizada(value) -> int:
    """
    Convierte la variable de verticalización a 0/1.
    Acepta 1/0, SI/NO, SÍ/NO, TRUE/FALSE.
    """
    if pd.isna(value):
        return 0

    v = str(value).replace("\xa0", " ").strip().upper()

    if v in ["1", "1.0", "SI", "SÍ", "TRUE", "VERDADERO", "YES"]:
        return 1

    return 0


@st.cache_data(show_spinner=False)
def load_base_eds(path: str):
    """
    Carga la base definitiva y estandariza columnas.

    Hoja Nombre esperada:
    - SICOM
    - BANDERA_SICOM
    - NOMBRE_COMERCIAL_SICOM
    - VERTICALIZADA_SICOM

    Hoja Datos esperada:
    - SICOM
    - COMPETIDOR
    - NOMBRE_COMERCIAL_COMPETIDOR
    - BANDERA_COMPETIDOR
    - VERTICALIZADA_COMPETIDOR
    - DEPARTAMENTO
    - MUNICIPIO
    """

    nombres = pd.read_excel(path, sheet_name="Nombre", dtype=str)
    datos = pd.read_excel(path, sheet_name="Datos", dtype=str)

    nombres.columns = [str(c).strip() for c in nombres.columns]
    datos.columns = [str(c).strip() for c in datos.columns]

    # -----------------------------
    # Validar columnas hoja Nombre
    # -----------------------------
    required_nombre = [
        "SICOM",
        "BANDERA_SICOM",
        "NOMBRE_COMERCIAL_SICOM",
        "VERTICALIZADA_SICOM",
    ]

    missing_nombre = [c for c in required_nombre if c not in nombres.columns]
    if missing_nombre:
        raise ValueError(
            f"Faltan columnas en la hoja Nombre: {missing_nombre}. "
            f"Columnas disponibles: {list(nombres.columns)}"
        )

    nombres = nombres.copy()

    # Columnas estándar internas
    nombres["SICOM_NORM"] = nombres["SICOM"].apply(normalize_code)
    nombres["NOMBRE_COMERCIAL_EDS_STD"] = (
        nombres["NOMBRE_COMERCIAL_SICOM"]
        .fillna("")
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )
    nombres["BANDERA_EDS_STD"] = (
        nombres["BANDERA_SICOM"]
        .fillna("")
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )
    nombres["BANDERA_EDS_CLEAN"] = nombres["BANDERA_EDS_STD"].apply(clean_text)
    nombres["VERTICALIZADA_EDS_CLEAN"] = nombres["VERTICALIZADA_SICOM"].apply(clean_verticalizada)

    # -----------------------------
    # Validar columnas hoja Datos
    # -----------------------------
    required_datos = [
        "SICOM",
        "COMPETIDOR",
        "NOMBRE_COMERCIAL_COMPETIDOR",
        "BANDERA_COMPETIDOR",
        "VERTICALIZADA_COMPETIDOR",
    ]

    missing_datos = [c for c in required_datos if c not in datos.columns]
    if missing_datos:
        raise ValueError(
            f"Faltan columnas en la hoja Datos: {missing_datos}. "
            f"Columnas disponibles: {list(datos.columns)}"
        )

    datos = datos.copy()

    datos["SICOM_NORM"] = datos["SICOM"].apply(normalize_code)
    datos["COMPETIDOR_NORM"] = datos["COMPETIDOR"].apply(normalize_code)

    datos["NOMBRE_COMERCIAL_COMPETIDOR_STD"] = (
        datos["NOMBRE_COMERCIAL_COMPETIDOR"]
        .fillna("")
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    datos["BANDERA_COMPETIDOR_STD"] = (
        datos["BANDERA_COMPETIDOR"]
        .fillna("")
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    datos["BANDERA_COMPETIDOR_CLEAN"] = datos["BANDERA_COMPETIDOR_STD"].apply(clean_text)
    datos["VERTICALIZADA_COMPETIDOR_CLEAN"] = datos["VERTICALIZADA_COMPETIDOR"].apply(clean_verticalizada)

    # Departamento y municipio son opcionales, pero se estandarizan si existen
    if "DEPARTAMENTO" not in datos.columns:
        datos["DEPARTAMENTO"] = "No disponible"

    if "MUNICIPIO" not in datos.columns:
        datos["MUNICIPIO"] = "No disponible"

    return nombres, datos

def compute_no_competencia_score(
    competitors_df: pd.DataFrame,
    eds_info: dict
) -> dict:
    """
    Calcula el Puntaje de No Competencia incluyendo:
    - la EDS consultada;
    - los competidores de su mercado relevante.

    Total EDS = competidores identificados + EDS consultada.
    """

    bandera_eds = clean_text(eds_info.get("BANDERA", ""))
    sicom_eds = normalize_code(eds_info.get("SICOM", ""))
    verticalizada_eds = int(eds_info.get("VERTICALIZADA_EDS", 0))

    # -----------------------------
    # Construir universo del mercado relevante
    # Incluye competidores + EDS consultada
    # -----------------------------
    rows = []

    # 1. Agregar competidores
    if competitors_df is not None and not competitors_df.empty:
        for _, r in competitors_df.iterrows():
            rows.append({
                "SICOM": normalize_code(r.get("COMPETIDOR", "")),
                "BANDERA": clean_text(r.get("BANDERA_COMPETIDOR", "")),
                "VERTICALIZADA": int(r.get("VERTICALIZADA_COMPETIDOR", 0)),
                "TIPO": "COMPETIDOR",
            })

    # 2. Agregar la EDS consultada
    rows.append({
        "SICOM": sicom_eds,
        "BANDERA": bandera_eds,
        "VERTICALIZADA": verticalizada_eds,
        "TIPO": "EDS_CONSULTADA",
    })

    market_df = pd.DataFrame(rows)

    # Evitar duplicados si la EDS consultada aparece accidentalmente como competidor
    market_df = market_df.drop_duplicates(subset=["SICOM"])

    total_eds = len(market_df)

    if total_eds == 0:
        return {
            "total_eds": 0,
            "competidores_identificados": 0,
            "eds_verticalizadas": 0,
            "eds_verticalizadas_misma_bandera": 0,
            "eds_misma_bandera": 0,
            "alpha_1": 0.0,
            "alpha_2": 0.0,
            "alpha_3": 0.0,
            "puntaje_no_competencia": 0.0,
        }

    is_verticalizada = market_df["VERTICALIZADA"].eq(1)
    is_misma_bandera = market_df["BANDERA"].eq(bandera_eds)

    eds_verticalizadas = int(is_verticalizada.sum())
    eds_verticalizadas_misma_bandera = int((is_verticalizada & is_misma_bandera).sum())
    eds_misma_bandera = int(is_misma_bandera.sum())

    alpha_1 = eds_verticalizadas / total_eds
    alpha_2 = eds_verticalizadas_misma_bandera / total_eds
    alpha_3 = eds_misma_bandera / total_eds

    puntaje_no_competencia = alpha_1 * alpha_2 * alpha_3

    return {
        "total_eds": total_eds,
        "competidores_identificados": total_eds - 1,
        "eds_verticalizadas": eds_verticalizadas,
        "eds_verticalizadas_misma_bandera": eds_verticalizadas_misma_bandera,
        "eds_misma_bandera": eds_misma_bandera,
        "alpha_1": alpha_1,
        "alpha_2": alpha_2,
        "alpha_3": alpha_3,
        "puntaje_no_competencia": puntaje_no_competencia,
    }


def get_market_relevant_info(sicom_code: str):
    """
    Busca la EDS consultada por código SICOM y retorna:
    - información de la EDS consultada;
    - competidores del mercado relevante;
    - métricas del Puntaje de No Competencia.

    La EDS consultada se toma de la hoja Nombre.
    Los competidores se toman de la hoja Datos.
    """

    nombres, datos = load_base_eds(BASE_EDS_PATH)
    sicom_norm = normalize_code(sicom_code)

    # -----------------------------
    # 1. Buscar EDS consultada
    # -----------------------------
    eds_match = nombres[nombres["SICOM_NORM"] == sicom_norm].copy()

    if eds_match.empty:
        return None, pd.DataFrame()

    eds_row = eds_match.iloc[0]

    # -----------------------------
    # 2. Buscar competidores
    # -----------------------------
    subset = datos[datos["SICOM_NORM"] == sicom_norm].copy()

    if not subset.empty:
        first = subset.iloc[0]

        departamento = first.get("DEPARTAMENTO", "No disponible")
        municipio = first.get("MUNICIPIO", "No disponible")

        competitors = subset[
            [
                "COMPETIDOR",
                "NOMBRE_COMERCIAL_COMPETIDOR_STD",
                "BANDERA_COMPETIDOR_STD",
                "VERTICALIZADA_COMPETIDOR_CLEAN",
            ]
        ].copy()

        competitors = competitors.rename(columns={
            "NOMBRE_COMERCIAL_COMPETIDOR_STD": "NOMBRE_COMERCIAL_COMPETIDOR",
            "BANDERA_COMPETIDOR_STD": "BANDERA_COMPETIDOR",
            "VERTICALIZADA_COMPETIDOR_CLEAN": "VERTICALIZADA_COMPETIDOR",
        })

        competitors = competitors.drop_duplicates(subset=["COMPETIDOR"])

        competitors = competitors.sort_values(
            by=["BANDERA_COMPETIDOR", "NOMBRE_COMERCIAL_COMPETIDOR"],
            na_position="last"
        )

    else:
        departamento = "No disponible"
        municipio = "No disponible"

        competitors = pd.DataFrame(
            columns=[
                "COMPETIDOR",
                "NOMBRE_COMERCIAL_COMPETIDOR",
                "BANDERA_COMPETIDOR",
                "VERTICALIZADA_COMPETIDOR",
            ]
        )

    # -----------------------------
    # 3. Información de la EDS consultada
    # -----------------------------
    eds_info = {
        "SICOM": sicom_norm,
        "NOMBRE COMERCIAL": eds_row.get("NOMBRE_COMERCIAL_EDS_STD", "No disponible"),
        "BANDERA": eds_row.get("BANDERA_EDS_STD", "No disponible"),
        "VERTICALIZADA_EDS": int(eds_row.get("VERTICALIZADA_EDS_CLEAN", 0)),
        "DEPARTAMENTO": departamento,
        "MUNICIPIO": municipio,
    }

    # -----------------------------
    # 4. Calcular ratios incluyendo la EDS consultada
    # -----------------------------
    no_comp_metrics = compute_no_competencia_score(
        competitors_df=competitors,
        eds_info=eds_info
    )

    eds_info.update({
        "TOTAL_EDS": no_comp_metrics["total_eds"],
        "COMPETIDORES_IDENTIFICADOS": no_comp_metrics["competidores_identificados"],
        "EDS_VERTICALIZADAS": no_comp_metrics["eds_verticalizadas"],
        "EDS_VERTICALIZADAS_MISMA_BANDERA": no_comp_metrics["eds_verticalizadas_misma_bandera"],
        "EDS_MISMA_BANDERA": no_comp_metrics["eds_misma_bandera"],
        "ALPHA_1": no_comp_metrics["alpha_1"],
        "ALPHA_2": no_comp_metrics["alpha_2"],
        "ALPHA_3": no_comp_metrics["alpha_3"],
        "PUNTAJE_NO_COMPETENCIA": no_comp_metrics["puntaje_no_competencia"],
    })

    return eds_info, competitors

def render_competitors_table(competitors_df: pd.DataFrame):
    """
    Renderiza la tabla de competidores con HTML controlado.
    Usa los nombres de columnas de la base definitiva.
    """

    if competitors_df is None or competitors_df.empty:
        st.info("No se identificaron competidores para esta EDS.")
        return

    cols = [
        "COMPETIDOR",
        "NOMBRE_COMERCIAL_COMPETIDOR",
        "BANDERA_COMPETIDOR",
    ]

    cols_available = [c for c in cols if c in competitors_df.columns]

    if not cols_available:
        st.info("No se identificaron columnas de competidores para mostrar.")
        return

    table_df = competitors_df[cols_available].copy()

    table_df = table_df.rename(columns={
        "NOMBRE_COMERCIAL_COMPETIDOR": "NOMBRE COMERCIAL",
        "BANDERA_COMPETIDOR": "BANDERA",
    })

    html_table = table_df.to_html(
        index=False,
        escape=True,
        classes="competitors-table"
    )

    st.markdown(
        f"""
        <div class="competitors-table-wrap">
            {html_table}
        </div>
        """,
        unsafe_allow_html=True
    )

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

def compute_score(params: dict, inputs: dict, puntaje_no_competencia: float = 0.0) -> dict:
    weights = params["weights"]
    threshold_green = params["threshold_green"]
    threshold_yellow = params["threshold_yellow"]
    alpha = params["alpha"]
    center = params["center"]

    x = {
        "exclusividad": yesno(inputs["exclusividad"]),
        "duracion": dur_scale(inputs["duracion_meses"]),
        "penalidades": yesno(inputs["penalidades"]),
        "clausulas_precio": yesno(inputs["clausulas_precio"]),
        "control_operativo": yesno(inputs["control_operativo"]),
        "sancion_mayorista": yesno(inputs["sancion_mayorista"]),
        "datos_compartidos": yesno(inputs["datos_compartidos"]),
        "notificacion_tercero": yesno(inputs["notificacion_tercero"]),
        "mejora_oferta_mayorista": yesno(inputs["mejora_oferta_mayorista"]),
    }



    max_score = sum(weights.values()) if sum(weights.values()) > 0 else 1
    raw_score = sum(weights[k] * x[k] for k in x.keys())

    # Puntaje contractual o Puntaje de Preguntas
    score_preguntas = 100.0 * raw_score / max_score

    # ------------------------------------------------------
    # Ajuste por mercado relevante / No Competencia
    # ------------------------------------------------------
    # puntaje_no_competencia viene de:
    # alpha_1 * alpha_2 * alpha_3
    puntaje_no_competencia_raw = float(puntaje_no_competencia)

    # Media geométrica: transforma la productoria para evitar ajustes demasiado pequeños
    if puntaje_no_competencia_raw > 0:
        indice_no_competencia = puntaje_no_competencia_raw ** (1 / 3)
    else:
        indice_no_competencia = 0.0

    # Parámetro de intensidad del ajuste
    gamma_no_competencia = 1 / 3

    # Ajuste efectivamente aplicado al puntaje contractual
    ajuste_no_competencia_aplicado = gamma_no_competencia * indice_no_competencia

    # Factor multiplicativo final
    factor_ajuste_no_competencia = 1.0 + ajuste_no_competencia_aplicado

    # Puntaje final ajustado
    score_final_sin_tope = factor_ajuste_no_competencia * score_preguntas

    # Mantener escala 0-100
    score = min(100.0, score_final_sin_tope)

    # Probabilidad orientativa de riesgo
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
        "score_preguntas": score_preguntas,
        # Productoria original alpha_1 * alpha_2 * alpha_3
        "puntaje_no_competencia": puntaje_no_competencia_raw,
        # Índice transformado mediante media geométrica
        "indice_no_competencia": indice_no_competencia,
        # Parámetro de intensidad
        "gamma_no_competencia": gamma_no_competencia,
        # Ajuste realmente aplicado: gamma * indice_no_competencia
        "ajuste_no_competencia_aplicado": ajuste_no_competencia_aplicado,
        # Factor multiplicativo: 1 + ajuste
        "factor_ajuste_no_competencia": factor_ajuste_no_competencia,
        "score_final_sin_tope": score_final_sin_tope,
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
        "exclusividad": st.slider("Peso: Exclusividad", 0, 30, 12),
        "duracion": st.slider("Peso: Duración en meses o equivalente", 0, 30, 10),
        "penalidades": st.slider("Peso: Penalidades / costos salida", 0, 30, 10),
        "clausulas_precio": st.slider("Peso: Restricciones de precio/promociones", 0, 30, 10),
        "control_operativo": st.slider("Peso: Control operativo", 0, 30, 10),
        "sancion_mayorista": st.slider("Peso: Sanción por parte del mayorista", 0, 30, 8),
        "datos_compartidos": st.slider("Peso: Intercambio info sensible", 0, 30, 20),
        "notificacion_tercero": st.slider("Peso: Notificación de propuesta de tercero", 0, 30, 10),
        "mejora_oferta_mayorista": st.slider("Peso: Mayorista mejora oferta de tercero", 0, 30, 10),
    }

    total_pesos = sum(w.values())
    st.caption(f"Suma actual de pesos: {total_pesos}")

    if total_pesos != 100:
        st.warning(
            "La suma de pesos no es 100. La herramienta normaliza automáticamente, "
            "pero para la versión metodológica se recomienda mantener la suma en 100."
        )
    
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
    competitors_df: pd.DataFrame = None,
    logo_somosuno_path: str = None
) -> io.BytesIO:
    """
    Genera un PDF ordenado con:
    1. Fecha de diligenciamiento
    2. Información de la EDS
    3. Mercado relevante y competidores
    4. Información diligenciada para el cálculo
    5. Resultado del cálculo
    6. Drivers principales
    7. Logos institucionales
    """

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    page_w, page_h = letter
    margin_x = 40
    top_y = page_h - 40
    bottom_limit = 80

    PRIMARY = HexColor("#000080")
    TEXT = HexColor("#0F172A")
    MUTED = HexColor("#475569")
    LIGHT_LINE = HexColor("#CBD5E1")

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    # -----------------------------
    # Funciones auxiliares
    # -----------------------------
    def draw_image_keep_ratio(path, x, y_top, max_width, max_height):
        """
        Dibuja una imagen conservando su proporción original.
        y_top corresponde al borde superior disponible.
        Retorna la altura efectivamente usada por la imagen.
        """
        try:
            with Image.open(path) as img:
                original_width, original_height = img.size

            if original_width <= 0 or original_height <= 0:
                return 0

            scale = min(max_width / original_width, max_height / original_height)
            draw_width = original_width * scale
            draw_height = original_height * scale

            c.drawImage(
                ImageReader(path),
                x,
                y_top - draw_height,
                width=draw_width,
                height=draw_height,
                mask="auto"
            )
            return draw_height
        except Exception:
            return 0

    def draw_footer(page_number: int):
        c.setStrokeColor(LIGHT_LINE)
        c.line(margin_x, 55, page_w - margin_x, 55)

        # Logos al pie
        try:
            if logo_somosuno_path:
                c.drawImage(
                    ImageReader(logo_somosuno_path),
                    margin_x,
                    15,
                    width=190,
                    height=42,
                    mask="auto"
                )
        except Exception:
            pass

        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawRightString(
            page_w - margin_x,
            25,
            f"Página {page_number} | Herramienta de Identificación de Riesgos de Pérdida de Competencia"
        )

    def draw_header():
        y = top_y

        # Logo principal conservando proporción original
        logo_height = 0
        if logo_path:
            logo_height = draw_image_keep_ratio(
                logo_path,
                margin_x,
                y,
                max_width=135,
                max_height=110
            )

        title_x = 185
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(title_x, y - 18, "Reporte de Riesgo – Contrato Mayorista/Minorista")

        c.setFont("Helvetica", 9)
        c.setFillColor(MUTED)
        c.drawString(title_x, y - 37, f"Fecha de diligenciamiento: {fecha}")

        # La línea queda por debajo del logo, incluso si el logo usa más alto.
        header_used_height = max(logo_height, 58)
        line_y = y - header_used_height - 18
        c.setStrokeColor(LIGHT_LINE)
        c.line(margin_x, line_y, page_w - margin_x, line_y)

        return line_y - 30

    def check_space(y, needed=40):
        nonlocal page_number
        if y - needed < bottom_limit:
            draw_footer(page_number)
            c.showPage()
            page_number += 1
            return draw_header()
        return y

    def section_title(y, title):
        y = check_space(y, 35)
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_x, y, title)
        y -= 14
        c.setStrokeColor(LIGHT_LINE)
        c.line(margin_x, y, page_w - margin_x, y)
        return y - 14

    def draw_key_value(y, key, value, x=50, key_width=120):
        y = check_space(y, 18)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y, f"{key}:")
        c.setFont("Helvetica", 9)
        c.drawString(x + key_width, y, str(value))
        return y - 13

    def wrap_canvas_text(text, max_width, font_name="Helvetica", font_size=9):
        """Parte un texto en líneas que caben dentro del ancho definido."""
        text = "" if pd.isna(text) else str(text)
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = f"{current} {word}".strip()
            if c.stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines if lines else [""]

    def draw_key_value_wrapped(y, key, value, x=50, value_x=320, label_width=250):
        """
        Dibuja preguntas largas sin que el texto invada la columna de respuesta.
        Se usa especialmente en la sección 3 del PDF.
        """
        label = f"{key}:"
        label_lines = wrap_canvas_text(label, label_width, "Helvetica-Bold", 8.5)
        needed = max(18, 11 * len(label_lines) + 4)
        y = check_space(y, needed)

        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 8.5)
        line_y = y
        for line in label_lines:
            c.drawString(x, line_y, line)
            line_y -= 10

        c.setFont("Helvetica", 8.5)
        c.drawString(value_x, y, str(value))

        return y - max(14, 10 * len(label_lines) + 3)

    def truncate_text(text, max_chars):
        text = "" if pd.isna(text) else str(text)
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."

    # -----------------------------
    # Inicio del documento
    # -----------------------------
    page_number = 1
    y = draw_header()

    # -----------------------------
    # 1. Información de la EDS
    # -----------------------------
    y = section_title(y, "1. Información de la EDS consultada")

    if eds_info is not None:
        y = draw_key_value(y, "SICOM", eds_info.get("SICOM", "N/D"))
        y = draw_key_value(y, "Nombre comercial", eds_info.get("NOMBRE COMERCIAL", "N/D"))
        y = draw_key_value(y, "Bandera", eds_info.get("BANDERA", "N/D"))
        y = draw_key_value(y, "Departamento", eds_info.get("DEPARTAMENTO", "N/D"))
        y = draw_key_value(y, "Municipio", eds_info.get("MUNICIPIO", "N/D"))
    else:
        y = draw_key_value(y, "Información", "No disponible")

    y -= 8

    # -----------------------------
    # 2. Mercado relevante
    # -----------------------------
    y = section_title(y, "2. Mercado relevante y competidores")

    n_comp = 0 if competitors_df is None else len(competitors_df)
    y = draw_key_value(y, "Competidores identificados", n_comp)

    if competitors_df is not None and not competitors_df.empty:
        y -= 4
        y = check_space(y, 35)

        # Encabezado tabla
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y, "COMPETIDOR")
        c.drawString(135, y, "NOMBRE COMERCIAL")
        c.drawString(420, y, "BANDERA")
        y -= 8

        c.setStrokeColor(LIGHT_LINE)
        c.line(50, y, page_w - 50, y)
        y -= 10

        c.setFillColor(TEXT)
        c.setFont("Helvetica", 8)

        for _, row in competitors_df.iterrows():
            y = check_space(y, 18)

            comp = truncate_text(row.get("COMPETIDOR", ""), 14)
            nom = truncate_text(row.get("NOMBRE_COMERCIAL_COMPETIDOR", ""), 55)
            bandera = truncate_text(row.get("BANDERA_COMPETIDOR", ""), 18)

            c.drawString(50, y, comp)
            c.drawString(135, y, nom)
            c.drawString(420, y, bandera)

            y -= 11
    else:
        y = draw_key_value(y, "Competidores", "No se identificaron competidores para el SICOM consultado")

    y -= 10

    # -----------------------------
    # 3. Información diligenciada
    # -----------------------------
    y = section_title(y, "3. Información diligenciada para el cálculo")

    inputs = res.get("inputs", {})

    labels_inputs = {
        "exclusividad": "Cláusula de exclusividad",
        "tipo_duracion": "Tipo de duración",
        "duracion_meses": "Duración en meses o equivalente",
        "penalidades": "Penalidades o costos de salida",
        "clausulas_precio": "Restricciones sobre precios/promociones",
        "control_operativo": "Control operativo del mayorista",
        "sancion_mayorista": "Sanción por parte del mayorista",
        "datos_compartidos": "Intercambio de información sensible",
        "notificacion_tercero": "Obligación de notificar propuesta de tercero",
        "mejora_oferta_mayorista": "Mayorista mejora propuesta de tercero",
        "precio_bajo_margen": "EDS verticalizadas venden por debajo del margen de referencia",
        "tribunal_sin_arreglo": "Tribunal de arbitramento sin instancia previa efectiva",
    }

    for k, label in labels_inputs.items():
        y = draw_key_value_wrapped(
            y,
            label,
            inputs.get(k, "N/D"),
            x=50,
            value_x=330,
            label_width=265
        )

    y -= 10

    # -----------------------------
    # 4. Resultado del cálculo
    # -----------------------------
    y = section_title(y, "4. Resultado del cálculo")

    y = check_space(y, 95)
    result_top_y = y

    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Puntaje de riesgo:")
    c.setFont("Helvetica", 10)
    c.drawString(190, y, f"{res['score']:.1f} / 100")

    y -= 16

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Probabilidad estimada:")
    c.setFont("Helvetica", 10)
    c.drawString(190, y, f"{100 * res['p']:.1f}%")

    y -= 16

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Semáforo:")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawString(190, y, res["label"])

    y -= 16

    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Clasificación:")
    c.setFont("Helvetica", 10)
    c.drawString(190, y, res["bucket"])

    # Círculo visual del semáforo en el lado derecho del bloque de resultados
    circle_color = HexColor(res.get("color_hex", "#94A3B8"))
    circle_x = page_w - margin_x - 145
    circle_y = result_top_y - 25
    c.setFillColor(circle_color)
    c.circle(circle_x, circle_y, 24, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#334155"))
    c.setLineWidth(0.8)
    c.circle(circle_x, circle_y, 24, stroke=1, fill=0)

    y -= 22

    # -----------------------------
    # 5. Lectura rápida del resultado
    # -----------------------------
    y = section_title(y, "5. Lectura rápida del resultado")

    y = check_space(y, 70)

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 9)

    if res["bucket"] == "Bajo":
        texto_lectura = (
            "El contrato presenta una baja concentración de factores contractuales sensibles, "
            "según la parametrización de la herramienta. Se recomienda conservar este reporte "
            "como soporte y realizar seguimiento si se modifican las condiciones contractuales."
        )
    elif res["bucket"] == "Medio":
        texto_lectura = (
            "El contrato presenta elementos que justifican una revisión preventiva. "
            "Se recomienda analizar con mayor detalle las condiciones contractuales antes de renovar, "
            "modificar o suscribir nuevos compromisos."
        )
    else:
        texto_lectura = (
            "El contrato presenta una combinación de condiciones que amerita una revisión técnica detallada. "
            "Se recomienda evaluar el alcance de las cláusulas, su justificación económica y sus posibles efectos "
            "sobre la autonomía competitiva del minorista."
        )

    # Escritura simple en varias líneas
    lineas = []
    max_chars = 95
    while len(texto_lectura) > max_chars:
        corte = texto_lectura[:max_chars].rfind(" ")
        if corte == -1:
            corte = max_chars
        lineas.append(texto_lectura[:corte])
        texto_lectura = texto_lectura[corte:].strip()
    lineas.append(texto_lectura)
    
    for linea in lineas:
        y = check_space(y, 14)
        c.drawString(50, y, linea)
        y -= 12

    y -= 8
    y = check_space(y, 35)

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(MUTED)
    c.drawString(
        margin_x,
        y,
        "Nota: esta herramienta prioriza contratos para revisión técnica. No constituye una determinación de infracción."
    )

    # Footer última página
    draw_footer(page_number)

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
        "Puntaje_contractual": round(res.get("score_preguntas", res["score"]), 2),
        "Ajuste_no_competencia_%": round(100 * res.get("puntaje_no_competencia", 0.0), 4),
        "Puntaje_final": round(res["score"], 2),
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


# ======================================================
# FOOTER – Logos institucionales
# ======================================================

def render_footer():
    st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        try:
            st.image(Image.open(LOGO_SOMOSUNO_PATH), width=520)
        except Exception:
            pass

    st.caption(
        "Herramienta desarrollada en el marco del estudio sobre acuerdos verticales "
        "en la distribución minorista de combustibles líquidos – Fondo SOLDICOM / FENDIPETRÓLEO / COMCE."
        " © 2026"
    )

# ======================================================
# HISTÓRICO EN GOOGLE SHEETS
# ======================================================

HISTORY_HEADERS = [
    "Fecha y Hora",
    "Puntaje_contractual",
    "Ajuste_no_competencia_%",
    "Puntaje_no_competencia_raw",
    "Indice_no_competencia",
    "Gamma_no_competencia",
    "Factor_ajuste_no_competencia",
    "Puntaje_final",
    "Probabilidad_%",
    "Semáforo",
    "Bucket",
    "SICOM",
    "Nombre_EDS",
    "Bandera_EDS",
    "Departamento",
    "Municipio",
    "Numero_competidores",
    "ALPHA_1",
    "ALPHA_2",
    "ALPHA_3",
    "valor_exclusividad",
    "valor_tipo_duracion",
    "valor_duracion_meses",
    "valor_penalidades",
    "valor_clausulas_precio",
    "valor_control_operativo",
    "valor_sancion_mayorista",
    "valor_datos_compartidos",
    "valor_notificacion_tercero",
    "valor_mejora_oferta_mayorista",
    "valor_precio_bajo_margen",
    "valor_tribunal_sin_arreglo",
]


@st.cache_resource(show_spinner=False)
def get_gsheet_worksheet():
    """
    Conecta con Google Sheets usando credenciales guardadas en Streamlit Secrets.
    """

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    service_account_info = dict(st.secrets["gcp_service_account"])

    # Evita errores con saltos de línea en private_key
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet_id = st.secrets["gcp_sheet"]["spreadsheet_id"]
    worksheet_name = st.secrets["gcp_sheet"].get("worksheet_name", "Historico")

    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=len(HISTORY_HEADERS)
        )

    return worksheet


def ensure_history_headers(worksheet):
    """
    Crea encabezados si la hoja está vacía.
    """

    first_row = worksheet.row_values(1)

    if not first_row:
        worksheet.append_row(
            HISTORY_HEADERS,
            value_input_option="USER_ENTERED"
        )


def build_history_row(res: dict, eds_info: dict, competitors_df: pd.DataFrame) -> list:
    """
    Construye una fila del histórico con la estructura requerida.
    """

    inputs = res.get("inputs", {})

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        round(res.get("score_preguntas", res.get("score", 0)), 4),
        round(100 * res.get("ajuste_no_competencia_aplicado", 0.0), 6),
        round(res.get("puntaje_no_competencia", 0.0), 8),
        round(res.get("indice_no_competencia", 0.0), 8),
        round(res.get("gamma_no_competencia", 0.0), 8),
        round(res.get("factor_ajuste_no_competencia", 1.0), 8),
        round(res.get("score", 0), 4),
        round(100 * res.get("p", 0), 4),
        res.get("label", ""),
        res.get("bucket", ""),
        eds_info.get("SICOM", "") if eds_info else "",
        eds_info.get("NOMBRE COMERCIAL", "") if eds_info else "",
        eds_info.get("BANDERA", "") if eds_info else "",
        eds_info.get("DEPARTAMENTO", "") if eds_info else "",
        eds_info.get("MUNICIPIO", "") if eds_info else "",
        eds_info.get("COMPETIDORES_IDENTIFICADOS", 0) if eds_info else 0,
        round(eds_info.get("ALPHA_1", 0.0), 6) if eds_info else 0,
        round(eds_info.get("ALPHA_2", 0.0), 6) if eds_info else 0,
        round(eds_info.get("ALPHA_3", 0.0), 6) if eds_info else 0,
        inputs.get("exclusividad", ""),
        inputs.get("tipo_duracion", ""),
        inputs.get("duracion_meses", ""),
        inputs.get("penalidades", ""),
        inputs.get("clausulas_precio", ""),
        inputs.get("control_operativo", ""),
        inputs.get("sancion_mayorista", ""),
        inputs.get("datos_compartidos", ""),
        inputs.get("notificacion_tercero", ""),
        inputs.get("mejora_oferta_mayorista", ""),
        inputs.get("precio_bajo_margen", ""),
        inputs.get("tribunal_sin_arreglo", ""),
    ]

    return row


def save_result_to_history(res: dict, eds_info: dict, competitors_df: pd.DataFrame) -> bool:
    """
    Guarda una evaluación en el Google Sheet histórico.
    Devuelve True si guardó correctamente y False si falló.
    """

    try:
        worksheet = get_gsheet_worksheet()
        ensure_history_headers(worksheet)

        row = build_history_row(
            res=res,
            eds_info=eds_info,
            competitors_df=competitors_df
        )

        worksheet.append_row(
            row,
            value_input_option="USER_ENTERED"
        )

        return True

    except Exception as e:
        st.session_state["history_error"] = str(e)
        return False

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
    st.markdown(
        """
        <style>
        div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p {
            color: #1A3D75 !important;
            font-weight: 500 !important;
        }

        div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] strong {
            color: #1A3D75 !important;
            font-weight: 800 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
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
    render_footer()
    
# -----------------------------
# STEP 2: Forma y Estructura
# -----------------------------
elif st.session_state.step == 2:
    step_badge()
    st.markdown('<div class="card">', unsafe_allow_html=True)
#    st.header("Ingreso de información del contrato")

    # -----------------------------
    # Información de la EDS y mercado relevante
    # -----------------------------
    if st.session_state.eds_info is not None:
        eds = st.session_state.eds_info
        competitors_df = st.session_state.competitors_df

        st.subheader("EDS consultada y mercado relevante")

        nombre_eds = eds.get("NOMBRE COMERCIAL", "N/D")
        sicom_eds = eds.get("SICOM", "N/D")
        bandera_eds = eds.get("BANDERA", "N/D")
        departamento_eds = eds.get("DEPARTAMENTO", "N/D")
        municipio_eds = eds.get("MUNICIPIO", "N/D")
        n_competidores = eds.get("COMPETIDORES_IDENTIFICADOS", len(competitors_df))

        st.markdown(f"""
        <div style="
            background:#FFFFFF;
            border:1px solid rgba(15,23,42,0.08);
            border-radius:14px;
            padding:14px 18px;
            margin-bottom:12px;
            box-shadow:0 4px 12px rgba(15,23,42,0.06);
        ">
            <p style="margin:0; color:#0F172A; font-size:15px;">
                <b>Nombre comercial:</b> {nombre_eds} &nbsp; | &nbsp;
                <b>SICOM:</b> {sicom_eds} &nbsp; | &nbsp;
                <b>Bandera:</b> {bandera_eds}
            </p>
            <p style="margin:6px 0 0 0; color:#0F172A; font-size:15px;">
                <b>Departamento:</b> {departamento_eds} &nbsp; | &nbsp;
                <b>Municipio:</b> {municipio_eds} &nbsp; | &nbsp;
                <b>Competidores identificados:</b> {n_competidores}
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Ver competidores del mercado relevante"):
            render_competitors_table(competitors_df)
        
        st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

    else:
        st.warning("No se ha ingresado un código SICOM. Vuelve al paso anterior para identificar la EDS.")
        if st.button("⟵ Volver a bienvenida"):
            go(1)
            st.rerun()
        render_footer()
        st.stop()

    st.header("Ingreso de información del contrato")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("Estructura")

        exclusividad = st.selectbox(
            "¿Hay cláusula de exclusividad?",
            ["No", "Sí"]
        )

        tipo_duracion = st.radio(
            "¿La duración está definida en cantidad o tiempo?",
            ["Tiempo", "Cantidad"],
            index=None,
            horizontal=True,
            help=(
                "Seleccione 'Tiempo' si el contrato fija una duración temporal. "
                "Seleccione 'Cantidad' si la duración depende de volumen, cupos, galones u otra unidad, "
                "y registre abajo su equivalente aproximado en meses."
            )
        )

        duracion_meses = st.number_input(
            "Duración en meses o equivalente",
            min_value=0,
            max_value=240,
            value=36,
            step=1,
            help=(
                "Ingrese la duración en meses. Si la duración está definida por cantidad, "
                "registre una equivalencia temporal estimada."
            )
        )

        penalidades = st.selectbox(
            "¿Existen penalidades/costos de salida relevantes?",
            ["No", "Sí"]
        )

        tribunal_sin_arreglo = st.selectbox(
            "¿Ante diferencias con el mayorista, la EDS debe acudir directamente a la cláusula de resolución de conflictos por tribunal de arbitramento, sin contar con una instancia previa efectiva de arreglo directo o conciliación?",
            ["No", "Sí"],
            help=(
                "Pregunta de contexto. Se registra para trazabilidad y análisis descriptivo, "
                "pero no afecta el cálculo del puntaje contractual."
            )
        )

    with c2:
        st.subheader("Conducta / incentivos")
        clausulas_precio = st.selectbox(
            "¿Hay restricciones sobre precios/promociones o alineación obligatoria?",
            ["No", "Sí"]
        )

        control_operativo = st.selectbox(
            "¿El mayorista impone control operativo (inventario, proveedores, branding rígido, etc.)?",
            ["No", "Sí"]
        )

        sancion_mayorista = st.selectbox(
            "¿Ha sido usted sancionado por el mayorista?",
            ["No", "Sí"],
            help=(
                "Marque 'Sí' si el mayorista le ha impuesto sanciones, multas, penalidades operativas "
                "o medidas disciplinarias asociadas al cumplimiento del contrato."
            )
        )

        precio_bajo_margen = st.selectbox(
            "¿En el mismo corredor o mercado relevante de su EDS operan EDS verticalizadas que vendan combustibles por debajo del margen de referencia definido o reconocido por la autoridad competente?",
            ["No", "Sí"],
            help=(
                "Pregunta de contexto. Se registra para trazabilidad y análisis descriptivo, "
                "pero no afecta el cálculo del puntaje contractual."
            )
        )

    with c3:
        st.subheader("Información")
        datos_compartidos = st.selectbox(
            "¿Se comparte información sensible (ventas, márgenes, estrategias locales)?", ["No", "Sí"]
        )
        
        notificacion_tercero = st.selectbox(
            "Cuando un tercero demuestra interés en su EDS, ¿está obligado a notificar a su mayorista sobre esa propuesta?",
            ["No", "Sí"]
        )
        
        mejora_oferta_mayorista = st.selectbox(
            "En la vida práctica, ¿el mayorista presenta ofertas que mejoran la propuesta del tercero?",
            ["No", "Sí"]
        )

    st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

    col_back, col_calc = st.columns([1, 1])
    with col_back:
        if st.button("⟵ Volver"):
            go(1)
            st.rerun()

    with col_calc:
        if st.button("Calcular"):

            # Si el usuario no marca Tiempo/Cantidad, se registra como "No especificado"
            tipo_duracion_final = tipo_duracion if tipo_duracion is not None else "No especificado"

            inputs = {
                "exclusividad": exclusividad,
                "tipo_duracion": tipo_duracion_final,
                "duracion_meses": int(duracion_meses),
                "penalidades": penalidades,
                "clausulas_precio": clausulas_precio,
                "control_operativo": control_operativo,
                "sancion_mayorista": sancion_mayorista,
                "datos_compartidos": datos_compartidos,
                "notificacion_tercero": notificacion_tercero,
                "mejora_oferta_mayorista": mejora_oferta_mayorista,
                "precio_bajo_margen": precio_bajo_margen,
                "tribunal_sin_arreglo": tribunal_sin_arreglo,
            }

            puntaje_no_competencia = 0.0

            if st.session_state.get("eds_info") is not None:
                puntaje_no_competencia = float(
                    st.session_state.eds_info.get("PUNTAJE_NO_COMPETENCIA", 0.0)
                )

            res_tmp = compute_score(
                params=params,
                inputs=inputs,
                puntaje_no_competencia=puntaje_no_competencia
            )

            st.session_state.result = res_tmp

            # Guardar histórico en Google Sheets
            history_saved = save_result_to_history(
                res=res_tmp,
                eds_info=st.session_state.get("eds_info", {}),
                competitors_df=st.session_state.get("competitors_df", pd.DataFrame())
            )

            st.session_state["history_saved"] = history_saved

            go(3)
            st.rerun()


    st.markdown("</div>", unsafe_allow_html=True)
    
    render_footer()
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
            st.rerun()
        render_footer()
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
                        <b>Competidores identificados:</b> {eds_info.get("COMPETIDORES_IDENTIFICADOS", len(competitors_df))}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.expander("Ver competidores del mercado relevante"):
                render_competitors_table(competitors_df)
            
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
            st.subheader("Resultado de la evaluación")

            st.write(f"**Puntaje contractual:** {res.get('score_preguntas', res['score']):.1f} / 100")
#            st.write(f"**Índice de no competencia:** {100*res.get('indice_no_competencia', 0.0):.2f}%")
#            st.write(f"**Intensidad del ajuste:** {res.get('gamma_no_competencia', 0.0):.3f}")
#            st.write(f"**Ajuste aplicado al puntaje contractual:** {100*res.get('ajuste_no_competencia_aplicado', 0.0):.2f}%")
            st.write(f"**Puntaje final de riesgo:** {res['score']:.1f} / 100")
            st.write(f"**Probabilidad estimada de riesgo:** {100*res['p']:.1f}%")
            st.write(f"**Clasificación:** {res['bucket']}")

#            st.info(
#                "El resultado tiene carácter preventivo y orientador. "
#                "No constituye una determinación de infracción ni sustituye un análisis jurídico-económico de fondo."
#            )


            st.markdown(
                """
                <style>
                div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p {
                    color: #1A3D75 !important;
                    font-weight: 500 !important;
                }

                div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] strong {
                    color: #1A3D75 !important;
                    font-weight: 800 !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            st.info(
                "El resultado tiene carácter **preventivo y orientador**. "
                "No constituye una determinación de infracción ni sustituye un análisis jurídico-económico de fondo."
            )


        with right:
            st.subheader("Acciones")

            if st.button("⟵ Modificar respuestas"):
                go(2)
                st.rerun()

            if st.button("✅ Finalizar"):
                reset_app()
                st.rerun()

            st.markdown("")

            
            # Exportación (PDF y Excel)
            eds_info_report = st.session_state.get("eds_info", None)
            competitors_report = st.session_state.get("competitors_df", pd.DataFrame())

            pdf_buffer = build_pdf_report(
                res,
                logo_path=LOGO_PATH,
                eds_info=eds_info_report,
                competitors_df=competitors_report,
                logo_somosuno_path=LOGO_SOMOSUNO_PATH
            )

#            xlsx_buffer = build_excel_report(
#                res,
#                eds_info=eds_info_report,
#                competitors_df=competitors_report
#            )

            st.download_button(
                label="📄 Exportar a PDF",
                data=pdf_buffer,
                file_name=f"reporte_riesgo_soldicom_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )

#            st.download_button(
#                label="📊 Exportar a Excel",
#                data=xlsx_buffer,
#                file_name=f"reporte_riesgo_soldicom_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
#                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#            )

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

                    st.markdown("**Lectura operativa del resultado:**")

                    if res["bucket"] == "Bajo":
                        st.write(
                            "El contrato presenta una baja concentración de factores contractuales sensibles, "
                            "según la parametrización de la herramienta. Se recomienda conservar el reporte como soporte "
                            "y realizar seguimiento si se modifican las condiciones contractuales."
                        )

                    elif res["bucket"] == "Medio":
                        st.write(
                            "El contrato presenta elementos que justifican una revisión preventiva. "
                            "Se recomienda analizar con mayor detalle las condiciones contractuales antes de renovar, modificar "
                            "o suscribir nuevos compromisos."
                        )

                    else:
                        st.write(
                            "El contrato presenta una combinación de condiciones que amerita una revisión técnica detallada. "
                            "Se recomienda evaluar el alcance de las cláusulas, su justificación económica y sus posibles efectos "
                            "sobre la autonomía competitiva del minorista."
                        )

                    st.markdown(
                        """
                        **Interpretación operativa:**
                        Un mayor número de factores activados o una mayor contribución acumulada sugiere la conveniencia de
                        realizar una **revisión técnica más detallada del contrato**, considerando su contexto económico y regulatorio.
                        """
                    )

#                    st.info(
#                        "Nota: esta herramienta tiene un carácter preventivo y orientador. "
#                        "El semáforo no constituye una determinación de infracción ni sustituye el análisis jurídico o económico de fondo."
#                    )
                    st.markdown(
                        """
                        <div class="modal-note">
                            <p style="font-size:16px; line-height:1.6; margin:0; font-weight:500;">
                                <strong>Nota:</strong>
                                esta herramienta tiene un carácter preventivo y orientador.
                                El semáforo no constituye una determinación de infracción ni sustituye
                                el análisis jurídico o económico de fondo.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    

                if st.button("📌 Lectura rápida de los resultados"):
                    lectura_rapida_dialog()

            else:
                with st.expander("📌 Lectura rápida de los resultados"):
                    st.write(
                        "Este resultado sintetiza los **principales elementos contractuales** que, de acuerdo con la "
                        "parametrización actual del modelo, **incrementan el riesgo potencial de afectación a la competencia**."
                    )

                    st.markdown("**Lectura operativa del resultado:**")

                    if res["bucket"] == "Bajo":
                        st.write(
                            "El contrato presenta una baja concentración de factores contractuales sensibles, "
                            "según la parametrización de la herramienta. Se recomienda conservar el reporte como soporte "
                            "y realizar seguimiento si se modifican las condiciones contractuales."
                        )
                    elif res["bucket"] == "Medio":
                        st.write(
                            "El contrato presenta elementos que justifican una revisión preventiva. "
                            "Se recomienda analizar con mayor detalle las condiciones contractuales antes de renovar, modificar "
                            "o suscribir nuevos compromisos."
                        )
                    else:
                        st.write(
                            "El contrato presenta una combinación de condiciones que amerita una revisión técnica detallada. "
                            "Se recomienda evaluar el alcance de las cláusulas, su justificación económica y sus posibles efectos "
                            "sobre la autonomía competitiva del minorista."
                        )

                    st.markdown(
                        """
                        **Interpretación operativa:**
                        Un mayor número de factores activados o una mayor contribución acumulada sugiere la conveniencia de
                        realizar una **revisión técnica más detallada del contrato**, considerando su contexto económico y regulatorio.
                        """
                    )

                    st.markdown(
                        """
                        <div class="modal-note">
                            <p style="font-size:16px; line-height:1.6; margin:0; font-weight:500;">
                                <strong>Nota:</strong>
                                esta herramienta tiene un carácter preventivo y orientador.
                                El semáforo no constituye una determinación de infracción ni sustituye
                                el análisis jurídico o económico de fondo.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


        st.markdown("</div>", unsafe_allow_html=True)
        render_footer()

# ======================================================
# FOOTER – Logos institucionales (al final de todo)
# ======================================================

#st.markdown('<hr class="soft-hr"/>', unsafe_allow_html=True)

#col1, col2, col3 = st.columns([1, 3, 1])

#with col2:
#    try:
#        st.image(Image.open(LOGO_SOMOSUNO_PATH), width=520)
#    except Exception:
#        pass

#st.caption(
#    "Herramienta desarrollada en el marco del estudio sobre acuerdos verticales "
#    "en la distribución minorista de combustibles líquidos – Fondo SOLDICOM / FENDIPETRÓLEO / COMCE."
#    " © 2026"
#)
