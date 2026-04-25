import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
from datetime import date, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Centro de Mando - El Tejar", layout="wide", page_icon="🏭")

# --- ESTILOS VISUALES (LIMPIOS Y PROFESIONALES) ---
st.markdown("""
<style>
    /* Fondo suave */
    .stApp { background-color: #f8fafc; }
    
    /* Tarjetas de KPI */
    .kpi-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; margin-bottom: 10px; }
    .kpi-value { color: #0f172a; font-size: 2.2rem; font-weight: 800; }
    .kpi-unit { color: #94a3b8; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE CARGA DE DATOS (LOCAL) ---
def cargar_datos_locales(fecha_sel):
    """Busca el CSV generado por el robot en la carpeta de archivados"""
    fecha_str = fecha_sel.strftime("%d%m%y")
    # Buscamos tanto en Nuevos como en Archivados por si acaso
    patron = f"**/parte {fecha_str}.csv"
    archivos = glob.glob(patron, recursive=True)
    
    if not archivos:
        return None
    
    try:
        # Leemos el CSV (formato Subifor: separado por ;)
        df = pd.read_csv(archivos[0], sep=';', decimal=',')
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

# --- INTERFAZ PRINCIPAL ---
st.title("🏭 Centro de Mando El Tejar")
st.markdown("Monitorización de producción y eficiencia energética")

# Selector de fecha en la barra lateral
with st.sidebar:
    st.header("Configuración")
    fecha_consulta = st.date_input("Consultar Fecha:", date.today() - timedelta(days=1))
    st.info("El sistema busca automáticamente los archivos procesados por el Robot Vigilante.")

df = cargar_datos_locales(fecha_consulta)

if df is not None:
    # --- FILTRADO DE DATOS ---
    # Actividad 1 = Aportaciones
    df_aport = df[df['actividad'] == 1].copy()
    # Actividad 8 = Electricidad
    df_elec = df[df['actividad'] == 8].copy()
    # Actividad 3 y 7 = Producción Aceite (Centrif. y Extrac.)
    df_aceite = df[df['actividad'].isin([3, 7])].copy()

    # --- BLOQUE DE KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        total_orujo = df_aport['a1'].sum() if not df_aport.empty else 0
        st.markdown(f"""<div class="kpi-container">
            <div class="kpi-title">📦 Orujo Recibido</div>
            <div class="kpi-value">{total_orujo:,.0f}</div>
            <div class="kpi-unit">KILOS HOY</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        # Sumamos producción de aceite (columna a1 suele ser hoy)
        total_aceite = df_aceite['a1'].sum() if not df_aceite.empty else 0
        st.markdown(f"""<div class="kpi-container">
            <div class="kpi-title">💧 Aceite Producido</div>
            <div class="kpi-value">{total_aceite:,.0f}</div>
            <div class="kpi-unit">KILOS HOY</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        total_kwh = df_elec['a1'].sum() if not df_elec.empty else 0
        st.markdown(f"""<div class="kpi-container">
            <div class="kpi-title">⚡ Energía Generada</div>
            <div class="kpi-value">{total_kwh:,.0f}</div>
            <div class="kpi-unit">kWh HOY</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        # Eficiencia (Real vs Óptimo en Electricidad)
        optimo_kwh = df_elec['a10'].sum() if not df_elec.empty else 1
        eficiencia = (total_kwh / optimo_kwh) * 100 if optimo_kwh > 0 else 0
        color = "#16a34a" if eficiencia >= 95 else "#ca8a04"
        st.markdown(f"""<div class="kpi-container" style="border-top: 5px solid {color}">
            <div class="kpi-title">🎯 Eficiencia Eléc.</div>
            <div class="kpi-value" style="color: {color}">{eficiencia:.1f}%</div>
            <div class="kpi-unit">VS. ÓPTIMO TEÓRICO</div>
        </div>""", unsafe_allow_html=True)

    # --- GRÁFICOS ---
    st.write("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Generación por Planta (kWh)")
        if not df_elec.empty:
            # Limpiamos nombres para el gráfico
            df_elec['Planta'] = df_elec['nombre_c'].str.replace('12,6 MW', '').str.replace('25 MW', '').str.strip()
            fig_elec = px.bar(df_elec, x='Planta', y='a1', 
                             labels={'a1': 'kWh Hoy', 'Planta': 'Planta'},
                             color_discrete_sequence=['#3b82f6'])
            fig_elec.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_elec, use_container_width=True)

    with col_right:
        st.subheader("Aportación por Centro")
        if not df_aport.empty:
            fig_pie = px.pie(df_aport, values='a1', names='nombre_c', hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABLA DE DETALLE ---
    with st.expander("🔍 Ver desglose completo del parte"):
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.warning(f"No se han encontrado datos procesados para el día {fecha_consulta.strftime('%d/%m/%Y')}.")
    st.info("Asegúrate de que el Robot Vigilante ha procesado el PDF de este día.")
