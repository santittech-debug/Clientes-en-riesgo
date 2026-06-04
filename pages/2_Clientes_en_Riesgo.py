import streamlit as st
import pandas as pd
import plotly.express as px
from utils.filtros import cargar_datos, SERVICIOS, ESTADOS

df, ops = cargar_datos()

umbral_inactividad = 180
hoy = pd.Timestamp.today()

client_stats = (
    ops.groupby("Cliente")
    .agg(
        ultima_compra=("Fecha Inicio", "max"),
        total_compras=("FileID", "count")
    )
    .reset_index()
)
client_stats["dias_inactivo"] = (hoy - client_stats["ultima_compra"]).dt.days

# ─── ESTILOS ──────────────────────────────────────────────────
st.markdown("""
<style>
    .section-title {
        font-size: 1rem; font-weight: 600; color: #cbd5e1;
        margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 6px;
    }
    .alert-banner {
        display: flex; align-items: center; gap: 10px;
        background: #2d1515; border-left: 4px solid #ef4444;
        border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 1.2rem;
    }
    .alert-banner span { font-size: 14px; color: #fca5a5; }
    .kpi-row { display: flex; gap: 12px; margin-bottom: 1.5rem; }
    .kpi-card {
        flex: 1; background: #1e293b; border-radius: 10px;
        padding: 16px; border-left: 4px solid #334155;
    }
    .kpi-card.verde { border-left-color: #10b981; }
    .kpi-card.amarillo { border-left-color: #f59e0b; }
    .kpi-card.rojo { border-left-color: #f97316; }
    .kpi-card.gris { border-left-color: #64748b; }
    .kpi-val { font-size: 28px; font-weight: 700; color: #f1f5f9; }
    .kpi-label { font-size: 12px; color: #94a3b8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ─── TÍTULO ───────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:1rem">
    <span style="font-size:32px">🚨</span>
    <div>
        <h2 style="margin:0; color:#f1f5f9">Clientes en Riesgo — Medellín</h2>
        <p style="margin:0; color:#64748b; font-size:13px">Importaciones · compras efectivas · 2022–2026</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── CÁLCULOS ─────────────────────────────────────────────────
ultimo_comercial = (
    ops.sort_values("Fecha Inicio")
    .groupby("Cliente")["Comercial Reponsable"].last()
    .reset_index()
    .rename(columns={"Comercial Reponsable": "Ultimo Comercial"})
)
servicios_cliente = (
    ops.groupby("Cliente")["Servicio"]
    .agg(lambda x: ", ".join(sorted(x.unique())))
    .reset_index()
    .rename(columns={"Servicio": "Servicios Usados"})
)

tabla_riesgo = client_stats.merge(ultimo_comercial, on="Cliente").merge(servicios_cliente, on="Cliente")

def nivel_riesgo(d):
    if d <= 90:
        return "Bajo"
    elif d <= umbral_inactividad:
        return "Medio"
    elif d <= umbral_inactividad * 1.5:
        return "Alto"
    else:
        return "Perdido"

tabla_riesgo["Riesgo"] = tabla_riesgo["dias_inactivo"].apply(nivel_riesgo)
tabla_riesgo["Ultima Compra"] = tabla_riesgo["ultima_compra"].dt.strftime("%d/%m/%Y")

solo_activos = tabla_riesgo[tabla_riesgo["dias_inactivo"] <= umbral_inactividad].sort_values(
    "dias_inactivo", ascending=False
)

n_activos  = len(tabla_riesgo[tabla_riesgo["Riesgo"] == "Bajo"])
n_medio    = len(tabla_riesgo[tabla_riesgo["Riesgo"] == "Medio"])
n_alto     = len(tabla_riesgo[tabla_riesgo["Riesgo"] == "Alto"])
n_perdidos = len(tabla_riesgo[tabla_riesgo["Riesgo"] == "Perdido"])

# ─── BANNER ───────────────────────────────────────────────────
if n_alto > 0:
    st.markdown(f"""
    <div class="alert-banner">
        🔔 <span><strong>{n_alto} clientes</strong> superaron el umbral de inactividad y requieren atención inmediata</span>
    </div>
    """, unsafe_allow_html=True)

# ─── KPIs ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card verde">
        <div class="kpi-val">👥 {n_activos}</div>
        <div class="kpi-label">Clientes activos (bajo riesgo)</div>
    </div>
    <div class="kpi-card amarillo">
        <div class="kpi-val">⚠️ {n_medio}</div>
        <div class="kpi-label">En alerta media</div>
    </div>
    <div class="kpi-card rojo">
        <div class="kpi-val">🔴 {n_alto}</div>
        <div class="kpi-label">En riesgo alto</div>
    </div>
    <div class="kpi-card gris">
        <div class="kpi-val">💀 {n_perdidos}</div>
        <div class="kpi-label">Clientes perdidos</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── TABLA PRINCIPAL ──────────────────────────────────────────
st.markdown('<div class="section-title">📋 Clientes activos ordenados por riesgo de fuga</div>', unsafe_allow_html=True)

st.dataframe(
    solo_activos[[
        "Riesgo", "Cliente", "total_compras", "dias_inactivo",
        "Ultima Compra", "Ultimo Comercial", "Servicios Usados"
    ]].rename(columns={
        "total_compras": "Num Compras",
        "dias_inactivo": "Dias sin comprar",
    }),
    use_container_width=True, height=380,
)

# ─── GRÁFICOS ─────────────────────────────────────────────────
col_r1, col_r2 = st.columns(2)

with col_r1:
    st.markdown('<div class="section-title">📊 Top 10 clientes por días sin comprar</div>', unsafe_allow_html=True)
    top10_barras = solo_activos.nlargest(10, "dias_inactivo")[
        ["Cliente", "dias_inactivo", "Riesgo"]
    ].sort_values("dias_inactivo", ascending=True)

    fig_bar = px.bar(
        top10_barras,
        x="dias_inactivo", y="Cliente", orientation="h",
        color="Riesgo",
        color_discrete_map={"Bajo": "#10b981", "Medio": "#f59e0b", "Alto": "#f97316", "Perdido": "#ef4444"},
        text="dias_inactivo",
        labels={"dias_inactivo": "Días sin comprar", "Cliente": ""},
    )
    fig_bar.update_traces(textposition="outside", textfont_size=10)
    fig_bar.add_vline(
        x=umbral_inactividad, line_dash="dash", line_color="#ef4444",
        annotation_text=f"Umbral {umbral_inactividad}d",
    )
    fig_bar.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="#e2e8f0", height=420,
        margin=dict(l=10, r=60, t=10, b=10),
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_r2:
    st.markdown('<div class="section-title">🍩 Distribución por nivel de riesgo</div>', unsafe_allow_html=True)
    riesgo_counts = tabla_riesgo["Riesgo"].value_counts().reset_index()
    riesgo_counts.columns = ["Riesgo", "Clientes"]
    fig_pie = px.pie(
        riesgo_counts, names="Riesgo", values="Clientes", color="Riesgo",
        color_discrete_map={"Bajo": "#10b981", "Medio": "#f59e0b", "Alto": "#f97316", "Perdido": "#ef4444"},
        hole=0.45,
    )
    fig_pie.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="#e2e8f0", height=420,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ─── CLIENTES CRÍTICOS ────────────────────────────────────────
st.markdown('<div class="section-title">🆘 Clientes críticos — acción inmediata requerida</div>', unsafe_allow_html=True)
st.caption("Solo clientes con riesgo Alto o Perdido, ordenados por días de inactividad.")

criticos = tabla_riesgo[tabla_riesgo["Riesgo"].isin(["Alto", "Perdido"])].sort_values(
    "dias_inactivo", ascending=False
)[["Riesgo", "Cliente", "total_compras", "dias_inactivo", "Ultima Compra", "Ultimo Comercial"]].rename(
    columns={"total_compras": "Num Compras", "dias_inactivo": "Dias sin comprar"}
)

st.dataframe(criticos, use_container_width=True, height=300)