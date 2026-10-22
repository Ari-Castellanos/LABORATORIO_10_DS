"""Cabecera, selector de año y dos indicadores del Observatorio de Turismo.

Coloca este archivo junto a DATOS_LIMPIOS.csv y ejecuta:
    streamlit run app.py

Dependencias: streamlit, pandas.
"""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import base64

import pandas as pd
import streamlit as st


# ----------------------- Configuración -----------------------
st.set_page_config(
    page_title="Observatorio de Turismo Sostenible | Guatemala",
    page_icon="🇬🇹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CARPETA = Path(__file__).resolve().parent
RUTA_CSV = CARPETA / "DATOS_LIMPIOS.csv"
MES_ACTUAL = datetime.now(ZoneInfo("America/Guatemala")).month
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ----------------------- Carga y cálculos -----------------------
@st.cache_data(show_spinner="Cargando datos...")
def cargar_totales(ruta: str, fecha_modificacion: float) -> pd.Series:
    """Agrega visitantes mensuales; incluye turistas y excursionistas.

    fecha_modificacion invalida el caché si cambia el CSV.
    """
    df = pd.read_csv(
        ruta,
        usecols=["Fecha", "Viajero", "Tipo de Viajero"],
        low_memory=False,
    )
    df = df.loc[
        df["Tipo de Viajero"].astype(str).str.strip().isin(
            ["Turista", "Excursionista"]
        )
    ].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Viajero"] = pd.to_numeric(df["Viajero"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Viajero"])
    df["Año"] = df["Fecha"].dt.year.astype(int)
    df["Mes"] = df["Fecha"].dt.month.astype(int)
    return df.groupby(["Año", "Mes"])["Viajero"].sum().sort_index()


def porcentaje_cambio(actual: float, anterior: float) -> float | None:
    """Porcentaje de variación; evita divisiones por cero o meses ausentes."""
    if anterior is None or actual is None or anterior == 0:
        return None
    return (actual / anterior - 1) * 100


def crecimiento_anual(totales: pd.Series, anio: int):
    """Compara meses equivalentes (YTD cuando el año está incompleto)."""
    meses_anio = sorted(m for y, m in totales.index if y == anio)
    if not meses_anio:
        return None, "Sin datos en el año seleccionado"

    # Si el último año es parcial, no se compara contra un año anterior completo.
    mes_final = max(meses_anio)
    meses = list(range(1, mes_final + 1))
    if not all((anio, m) in totales.index and (anio - 1, m) in totales.index for m in meses):
        return None, "No hay períodos comparables"

    actual = sum(float(totales.loc[(anio, m)]) for m in meses)
    anterior = sum(float(totales.loc[(anio - 1, m)]) for m in meses)
    comparacion = f"{anio} vs. {anio - 1}"
    if mes_final < 12:
        comparacion += f" (ene–{MESES[mes_final - 1][:3]})"
    return porcentaje_cambio(actual, anterior), comparacion


def crecimiento_mensual(totales: pd.Series, anio: int, mes: int):
    """Compara el mismo mes del año elegido con el año previo."""
    actual = totales.get((anio, mes))
    anterior = totales.get((anio - 1, mes))
    return porcentaje_cambio(actual, anterior)


def valor_porcentaje(valor: float | None) -> tuple[str, str]:
    if valor is None:
        return "N/D", "#64748B"
    return f"{valor:+.1f}%", ("#0C9268" if valor >= 0 else "#C24146")


if not RUTA_CSV.exists():
    st.error("No se encontró DATOS_LIMPIOS.csv. Colócalo en la misma carpeta que app.py.")
    st.stop()

try:
    totales = cargar_totales(str(RUTA_CSV), RUTA_CSV.stat().st_mtime)
except Exception as error:
    st.error(f"No se pudo cargar DATOS_LIMPIOS.csv: {error}")
    st.stop()

if totales.empty:
    st.error("No hay registros válidos de turistas o excursionistas.")
    st.stop()

anios = sorted(totales.index.get_level_values("Año").unique().astype(int), reverse=True)
anio_predeterminado = 2024 if 2024 in anios else anios[0]


# ----------------------- Encabezado y filtro -----------------------
# Imagen opcional: coloca atitlan.jpg junto a app.py para utilizarla de fondo.
imagen = CARPETA / "atitlan.jpg"
if imagen.exists():
    imagen_b64 = base64.b64encode(imagen.read_bytes()).decode("ascii")
    fondo = (
        "linear-gradient(90deg, rgba(239,248,255,.95) 0%, "
        "rgba(239,248,255,.60) 55%, rgba(239,248,255,.12) 100%), "
        f"url('data:image/jpeg;base64,{imagen_b64}')"
    )
else:
    fondo = "linear-gradient(105deg, #EDF7FE 0%, #B6DBEE 65%, #72AFC7 100%)"

st.markdown(
    f"""
    <style>
      .block-container {{padding-top: .7rem; max-width: 1500px;}}
      .cabecera {{
        background-image: {fondo};
        background-position: center; background-size: cover;
        border-radius: 13px; padding: 18px 24px 20px;
        min-height: 120px; margin-bottom: 12px;
        display: flex; flex-direction: column; justify-content: center;
      }}
      .cabecera h1 {{margin: 0; color: #102C55; font-size: clamp(28px, 3.2vw, 44px); line-height: 1.1;}}
      .cabecera p {{margin: 6px 0 0; color: #24476F; font-size: 16px;}}
      div[data-testid="stSelectbox"] {{
        background: #FFFFFF; padding: 8px 13px 4px;
        border-radius: 12px; border: 1px solid #D9E4EE;
      }}
      .ficha {{
        background: #FFFFFF; border: 1px solid #DCE6EE; border-radius: 12px;
        min-height: 128px; padding: 17px 20px;
        display: flex; align-items: flex-start; gap: 20px;
        box-shadow: 0 1px 2px rgba(21,54,87,.03);
      }}
      .icono {{
        flex-shrink: 0; width: 60px; height: 60px;
        background: #E0F4EC; color: #128A65; border-radius: 13px;
        display: grid; place-items: center;
      }}
      .titulo {{color: #102C55; font-size: 15px; font-weight: 750; line-height: 1.25;}}
      .subtitulo {{color: #687A96; font-size: 13px; margin-top: 3px;}}
      .cifra {{font-size: 31px; font-weight: 750; line-height: 1.25; margin-top: 3px;}}
      .pie {{color: #8290A4; font-size: 13px;}}
      @media (max-width: 700px) {{.ficha {{margin-bottom: 12px;}}}}
    </style>
    """,
    unsafe_allow_html=True,
)

col_titulo, col_filtro = st.columns([4.2, 1.05], vertical_alignment="center", gap="small")
with col_titulo:
    st.markdown(
        """
        <div class="cabecera">
          <h1>Panorama general</h1>
          <p>Principales indicadores, tendencias y proyecciones del turismo en Guatemala</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_filtro:
    anio_elegido = st.selectbox(
        "Año de análisis",
        options=anios,
        index=anios.index(anio_predeterminado),
        key="anio_analisis",
    )


# ----------------------- Dos fichas -----------------------
valor_anual, periodo_anual = crecimiento_anual(totales, anio_elegido)
valor_mes = crecimiento_mensual(totales, anio_elegido, MES_ACTUAL)
texto_anual, color_anual = valor_porcentaje(valor_anual)
texto_mes, color_mes = valor_porcentaje(valor_mes)
mes_nombre = MESES[MES_ACTUAL - 1].capitalize()

icono_tendencia = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 17 6-6 4 4 8-9"/><path d="M15 6h6v6"/></svg>"""
icono_calendario = """<svg width="31" height="31" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>"""

col_anual, col_mensual = st.columns(2, gap="small")
with col_anual:
    st.markdown(
        f"""
        <div class="ficha">
          <div class="icono">{icono_tendencia}</div>
          <div>
            <div class="titulo">Crecimiento interanual de visitantes</div>
            <div class="subtitulo">{periodo_anual}</div>
            <div class="cifra" style="color:{color_anual}">{texto_anual}</div>
            <div class="pie">vs. año anterior</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_mensual:
    st.markdown(
        f"""
        <div class="ficha">
          <div class="icono">{icono_calendario}</div>
          <div>
            <div class="titulo">Crecimiento del mes actual</div>
            <div class="subtitulo">{mes_nombre} {anio_elegido} vs. {mes_nombre} {anio_elegido - 1}</div>
            <div class="cifra" style="color:{color_mes}">{texto_mes}</div>
            <div class="pie">vs. mismo mes del año anterior</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
