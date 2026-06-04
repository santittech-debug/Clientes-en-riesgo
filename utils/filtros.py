import pandas as pd
import streamlit as st

SERVICIOS = [
    "Importación Aérea (AIO)",
    "Full Container Load Impo (FCLI)",
    "Less Container Load Impo (LCLI)",
    "Importación Aérea Miami (AIM)",
]
ESTADOS = [
    "4. Carga en Destino", "7. Carga en Destino",
    "5. Carga liberada", "Terminado", "Facturacion",
]

@st.cache_data
def cargar_datos():
    df = pd.read_parquet("data/datos_finales.parquet")
    df_f = df[
        df["Servicio"].isin(SERVICIOS)
        & df["StatusNegocio"].isin(ESTADOS)
        & df["FileID"].str.contains("MDE", na=False)
    ].copy()
    df_f["Fecha Inicio"] = pd.to_datetime(df_f["Fecha Inicio"], dayfirst=True, errors="coerce")
    df_f["Año"] = df_f["Fecha Inicio"].dt.year
    df_f["Mes"] = df_f["Fecha Inicio"].dt.month
    ops = df_f.drop_duplicates(subset="FileID").copy()
    return df_f, ops