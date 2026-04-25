import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
from datetime import date, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

def cargar_datos_locales(fecha_sel):
    """Busca el CSV generado por el robot en la carpeta de archivados"""
    fecha_str = fecha_sel.strftime("%d%m%y")
    patron = f"**/parte {fecha_str}.csv"
    archivos = glob.glob(patron, recursive=True)
    
    if not archivos:
        return None
    
    try:
        df = pd.read_csv(archivos[0], sep=';', decimal=',')
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

# --- INTERFAZ ---
st.title("🏭 Panel de Control - El Tejar")

with st.sidebar:
    st.header("Filtros")
    fecha_consulta = st.date_input("Fecha:", date.today() - timedelta(days=1))

df = cargar_datos_locales(fecha_consulta)

if df is not None:
    # Separación de datos por actividad
    df_aport = df[df['actividad'] == 1].copy()
    df_elec = df[df['actividad'] == 8].copy()
    df_aceite = df[df['actividad'].isin([3, 7])].copy()

    # --- MÉTRICAS PRINCIPALES ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        total_orujo = df_aport['a1'].sum() if not df_aport.empty else 0
        st.metric("Orujo Recibido (kg)", f"{total_orujo:,.0f}")

    with c2:
        total_aceite = df_aceite['a1'].sum() if not df_aceite.empty else 0
        st.metric("Aceite Producido (kg)", f"{total_aceite:,.0f}")

    with c3:
        total_kwh = df_elec['a1'].sum() if not df_elec.empty else 0
        st.metric("Energía Generada (kWh)", f"{total_kwh:,.0f}")

    # --- GRÁFICOS ---
    st.write("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Generación Eléctrica por Planta")
        if not df_elec.empty:
            df_elec['Planta'] = df_elec['nombre_c'].str.replace('12,6 MW', '').str.replace('25 MW', '').strip()
            fig = px.bar(df_elec, x='Planta', y='a1', color='Planta', labels={'a1': 'kWh Hoy'})
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Distribución de Aportaciones")
        if not df_aport.empty:
            fig_pie = px.pie(df_aport, values='a1', names='nombre_c', hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABLA COMPLETA ---
    with st.expander("Ver tabla completa de datos"):
        st.dataframe(df)
else:
    st.warning(f"No hay datos para el día {fecha_consulta.strftime('%d/%m/%Y')}")
