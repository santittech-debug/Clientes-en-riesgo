import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from utils.filtros import cargar_datos, SERVICIOS, ESTADOS
import matplotlib.ticker as mticker

# ─── CARGA DE DATOS ───────────────────────────────────────────

from utils.filtros import cargar_datos 

try:
    df, ops = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo en: data/datos_finales.parquet")
    st.stop()
 
# ─── IMAGEN DE PORTADA ────────────────────────────────────────
if os.path.exists("assets/portada.jpg"):
    st.image("assets/portada.jpg", use_column_width=True)
 
# ─── TÍTULO Y DESCRIPCIÓN ─────────────────────────────────────
st.markdown("""
<h1 style='color:#1D9E75; margin-bottom:0'>Radar Comercial</h1>
<h4 style='color:#6B7280; margin-top:4px'>Detección anticipada de clientes en riesgo — Importaciones Medellín</h4>
""", unsafe_allow_html=True)
 
st.markdown("""
Este dashboard analiza el comportamiento histórico de los clientes de importación 
de la sede **Medellín (2022–2026)**, con el objetivo de detectar de forma temprana 
señales de fuga, evaluar el desempeño comercial y priorizar acciones de retención.
 
Navega por las páginas del menú lateral para explorar cada análisis.
""")
 
st.divider()
 
# ─── SECCIÓN 1: KPIs GLOBALES ─────────────────────────────────
st.markdown("### Panorama general")
 
# DF completo (todas las sedes, todos los servicios)
total_ops_historicas = df['FileID'].nunique()
total_clientes_historicos = df['Cliente'].nunique()
años_cubiertos = sorted(df['Año'].dropna().unique().astype(int))
rango_años = f"{min(años_cubiertos)} – {max(años_cubiertos)}"
 
# DF filtrado MDE importaciones
df_mde = df[
    df['Servicio'].isin(SERVICIOS) &
    df['StatusNegocio'].isin(ESTADOS) &
    df['FileID'].str.contains('MDE', na=False)
].drop_duplicates('FileID').copy()
 
ops_mde = len(df_mde)
clientes_mde = df_mde['Cliente'].nunique()
comerciales_mde = df_mde['Comercial Reponsable'].nunique()
 
# Año actual vs año anterior
año_actual = max(años_cubiertos)
año_ant = año_actual - 1
ops_actual = df_mde[df_mde['Año'] == año_actual]['FileID'].count()
ops_ant = df_mde[df_mde['Año'] == año_ant]['FileID'].count()
 
if ops_ant > 0:
    delta_pct = ((ops_actual - ops_ant) / ops_ant) * 100
    delta_label = f"{delta_pct:+.1f}% vs {año_ant}"
else:
    delta_label = f"Sin dato {año_ant}"
 
# Fila 1 — globales
c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.metric(
            label="Operaciones históricas (todas las sedes)",
            value=f"{total_ops_historicas:,}",
            help="FileIDs únicos en todo el DF, sin filtro de ciudad ni servicio"
        )
with c2:
    with st.container(border=True):
        st.metric(
            label="Clientes únicos históricos",
            value=f"{total_clientes_historicos:,}",
            help="Clientes con al menos una operación registrada"
        )
with c3:
    with st.container(border=True):
        st.metric(
            label="Período cubierto",
            value=rango_años,
            help="Rango de años con datos disponibles"
        )
 
st.markdown("<br>", unsafe_allow_html=True)
 
# Fila 2 — filtrado MDE
st.markdown("##### Solo Medellín · Importaciones · Compras efectivas")
c4, c5, c6, c7 = st.columns(4)
with c4:
    with st.container(border=True):
        st.metric(
            label="Operaciones MDE",
            value=f"{ops_mde:,}",
            delta=delta_label,
            help=f"FileIDs únicos con filtro: AIO/FCLI/LCLI/AIM + estados efectivos + MDE"
        )
with c5:
    with st.container(border=True):
        st.metric(
            label="Clientes MDE",
            value=f"{clientes_mde:,}"
        )
with c6:
    with st.container(border=True):
        st.metric(
            label="Comerciales activos MDE",
            value=f"{comerciales_mde:,}"
        )
with c7:
    with st.container(border=True):
        st.metric(
            label=f"Operaciones {año_actual}",
            value=f"{ops_actual:,}",
            delta=delta_label
        )
 
st.divider()
 
# ─── SECCIÓN 2: GRÁFICO OPERACIONES POR AÑO ──────────────────
st.markdown("### Tendencia de operaciones por año — Medellín")
st.caption("Compras efectivas · Importaciones AIO / FCLI / LCLI / AIM")
 
ops_año = (
    df_mde.groupby('Año')['FileID']
    .count()
    .reset_index()
    .rename(columns={'FileID': 'Operaciones'})
    .sort_values('Año')
)
ops_año['Año'] = ops_año['Año'].astype(int)
 
# Variación % año vs año anterior
ops_año['Variacion'] = ops_año['Operaciones'].pct_change() * 100
 
meses_actuales = df_mde[df_mde['Año'] == año_actual]['Mes'].nunique()
nota_año = f"* {año_actual} incluye solo {meses_actuales} mes(es) con datos" if meses_actuales < 12 else ""
 
fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor('#0f172a')
ax.set_facecolor('#0f172a')
 
colores = ['#1D9E75' if a == año_actual else '#9FE1CB' for a in ops_año['Año']]
bars = ax.bar(ops_año['Año'].astype(str), ops_año['Operaciones'], color=colores, width=0.55)
 
for bar, (_, row) in zip(bars, ops_año.iterrows()):
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2, h + 15,
        str(int(h)),
        ha='center', va='bottom', fontsize=11, fontweight='bold', color='white'
    )
    if pd.notna(row['Variacion']):
        signo = '+' if row['Variacion'] >= 0 else ''
        color_txt = '#9FE1CB' if row['Variacion'] >= 0 else '#F87171'
        ax.text(
            bar.get_x() + bar.get_width() / 2, h * 0.5,
            f"{signo}{row['Variacion']:.1f}%",
            ha='center', va='center', fontsize=9, color=color_txt, fontweight='bold'
        )
 
ax.set_ylabel('Operaciones', color='#94a3b8', fontsize=11)
ax.set_xlabel('Año', color='#94a3b8', fontsize=11)
ax.tick_params(colors='#94a3b8')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#334155')
ax.spines['bottom'].set_color('#334155')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.tight_layout()
 
st.pyplot(fig)
if nota_año:
    st.caption(nota_año)
 
st.divider()
 
# ─── SECCIÓN 3: CONTEXTO DEL PROYECTO ────────────────────────
st.markdown("### ¿Qué responde este proyecto?")
 
col_q1, col_q2, col_q3 = st.columns(3)
with col_q1:
    with st.container(border=True):
        st.markdown("**¿Qué está pasando?**")
        st.markdown(
            "Indicadores clave: ventas totales, número de operaciones "
            "y comportamiento mensual — para tener visión del estado actual."
        )
with col_q2:
    with st.container(border=True):
        st.markdown("**¿Dónde están los problemas?**")
        st.markdown(
            "Análisis por cliente y comercial: quiénes generan más valor, "
            "quiénes muestran caída sostenida y qué tipos de carga dominan."
        )
with col_q3:
    with st.container(border=True):
        st.markdown("**¿A quién debo atender ya?**")
        st.markdown(
            "Lista accionable de clientes en riesgo con nivel de alerta, "
            "días sin comprar y comercial responsable — para actuar hoy."
        )

# 1. Imagen de portada
st.image("assets/portada.png", use_container_width=True)

# 2. Título y descripción del proyecto
st.title("Radar Comercial")
st.markdown("""
**¿De qué trata este proyecto?**  
Este dashboard detecta de forma anticipada clientes con señales de riesgo de fuga,
analiza el comportamiento de los comerciales y permite tomar decisiones basadas en
datos para el área comercial de importaciones — sede Medellín.
""")
st.divider()


# Cargar datos
ruta = 'data/datos_finales.parquet'
df = pd.read_parquet(ruta)


# Tipos válidos
tipos_validos = [
    'Importación Aérea (AIO)',
    'Full Container Load Impo (FCLI)',
    'Less Container Load Impo (LCLI)',
    'Importación Aérea Miami (AIM)'
]

# ── PASO 1: filtrar y crear columnas ANTES de usarlas ──
df_filtrado = df[df['Servicio'].isin(tipos_validos)].copy()
df_filtrado['Fecha Inicio'] = pd.to_datetime(df_filtrado['Fecha Inicio'], errors='coerce')
df_filtrado['Año'] = df_filtrado['Fecha Inicio'].dt.year
df_filtrado['Mes'] = df_filtrado['Fecha Inicio'].dt.month

# ── PASO 2: selectores ──
meses = {
    1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril',
    5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto',
    9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'
}

col_año, col_mes = st.columns(2)

with col_año:
    años_disponibles = sorted(df_filtrado['Año'].dropna().unique().astype(int), reverse=True)
    año_sel = st.selectbox('Seleccionar año', años_disponibles)

meses_disponibles = sorted(
    df_filtrado[df_filtrado['Año'] == año_sel]['Mes'].dropna().unique().astype(int)
)

with col_mes:
    mes_sel = st.selectbox(
        'Seleccionar mes',
        options=meses_disponibles,
        format_func=lambda x: meses[x]
    )

# ── PASO 3: calcular totales y delta ──
total_sel = df_filtrado[
    (df_filtrado['Año'] == año_sel) & (df_filtrado['Mes'] == mes_sel)
]['FileID'].count()

total_prev = df_filtrado[
    (df_filtrado['Año'] == año_sel - 1) & (df_filtrado['Mes'] == mes_sel)
]['FileID'].count()

if total_prev > 0:
    delta_pct = ((total_sel - total_prev) / total_prev) * 100
    delta_str = f"{delta_pct:+.1f}% vs {meses[mes_sel]} {año_sel - 1}"
else:
    delta_str = f"Sin dato para {meses[mes_sel]} {año_sel - 1}"

# ── PASO 4: mostrar métrica ──
with st.container(border=True):
    st.metric(
        label=f'Files — {meses[mes_sel]} {año_sel}',
        value=total_sel,
        delta=delta_str
    )

    # ── GRÁFICO: files por mes del año seleccionado ──
st.subheader(f'Files por mes — {año_sel}')

df_año = (
    df_filtrado[df_filtrado['Año'] == año_sel]
    .groupby('Mes')['FileID']
    .count()
    .reset_index()
    .rename(columns={'FileID': 'Total'})
    .sort_values('Mes')
)

df_año['Total_prev'] = df_año['Mes'].map(
    df_filtrado[df_filtrado['Año'] == año_sel - 1]
    .groupby('Mes')['FileID'].count()
)
df_año['Variacion'] = ((df_año['Total'] - df_año['Total_prev']) / df_año['Total_prev'] * 100).round(1)
df_año['Nombre Mes'] = df_año['Mes'].map(meses)

colores = ['#1D9E75' if m == mes_sel else '#9FE1CB' for m in df_año['Mes']]

fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(df_año['Nombre Mes'], df_año['Total'], color=colores, width=0.6)

for bar, (_, row) in zip(bars, df_año.iterrows()):
    altura = bar.get_height()
    
    # Total encima de la barra
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        altura + 10,
        str(int(altura)),
        ha='center', va='bottom', fontsize=10, fontweight='bold',
        color='#2C2C2A'
    )
    
    # Variación % dentro de la barra (cerca del tope)
    if pd.notna(row['Variacion']):
        signo = '+' if row['Variacion'] >= 0 else ''
        color_txt = '#1D9E75' if row['Variacion'] >= 0 else '#E24B4A'
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            altura * 0.85,          # 85% de la altura = dentro de la barra
            f"{signo}{row['Variacion']}%",
            ha='center', va='center', fontsize=9, color='white',
            fontweight='bold'
        )

ax.set_ylabel('Cantidad de files', fontsize=11)
ax.tick_params(axis='x', rotation=45)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
st.pyplot(fig)




