import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
from PIL import Image
import io
import base64
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
   - Fondo de pantalla: transparente con sombra suave
   - Caja flotante: azul oscuro sólido
   ========================= */

/* El contenedor externo del modal cubre toda la pantalla; debe quedar transparente. */
div[data-baseweb="modal"],
div[data-testid="stDialog"],
div[data-testid="stModal"] {{
    background-color: transparent !important;
    background: transparent !important;
}}

/* Capa de oscurecimiento suave para que se vea el aplicativo detrás. */
div[data-baseweb="modal"]::before,
div[data-testid="stDialog"]::before,
div[data-testid="stModal"]::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.34) !important;
    pointer-events: none;
    z-index: -1;
}}

/* Caja real del modal: esta sí debe ser azul oscuro sólido. */
div[role="dialog"] {{
    background-color: #0F172A !important;
    background: #0F172A !important;
    color: #F8FAFC !important;
    border-radius: 22px !important;
    border: 1px solid rgba(148, 163, 184, 0.55) !important;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.38) !important;
}}

/* Contenedores internos del modal: también en azul oscuro para evitar el gris/transparente. */
div[role="dialog"] > div,
div[role="dialog"] > div > div,
div[role="dialog"] section,
div[role="dialog"] form,
div[role="dialog"] div[data-testid="stForm"],
div[role="dialog"] div[data-testid="stVerticalBlock"],
div[role="dialog"] div[data-testid="stVerticalBlockBorderWrapper"],
div[role="dialog"] div[data-testid="stElementContainer"] {{
    background-color: #0F172A !important;
    background: #0F172A !important;
}}

/* El formulario conserva borde, pero no pinta un fondo gris. */
div[role="dialog"] div[data-testid="stForm"] {{
    border: 1px solid rgba(148, 163, 184, 0.45) !important;
    border-radius: 10px !important;
}}

/* Texto dentro de las ventanas flotantes. */
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

/* Títulos de ventanas flotantes. */
div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3,
div[role="dialog"] h4 {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
}}

/* Campo del código SICOM dentro del modal. */
div[role="dialog"] input,
div[role="dialog"] textarea {{
    color: #F8FAFC !important;
    background-color: #1E293B !important;
    border: 1px solid #64748B !important;
    border-radius: 10px !important;
}}

div[role="dialog"] input::placeholder,
div[role="dialog"] textarea::placeholder {{
    color: #CBD5E1 !important;
    opacity: 1 !important;
}}

/* Botones dentro de ventanas flotantes. */
div[role="dialog"] button {{
    color: #FFFFFF !important;
    border-color: #64748B !important;
}}

/* Nota dentro de lectura rápida: azul más claro, texto blanco. */
div[role="dialog"] .modal-note {{
    background-color: #1E497D !important;
    background: #1E497D !important;
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

# Refuerzo final para ventanas emergentes (Paso 1 y Lectura rápida).
# Este bloque va después del CSS general para que tenga prioridad sobre los estilos globales.
st.markdown("""
<style>
/* Fondo externo del modal: deja ver la herramienta detrás */
div[data-baseweb="modal"],
div[data-testid="stDialog"],
div[data-testid="stModal"] {
    background: transparent !important;
    background-color: transparent !important;
}

/* Capa de oscurecimiento suave, no azul sólido */
div[data-baseweb="modal"]::before,
div[data-testid="stDialog"]::before,
div[data-testid="stModal"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.34) !important;
    pointer-events: none;
    z-index: -1;
}

/* Caja flotante del modal */
div[data-baseweb="modal"] div[role="dialog"],
div[role="dialog"] {
    background: #0F172A !important;
    background-color: #0F172A !important;
    border-radius: 22px !important;
    border: 1px solid rgba(148, 163, 184, 0.55) !important;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.42) !important;
}

/* Texto del modal: forzar blanco, incluyendo títulos automáticos de st.dialog */
div[data-baseweb="modal"] div[role="dialog"] *,
div[role="dialog"] * {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    opacity: 1 !important;
}

/* Títulos y botón de cierre */
div[data-baseweb="modal"] div[role="dialog"] h1,
div[data-baseweb="modal"] div[role="dialog"] h2,
div[data-baseweb="modal"] div[role="dialog"] h3,
div[data-baseweb="modal"] div[role="dialog"] h4,
div[data-baseweb="modal"] div[role="dialog"] [data-testid="stMarkdownContainer"] h1,
div[data-baseweb="modal"] div[role="dialog"] [data-testid="stMarkdownContainer"] h2,
div[data-baseweb="modal"] div[role="dialog"] [data-testid="stMarkdownContainer"] h3,
div[data-baseweb="modal"] div[role="dialog"] [data-testid="stMarkdownContainer"] h4,
div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3,
div[role="dialog"] h4 {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 800 !important;
}

/* Contenedores internos transparentes para no tapar la caja azul */
div[data-baseweb="modal"] div[role="dialog"] > div,
div[data-baseweb="modal"] div[role="dialog"] section,
div[data-baseweb="modal"] div[role="dialog"] form,
div[data-baseweb="modal"] div[role="dialog"] div[data-testid="stVerticalBlock"],
div[data-baseweb="modal"] div[role="dialog"] div[data-testid="stElementContainer"],
div[role="dialog"] > div,
div[role="dialog"] section,
div[role="dialog"] form,
div[role="dialog"] div[data-testid="stVerticalBlock"],
div[role="dialog"] div[data-testid="stElementContainer"] {
    background: transparent !important;
    background-color: transparent !important;
}

/* Formulario del SICOM */
div[data-baseweb="modal"] div[role="dialog"] div[data-testid="stForm"],
div[role="dialog"] div[data-testid="stForm"] {
    background: transparent !important;
    border: 1px solid rgba(148, 163, 184, 0.45) !important;
    border-radius: 10px !important;
}

/* Inputs */
div[data-baseweb="modal"] div[role="dialog"] input,
div[role="dialog"] input,
div[data-baseweb="modal"] div[role="dialog"] textarea,
div[role="dialog"] textarea {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    background-color: #1E293B !important;
    border: 1px solid #64748B !important;
    border-radius: 10px !important;
}

div[data-baseweb="modal"] div[role="dialog"] input::placeholder,
div[role="dialog"] input::placeholder,
div[data-baseweb="modal"] div[role="dialog"] textarea::placeholder,
div[role="dialog"] textarea::placeholder {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
    opacity: 1 !important;
}

/* Botones */
div[data-baseweb="modal"] div[role="dialog"] button,
div[role="dialog"] button {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: #64748B !important;
}

/* Nota de lectura rápida */
div[data-baseweb="modal"] div[role="dialog"] .modal-note,
div[role="dialog"] .modal-note {
    background: #1E497D !important;
    background-color: #1E497D !important;
    border-radius: 14px !important;
    padding: 22px 24px !important;
    margin-top: 18px !important;
}

div[data-baseweb="modal"] div[role="dialog"] .modal-note *,
div[role="dialog"] .modal-note * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)



# CSS final de máxima prioridad para: botón de ayuda y ventanas emergentes.
st.markdown("""
<style>
/* Botón de ayuda: fondo azul y letra blanca siempre */
div[data-testid="stDownloadButton"] button,
div[data-testid="stDownloadButton"] button *,
div[data-testid="stDownloadButton"] p,
div[data-testid="stDownloadButton"] span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    text-decoration: none !important;
    font-weight: 800 !important;
}

/* Modal: caja azul sólida, fondo exterior transparente con overlay */
div[data-baseweb="modal"] {
    background: transparent !important;
    background-color: transparent !important;
}

div[data-baseweb="modal"] > div:first-child {
    background: rgba(15, 23, 42, 0.34) !important;
    background-color: rgba(15, 23, 42, 0.34) !important;
}

div[data-baseweb="modal"] div[role="dialog"],
div[role="dialog"] {
    background: #0F172A !important;
    background-color: #0F172A !important;
    border-radius: 22px !important;
    border: 1px solid rgba(148, 163, 184, 0.55) !important;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.42) !important;
}

/* Oculta el título automático de st.dialog cuando esté vacío o heredado */
div[data-baseweb="modal"] div[role="dialog"] h1:first-child,
div[data-baseweb="modal"] div[role="dialog"] h2:first-child {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Todo texto del modal en blanco, con prioridad máxima */
div[data-baseweb="modal"] div[role="dialog"] *,
div[role="dialog"] *,
div[role="dialog"] .stMarkdown,
div[role="dialog"] .stMarkdown *,
div[role="dialog"] [data-testid="stMarkdownContainer"],
div[role="dialog"] [data-testid="stMarkdownContainer"] * {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    opacity: 1 !important;
}

/* Títulos personalizados de los modales */
div[role="dialog"] .modal-custom-title,
div[role="dialog"] .modal-custom-title * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 28px !important;
    font-weight: 850 !important;
    line-height: 1.2 !important;
    margin-bottom: 26px !important;
}

div[role="dialog"] .modal-custom-text,
div[role="dialog"] .modal-custom-text * {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-size: 17px !important;
    line-height: 1.55 !important;
}

/* Inputs del modal */
div[role="dialog"] input,
div[role="dialog"] textarea {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    background-color: #1E293B !important;
}

div[role="dialog"] input::placeholder,
div[role="dialog"] textarea::placeholder {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
}

/* Nota de lectura rápida */
div[role="dialog"] .modal-note,
div[role="dialog"] .modal-note * {
    background-color: #1E497D !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
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

GUIA_USO_PATH = resolve_path(
    "/mnt/data/guia_rapida_identificacion_riesgos.pdf",
    "assets/guia_rapida_identificacion_riesgos.pdf"
)

# Respaldo embebido del PDF de ayuda. Así el botón funciona aunque el archivo no esté en assets.
GUIA_USO_PDF_B64_EMBEDDED = """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0X86fRRoBH50X/PRfzo8+L/nov51JRRoBH58X/PRfzpfOi/56L+dPoo0AZ50X/PRfzo86L/nov50+ijQCPz4v+ei/nR58X/PRfzqSijQCPz4v+ei/nR50X/PRfzqSko0AZ50X/PRfzpfOi/56L+dPoo0AZ50X/PRfzpPOi/56L+dSUUaAR+dF/z0X86Xzo/+ei/nT6KNAGedF/z0X86POi/56L+dOpaNAGedF/z0X86Tzov+ei/nUlFGgEfnRf8APRfzo8+L/nov51JRRoIj86L/AJ6L+dHnRf8APRfzqSijQYzzov8Anov50edF/wA9F/On0UaAM86L/nov50nnxf8APRfzqSijQCPzov8Anov50edF/wA9F/OpKSjQQ3zo/wDnov50edF/z0X86fRRoMj86L/nov50edF/z0X86koo0Aj86L/nov50vnRf89F/On0UaAM86L/nov50nnRf89F/OpKKNAI/Oi/56L+dHnRf89F/OpKKNAGedF/z0X86POi/56L+dPoo0EM86L/nov50nnRf89F/OpKKNBkfnRf89F/Ojz4v+ei/nUlFGgEfnxf89F/Ol86L/nov50+ijQCPzov+ei/nS+dH/wA9F/On0UaAM86L/nov50edF/z0X86fRRoBH50X/PRfzpfOi/56L+dPoo0Aj86L/nov50vnRf8APRfzp9FGgDPOi/56L+dJ50X/AD0X86koo0AZ50X/AD0X86Tzov8Anov51JRRoBH58X/PRfzo8+L/AJ6L+dSUUaAR+fD/AM9F/Ojz4v8Anov51JRRoAzzov8Anov50nnxf89F/OpKKNAI/Pi/56L+dL50X/PRfzp9FGgDPOi/56L+dHnRf89F/On0UaAM86L/AJ6L+dHnRf8APRfzp9FGgDPOi/56L+dHnxf89F/On0UaAR+fF/z0X86PPi/56L+dSUUaAR+fF/z0X86PPi/56L+dSUUaAR+fF/z0X86Xzov+ei/nT6OtGgDPPi/56L+dJ58X/PRfzqSijQCPz4v+ei/nR58X/PRfzqSijQCPz4v+ei/nR58X/PRfzqSijQRH58X/AD0X86Xzov8Anov50+ijQZH58X/PRfzo8+L/AJ6L+dSUUaAM8+L/AJ6L+dJ58X/PRfzqSijQCPz4v+ei/nS+dF/z0X86fRRoAzzov+ei/nSefF/z0X86koo0Aj8+L/nov50vnRf89F/On0UaAM86L/nov50edF/z0X86fRRoIj8+L/nov50efF/z0X86koo0GR+fF/z0X86PPi/56L+dSUUaAR+fF/z0X86PPi/56L+dSUUaAM8+L/nov50edF/z0X86fRRoAzz4v+ei/nR58X/PRfzp9FGgDPOi/wCei/nR50X/AD0X86fRRoBH58X/AD0X86PPi/56L+dSUUaAM86L/nov50edF/z0X86fRRoIZ50X/PRfzo86L/nov50+ijQBnnRf89F/OmmQyDbEDz/ERwP8alooAaiBECjoKdRRSGFJRRQAUdqKKAFFJRRQAUUUUAFFFFABRRRQAtJRRQAUUUUAFFFFABRRRQAUtFFACUUUUAFFFFABS9qKKACiiigBBS0UUAJS0UUAFJRRQAUtFFAAaSiigAooooAKKKKACloooASiiigAo7UUUAFFFFAC0lFFABS0UUAJRRRQAoooooASiiigAooooAKXvRRQAlLRRQAlFFFABRRRQAUUUUAFLRRQAlFFFAC0lFFABRRRQAUd6KKAFpKKKACiiigBaKKKAEooooAKKKKACiiigAooooAWkoooAKKKKACiiigAooooAKKKKACiiigAooooAU0lFFAC9qKKKAA0lFFABRRRQAtHaiigBKXtRRQAlFFFABRRRQAUUUUAFFFFAH//2QplbmRzdHJlYW0KZW5kb2JqCjIgMCBvYmo8PAovUmVzb3VyY2VzIDw8Ci9Qcm9jU2V0IFsgL1BERiAvSW1hZ2VDIF0KL1hPYmplY3QgPDwKL2ltYWdlIDEgMCBSCj4+Cj4+Ci9NZWRpYUJveCBbIDAgMCAyNTMuMiAzNTcuODQgXQovQ29udGVudHMgMyAwIFIKL1R5cGUgL1BhZ2UKL1BhcmVudCA1IDAgUgo+PmVuZG9iagozIDAgb2JqPDwKL0xlbmd0aCA0Nwo+PnN0cmVhbQpxIDI1My4yMDAwMDAgMCAwIDM1Ny44NDAwMDAgMCAwIGNtIC9pbWFnZSBEbyBRCgplbmRzdHJlYW0KZW5kb2JqCjYgMCBvYmo8PAovVGl0bGUgKP7/AGcAdQBpAGEAXwByAGEAcABpAGQAYQBfAGkAZABlAG4AdABpAGYAaQBjAGEAYwBpAG8AbgBfAHIAaQBlAHMAZwBvAHMpCi9DcmVhdGlvbkRhdGUgKEQ6MjAyNjA3MjIwMTMwMTdaKQovTW9kRGF0ZSAoRDoyMDI2MDcyMjAxMzAxN1opCj4+ZW5kb2JqCnhyZWYKMCA3CjAwMDAwMDAwMDAgNjU1MzYgZiAKMDAwMDAwMDE0NCAwMDAwMCBuIAowMDAwMjQ1MzM1IDAwMDAwIG4gCjAwMDAyNDU0OTggMDAwMDAgbiAKMDAwMDAwMDA0MCAwMDAwMCBuIAowMDAwMDAwMDg3IDAwMDAwIG4gCjAwMDAyNDU1OTMgMDAwMDAgbiAKdHJhaWxlcgo8PAovUm9vdCA0IDAgUgovU2l6ZSA3Ci9JbmZvIDYgMCBSCj4+CnN0YXJ0eHJlZgoyNDU3NTUKJSVFT0Y="""

def get_guia_uso_pdf_bytes() -> bytes:
    """Carga el PDF de ayuda desde assets o desde el respaldo embebido."""
    try:
        if Path(GUIA_USO_PATH).exists():
            return Path(GUIA_USO_PATH).read_bytes()
    except Exception:
        pass
    return base64.b64decode(GUIA_USO_PDF_B64_EMBEDDED)


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

    try:
        guia_pdf = get_guia_uso_pdf_bytes()
        st.download_button(
            label="📘 Modo de Uso - Ayuda",
            data=guia_pdf,
            file_name="guia_rapida_identificacion_riesgos.pdf",
            mime="application/pdf",
            use_container_width=False,
            key="download_guia_uso_ayuda"
        )
    except Exception:
        st.warning("No se encontró el PDF de la guía rápida de uso.")

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
                        '[data-testid="stAppViewBlockContainer"]',
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

                    // Fallback: mover arriba cualquier contenedor realmente desplazable.
                    Array.from(doc.querySelectorAll('*')).forEach((el) => {
                        try {
                            const style = win.getComputedStyle(el);
                            const scrollable = el.scrollHeight > el.clientHeight + 8;
                            const canScroll = ['auto', 'scroll', 'overlay'].includes(style.overflowY);
                            if (scrollable && canScroll) {
                                el.scrollTop = 0;
                                el.scrollLeft = 0;
                                if (typeof el.scrollTo === 'function') {
                                    el.scrollTo({ top: 0, left: 0, behavior: 'instant' });
                                }
                            }
                        } catch (e) {}
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
            [50, 150, 300, 600, 1000, 1500, 2500, 4000, 6000, 9000, 12000].forEach((t) => {
                window.setTimeout(forceTop, t);
            });
        })();
        </script>
        """,
        height=0,
        width=0,
    )

    st.session_state["_scroll_to_top"] = False

# El scroll se ejecuta al final del render para evitar que Streamlit restaure la vista a media página.

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

        @st.dialog("")
        def sicom_dialog():
            st.markdown(
                """
                <div class="modal-custom-title">Identificación de la EDS</div>
                <div class="modal-custom-text">
                    Ingrese el <strong>código SICOM</strong> de la estación de servicio para consultar
                    su mercado relevante y continuar con la evaluación del contrato.
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.form("form_sicom_dialog"):
                st.markdown('<div class="modal-custom-text" style="font-weight:700; margin-top:10px; margin-bottom:4px;">Código SICOM</div>', unsafe_allow_html=True)
                sicom_input = st.text_input(
                    "Código SICOM",
                    placeholder="6 dígitos",
                    label_visibility="collapsed"
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
                @st.dialog("")
                def lectura_rapida_dialog():
                    if res["bucket"] == "Bajo":
                        texto_operativo = (
                            "El contrato presenta una baja concentración de factores contractuales sensibles, "
                            "según la parametrización de la herramienta. Se recomienda conservar el reporte como soporte "
                            "y realizar seguimiento si se modifican las condiciones contractuales."
                        )
                    elif res["bucket"] == "Medio":
                        texto_operativo = (
                            "El contrato presenta elementos que justifican una revisión preventiva. "
                            "Se recomienda analizar con mayor detalle las condiciones contractuales antes de renovar, "
                            "modificar o suscribir nuevos compromisos."
                        )
                    else:
                        texto_operativo = (
                            "El contrato presenta una combinación de condiciones que amerita una revisión técnica detallada. "
                            "Se recomienda evaluar el alcance de las cláusulas, su justificación económica y sus posibles efectos "
                            "sobre la autonomía competitiva del minorista."
                        )

                    st.markdown(
                        f"""
                        <div class="modal-custom-title">Lectura rápida de resultados</div>
                        <div class="modal-custom-text">
                            Este resultado sintetiza los <strong>principales elementos contractuales</strong> que,
                            de acuerdo con la parametrización actual del modelo, <strong>incrementan el riesgo potencial
                            de afectación a la competencia</strong>.
                            <br><br>
                            <strong>Lectura operativa del resultado:</strong>
                            <br><br>
                            {texto_operativo}
                            <br><br>
                            <strong>Interpretación operativa:</strong> Un mayor número de factores activados o una mayor
                            contribución acumulada sugiere la conveniencia de realizar una <strong>revisión técnica más detallada
                            del contrato</strong>, considerando su contexto económico y regulatorio.
                        </div>
                        <div class="modal-note" style="border-radius:14px; padding:22px 24px; margin-top:24px; line-height:1.6; font-size:16px;">
                            <strong>Nota:</strong> esta herramienta tiene un carácter preventivo y orientador.
                            El semáforo no constituye una determinación de infracción ni sustituye el análisis jurídico
                            o económico de fondo.
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

# Ejecutar el scroll al final del render: más efectivo que hacerlo antes de construir la página.
scroll_to_top_if_needed()
