import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD (CONEXIÓN A NEON)
# ==============================================================================
DATABASE_URL = os.getenv("DATABASE_URL")

# --- ESTILOS PREMIUM INDUSTRIAL (CSS) ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    /* 1. Fondo y Contenedor Principal */
    .stApp { background-color: #f8fafc; } /* Slate 50: Limpio y profesional */
    
    /* 2. Tarjetas KPI (Soft UI / Glassmorphism) */
    .kpi-card {
        background-color: #ffffff;
        padding: 24px 16px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.07), 0 2px 6px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f5f9;
        margin-bottom: 20px;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    /* Colores de acento sutiles en la parte superior */
    .border-olive { border-top: 5px solid #65a30d; }
    .border-amber { border-top: 5px solid #d97706; }
    .border-blue { border-top: 5px solid #3b82f6; }
    
    /* Elementos internos de la tarjeta */
    .kpi-icon { 
        font-size: 28px; 
        color: #64748b; 
        margin-bottom: 12px;
        background: #f8fafc;
        width: 50px;
        height: 50px;
        line-height: 50px;
        border-radius: 12px;
        display: inline-block;
    }
    .kpi-title { 
        color: #64748b; 
        font-size: 0.8rem; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        margin-bottom: 8px; 
    }
    .kpi-value { 
        color: #0f172a; /* Azul noche: autoridad */
        font-size: 2.4rem; 
        font-weight: 800; 
        margin-bottom: 2px;
    }
    .kpi-unit { font-size: 0.9rem; color: #94a3b8; font-weight: 500; }
    
    /* Deltas (Rendimiento) */
    .kpi-delta { 
        font-size: 0.9rem; 
        font-weight: 600; 
        margin-top: 15px; 
        padding-top: 12px; 
        border-top: 1px solid #f1f5f9; 
    }
    .delta-positive { color: #16a34a; background: #f0fdf4; border-radius: 6px; padding: 4px 8px; }
    .delta-negative { color: #dc2626; background: #fef2f2; border-radius: 6px; padding: 4px 8px; }
    .delta-neutral { color: #64748b; }

    /* Estilo de tablas */
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
def format_kpi_number(num):
    try:
        val = float(num)
        if val >= 1_000_000: return f"{val/1_000_000:.2f}M"
        elif val >= 1_000: return f"{val/1_000:.1f}k"
        else: return f"{val:,.0f}"
    except: return "0"

def get_delta_html(real, target):
    if not target or target == 0 or pd.isna(target):
        return "<div class='kpi-delta delta-neutral'>Sin objetivo</div>"
    diff = real - target
    pct = (diff / target) * 100
    if diff > 0: return f"<div class='kpi-delta'><span class='delta-positive'>+{pct:.1f}% vs óptimo</span></div>"
    elif diff < 0: return f"<div class='kpi-delta'><span class='delta-negative'>{pct:.1f}% vs óptimo</span></div>"
    else: return "<div class='kpi-delta delta-neutral'>En objetivo</div>"

def get_kpi_card_html(title, icon_class, val, unit, delta_html, border_class=""):
    return f"""
    <div class="kpi-card {border_class}">
        <div class="kpi-icon"><i class="{icon_class}"></i></div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{format_kpi_number(val)}<span class="kpi-unit"> {unit}</span></div>
        {delta_html}
    </div>
    """

# ==============================================================================
# CONEXIÓN Y CARGA (SIMPLIFICADA PARA EL EJEMPLO VISUAL)
# ==============================================================================
@st.cache_data(ttl=60)
def load_all_data(fecha_reporte):
    try:
        engine = create_engine(DATABASE_URL)
        fecha_str = fecha_reporte.strftime('%Y-%m-%d')
        with engine.connect() as conn:
            df_aport = pd.read_sql(f"SELECT * FROM aportaciones WHERE fecha = '{fecha_str}'", conn)
            df_elec = pd.read_sql(f"SELECT * FROM electricidad WHERE fecha = '{fecha_str}'", conn)
            df_cent = pd.read_sql(f"SELECT * FROM centrifugacion WHERE fecha = '{fecha_str}'", conn)
            df_ext = pd.read_sql(f"SELECT * FROM extraccion WHERE fecha = '{fecha_str}'", conn)
            # Simplificamos nombres para el dashboard
            if not df_aport.empty: df_aport.rename(columns={'hoy_kg':'Hoy', 'planta':'Planta'}, inplace=True)
            if not df_elec.empty: df_elec.rename(columns={'generada_kwh':'Generada', 'planta':'Planta'}, inplace=True)
            if not df_cent.empty: df_cent.rename(columns={'aceite_prod':'Aceite', 'centro':'Centro'}, inplace=True)
            if not df_ext.empty: df_ext.rename(columns={'aceite_prod':'Aceite', 'extractora':'Extractora'}, inplace=True)
        return df_aport, df_elec, df_cent, df_ext
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- INTERFAZ ---
st.title("🏭 Centro de Mando El Tejar")
st.markdown("Cierre de operaciones y rendimiento diario")

col_d, col_f = st.columns([1, 2])
with col_d:
    fecha = st.date_input("Fecha", date.today() - timedelta(days=1))
with col_f:
    planta = st.selectbox("📍 Filtrar por Centro", ["Todas", "Baena", "Palenciana", "Marchena", "Cabra"])

df_aport, df_elec, df_cent, df_ext = load_all_data(fecha)

# --- DASHBOARD VISUAL ---
if df_aport.empty and df_elec.empty:
    st.info("Esperando datos para la fecha seleccionada...")
else:
    # 1. KPIs PRINCIPALES (CON ICONOGRAFÍA REFINADA)
    st.write("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    # Cálculos rápidos
    total_orujo = df_aport['Hoy'].sum() if not df_aport.empty else 0
    total_elec = df_elec['Generada'].sum() if not df_elec.empty else 0
    total_aceite = (df_cent['Aceite'].sum() if not df_cent.empty else 0) + (df_ext['Aceite'].sum() if not df_ext.empty else 0)
    
    with c1:
        st.markdown(get_kpi_card_html("Orujo Recibido", "fa-solid fa-truck-ramp-box", total_orujo, "kg", "", "border-olive"), unsafe_allow_html=True)
    with c2:
        st.markdown(get_kpi_card_html("Producción Aceite", "fa-solid fa-droplet", total_aceite, "kg", get_delta_html(total_aceite, 45000), "border-amber"), unsafe_allow_html=True)
    with c3:
        st.markdown(get_kpi_card_html("Energía Generada", "fa-solid fa-bolt-lightning", total_elec, "kWh", get_delta_html(total_elec, 800000), "border-blue"), unsafe_allow_html=True)
    with c4:
        # Ejemplo de Semáforo de Estado
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 5px solid #16a34a;">
            <div class="kpi-icon" style="color: #16a34a;"><i class="fa-solid fa-circle-check"></i></div>
            <div class="kpi-title">Estado Global</div>
            <div class="kpi-value" style="font-size: 1.8rem; color: #16a34a;">OPERATIVO</div>
            <div class="kpi-delta delta-neutral">Sin alertas críticas hoy</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. GRÁFICOS
    st.write("<br>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Generación Eléctrica por Planta")
        if not df_elec.empty:
            fig = px.bar(df_elec, x="Planta", y="Generada", color_discrete_sequence=['#3b82f6'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.subheader("Aportaciones por Centro")
        if not df_aport.empty:
            fig2 = px.pie(df_aport, values='Hoy', names='Planta', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig2.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)

    # 3. TABLAS DETALLADAS
    st.subheader("Detalle de Centrifugación")
    if not df_cent.empty:
        st.dataframe(df_cent, hide_index=True, use_container_width=True)
