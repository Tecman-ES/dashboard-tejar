import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Cargar la caja fuerte (.env)
load_dotenv()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

# ==============================================================================
# ⚠️ CONFIGURACIÓN DE SEGURIDAD (CONEXIÓN A NEON)
# ==============================================================================
# La clave ahora se lee de forma segura y oculta desde el archivo .env o Secrets
DATABASE_URL = os.getenv("DATABASE_URL")

# --- ESTILOS PERSONALIZADOS (CSS) - SLATE LIGHT THEME ---
st.markdown("""
<style>
    /* Fondo gris claro para no fatigar la vista */
    .stApp { background-color: #f1f5f9; }
    
    /* Tarjetas de Noticias */
    .news-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #eab308;
        margin-bottom: 15px;
        color: #0f172a;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #d97706; margin-bottom: 5px; }
    .news-source { font-size: 0.8rem; color: #64748b; margin-bottom: 10px; }
    .news-snippet { font-size: 0.9rem; line-height: 1.4; color: #334155; }
    .read-more { color: #0284c7; text-decoration: none; font-size: 0.85rem; font-weight: bold;}
    .stDataFrame [data-testid="stTable"] { font-variant-numeric: tabular-nums; }
    
    /* Tarjetas KPI Principales */
    .kpi-card {
        background-color: #ffffff;
        padding: 20px 10px 15px 10px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
        border-top: 4px solid #65a30d; 
        margin-bottom: 20px;
        color: #0f172a;
    }
    .kpi-card.blue { border-top-color: #3b82f6; }
    .kpi-card.yellow { border-top-color: #eab308; }
    .kpi-card.orange { border-top-color: #f97316; }
    
    .kpi-icon { font-size: 32px; margin-bottom: 10px; }
    .kpi-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
    .kpi-value { color: #0f172a; font-size: 2.2rem; font-weight: 800; line-height: 1.1; }
    .kpi-unit { font-size: 1rem; color: #94a3b8; font-weight: 500; }
    
    .kpi-delta { font-size: 0.95rem; font-weight: 600; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
    .delta-positive { color: #16a34a; } 
    .delta-negative { color: #dc2626; } 
    .delta-neutral { color: #64748b; font-weight: 400; } 
    
    /* Tarjetas Acumulado Mensual - Estilo Apilado */
    .monthly-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 10px;
        text-align: center;
        border-top: 4px solid #94a3b8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }
    .monthly-card.blue { border-top-color: #3b82f6; }
    .monthly-card.yellow { border-top-color: #eab308; }
    .monthly-card.orange { border-top-color: #f97316; }
    
    .m-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; display: block; }
    .m-icon { font-size: 20px; margin-bottom: 5px; display: block; }
    .m-value { color: #0f172a; font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
    .m-unit { font-size: 0.9rem; color: #94a3b8; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE DOBLE LOGIN ---
def check_password():
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False
        st.session_state["role"] = None
        
    if not st.session_state["login_ok"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            try:
                st.image("logo.png", width=250) 
            except Exception:
                st.markdown("<div style='text-align: center; font-size: 4rem;'>🏭</div>", unsafe_allow_html=True)
                
            st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            
            if st.button("Entrar", use_container_width=True):
                users_env = os.getenv("USUARIOS_AUTORIZADOS", "")
                usuarios_validos = {}
                if users_env:
                    for u in users_env.split(","):
                        partes = u.split(":")
                        if len(partes) == 3:
                            user, pwd, role = partes
                            usuarios_validos[user.strip()] = {"pwd": pwd.strip(), "role": role.strip()}
                
                if usuario in usuarios_validos and password == usuarios_validos[usuario]["pwd"]:
                    st.session_state["login_ok"] = True
                    st.session_state["role"] = usuarios_validos[usuario]["role"]
                    st.session_state["username"] = usuario
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no autorizado")
        return False
    return True

def get_centro_from_planta(planta_name):
    p_upper = str(planta_name).upper()
    if "BAENA" in p_upper: return "Baena"
    if "VETEJAR" in p_upper or "ALGODONALES" in p_upper or "AUTOGENERACI" in p_upper: return "Palenciana"
    if "TEJAR" in p_upper: return "El Tejar"
    return planta_name

def load_objectives():
    if os.path.exists("objetivos_tejar.csv"):
        df = pd.read_csv("objetivos_tejar.csv")
        if "Centro" not in df.columns:
            df["Centro"] = df["Planta"].apply(get_centro_from_planta)
        return df
    else:
        return pd.DataFrame({
            "Area": ["Centrifugacion", "Centrifugacion", "Centrifugacion", "Secado", "Secado", "Secado", "Secado", "Secado", "Extraccion", "Extraccion", "Electricidad", "Electricidad", "Electricidad", "Electricidad"],
            "Planta": ["Marchena", "Cabra", "Baena", "Palenciana", "Marchena", "Cabra", "Baena", "Espejo", "El Tejar", "Baena", "Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW", "Autogeneración 5.7 MW"],
            "Centro": ["Marchena", "Cabra", "Baena", "Palenciana", "Marchena", "Cabra", "Baena", "Espejo", "El Tejar", "Baena", "Palenciana", "Baena", "Palenciana", "Palenciana"],
            "Metrica": ["Aceite (kg)", "Aceite (kg)", "Aceite (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "Aceite (kg)", "Aceite (kg)", "Energia (kWh)", "Energia (kWh)", "Energia (kWh)", "Energia (kWh)"],
            "Objetivo_Diario": [5251, 442, 1906, 148900, 272720, 288560, 313160, 181020, 43400, 18900, 190270, 358330, 91400, 60000]
        })

def save_objectives(df):
    df.to_csv("objetivos_tejar.csv", index=False)

def apply_objectives(df_cent, df_secado, df_ext, df_elec, df_obj):
    def merge_obj(df, join_col, area_name, obj_col_name):
        if df.empty or join_col not in df.columns: return df
        sub_obj = df_obj[df_obj["Area"] == area_name][["Planta", "Objetivo_Diario"]]
        sub_obj = sub_obj.rename(columns={"Planta": join_col, "Objetivo_Diario": obj_col_name})
        if obj_col_name in df.columns: df = df.drop(columns=[obj_col_name])
        return pd.merge(df, sub_obj, on=join_col, how="left")

    df_cent = merge_obj(df_cent, "Centro", "Centrifugacion", "Optimo")
    df_secado = merge_obj(df_secado, "Centro", "Secado", "Obj_OGS")
    df_ext = merge_obj(df_ext, "Extractora", "Extraccion", "Obj_Aceite")
    df_elec = merge_obj(df_elec, "Planta", "Electricidad", "Optimo_kWh")
    return df_cent, df_secado, df_ext, df_elec

def format_kpi_number(num):
    try:
        val = float(num)
        if val >= 1_000_000: return f"{val/1_000_000:.2f}M"
        elif val >= 1_000: return f"{val/1_000:.1f}k"
        else: return f"{val:,.0f}"
    except: return "0"

def get_delta_html(real, target):
    if not target or target == 0 or pd.isna(target):
        return "<div class='kpi-delta delta-neutral'>Sin objetivo definido</div>"
    diff = real - target
    pct = (diff / target) * 100
    if diff > 0: return f"<div class='kpi-delta delta-positive'>▲ +{format_kpi_number(diff)} (+{pct:.1f}%)</div>"
    elif diff < 0: return f"<div class='kpi-delta delta-negative'>▼ {format_kpi_number(diff)} ({pct:.1f}%)</div>"
    else: return "<div class='kpi-delta delta-neutral'>▬ Objetivo exacto</div>"

def get_kpi_card_html(title, icon, val, unit, delta_html, css_class=""):
    return f"""
    <div class="kpi-card {css_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{format_kpi_number(val)}<span class="kpi-unit"> {unit}</span></div>
        {delta_html}
    </div>
    """

def get_monthly_card_html(title, icon, val, unit, css_class=""):
    return f"""
    <div class="monthly-card {css_class}">
        <span class="m-icon">{icon}</span>
        <span class="m-title">{title}</span>
        <div class="m-value">{format_kpi_number(val)}<span class="m-unit"> {unit}</span></div>
    </div>
    """

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

def display_styled_table(df, area="", download_name="datos.csv"):
    if df.empty: return
    df_clean = df.dropna(axis=1, how='all')
    if area == "Centrifugacion":
        def highlight(row):
            styles = [''] * len(row)
            if 'Acidez' in df_clean.columns:
                val = row['Acidez']
                if pd.notnull(val) and isinstance(val, (int, float)) and val > 3:
                    styles[df_clean.columns.get_loc('Acidez')] = 'background-color: rgba(239, 68, 68, 0.4); color: white;'
            return styles
        st.dataframe(df_clean.style.apply(highlight, axis=1).format(thousands=","), hide_index=True, use_container_width=True)
    else:
        st.dataframe(df_clean.style.format(thousands=","), hide_index=True, use_container_width=True)
    csv_data = convert_df(df_clean)
    st.download_button(label="📥 Descargar CSV", data=csv_data, file_name=download_name, mime='text/csv')

# ==============================================================================
# MOTOR DE CONEXIÓN: AHORA DESCARGA 7 DÍAS (VIAJE EN EL TIEMPO)
# ==============================================================================
@st.cache_data(ttl=60)
def get_data_from_db(fecha_reporte, dias_historial=0):
    try:
        engine = create_engine(DATABASE_URL)
        fecha_fin_str = fecha_reporte.strftime('%Y-%m-%d')
        fecha_inicio_str = (fecha_reporte - timedelta(days=dias_historial)).strftime('%Y-%m-%d')
        
        # Leer los últimos 7 días o solo 1 dependiendo del rol
        query_suffix = f"WHERE fecha >= '{fecha_inicio_str}' AND fecha <= '{fecha_fin_str}'"
        
        with engine.connect() as conn:
            df_aport = pd.read_sql(f"SELECT * FROM aportaciones {query_suffix}", conn)
            df_ex = pd.read_sql(f"SELECT * FROM existencias {query_suffix}", conn)
            df_cent = pd.read_sql(f"SELECT * FROM centrifugacion {query_suffix}", conn)
            df_sec = pd.read_sql(f"SELECT * FROM secado {query_suffix}", conn)
            df_ext = pd.read_sql(f"SELECT * FROM extraccion {query_suffix}", conn)
            df_elec = pd.read_sql(f"SELECT * FROM electricidad {query_suffix}", conn)
            df_cons_sec = pd.read_sql(f"SELECT * FROM consumo_secado {query_suffix}", conn)
            df_cons_ext = pd.read_sql(f"SELECT * FROM consumo_extraccion {query_suffix}", conn)
            df_cons_elec = pd.read_sql(f"SELECT * FROM consumo_electricidad {query_suffix}", conn)

        def standarize_dates(df):
            if not df.empty and 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m-%d')
            return df

        dfs = [df_aport, df_ex, df_cent, df_sec, df_ext, df_elec, df_cons_sec, df_cons_ext, df_cons_elec]
        for df in dfs: standarize_dates(df)

        if not df_aport.empty: df_aport.rename(columns={'planta':'Planta', 'centro':'Centro', 'hoy_kg':'Hoy (kg)', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_ex.empty: df_ex.rename(columns={'material':'Material', 'total_kilos':'Total Kilos'}, inplace=True)
        if not df_cent.empty: df_cent.rename(columns={'centro':'Centro', 'entrada_alperujo':'Entrada_Alperujo', 'aceite_prod':'Aceite_Prod', 'rdto_obtenido':'Rdto_Obtenido', 'acidez':'Acidez', 'acidez_mensual':'Acidez_Mensual', 'acidez_campana':'Acidez_Campana', 'media_mensual':'Media_Mensual', 'rdto_campana':'Rdto_Campana', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_sec.empty: df_sec.rename(columns={'centro':'Centro', 'entrada_alperujo':'Entrada_Alperujo', 'entrada_alperujo_mes':'Entrada_Alperujo_Mes', 'ogs_salida':'OGS_Salida', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_ext.empty: df_ext.rename(columns={'extractora':'Extractora', 'centro':'Centro', 'ogs_procesado':'OGS_Procesado', 'aceite_prod':'Aceite_Prod', 'acum_mensual':'Acum. Mensual', 'optimo_subifor':'Optimo_Subifor', 'salida_aceite':'Salida_Aceite'}, inplace=True)
        if not df_elec.empty: df_elec.rename(columns={'planta':'Planta', 'centro':'Centro', 'generada_kwh':'Generada_kWh', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_cons_sec.empty: df_cons_sec.rename(columns={'centro':'Centro', 'consumo_hueso':'Consumo_Hueso', 'consumo_orujillo':'Consumo_Orujillo', 'consumo_poda':'Consumo_Poda', 'consumo_hoja':'Consumo_Hoja'}, inplace=True)
        if not df_cons_ext.empty: df_cons_ext.rename(columns={'extractora':'Extractora', 'centro':'Centro', 'consumo_hueso':'Consumo_Hueso', 'consumo_orujillo':'Consumo_Orujillo', 'consumo_poda':'Consumo_Poda', 'consumo_hoja':'Consumo_Hoja'}, inplace=True)
        if not df_cons_elec.empty: df_cons_elec.rename(columns={'planta':'Planta', 'centro':'Centro', 'consumo_biomasa':'Consumo_Biomasa', 'consumo_biomasa_mes':'Consumo_Biomasa_Mes'}, inplace=True)

        has_data = not df_aport.empty
        return has_data, df_aport, df_ex, df_cent, df_sec, df_ext, df_elec, df_cons_sec, df_cons_ext, df_cons_elec
        
    except Exception as e:
        print(f"Error base de datos: {e}")
        return False, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def filter_dataframe(df, column_names, planta_seleccionada):
    if df.empty or planta_seleccionada == "Todas": return df
    if isinstance(column_names, str): column_names = [column_names]
    mask = pd.Series(False, index=df.index)
    for col in column_names:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(planta_seleccionada, case=False, na=False)
    return df[mask].reset_index(drop=True)

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    role = st.session_state["role"]
    username = st.session_state.get("username", "")
    
    # 🌟 EL TRUCO DE MAGIA: Si el usuario es "presidente", bloqueamos la V2.
    is_v2 = (username != "presidente")
    
    col_logo, col_titulo, col_logout = st.columns([1, 8, 1])
    with col_logo:
        try:
            st.image("logo.png", width=80)
        except Exception:
            st.markdown("<div style='font-size: 3rem; text-align: center;'>🏭</div>", unsafe_allow_html=True)
    with col_titulo:
        st.title("Panel Operativo - Oleícola El Tejar SCA")
    with col_logout:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🚪 Salir"):
            st.session_state["login_ok"] = False
            st.session_state["role"] = None
            st.rerun()
            
    st.markdown("---")
    
    col_date, col_filter = st.columns([1, 2])
    with col_date:
        if is_v2:
            fecha_activa = st.date_input("📅 Fecha de Análisis (Descarga últimos 7 días):", date.today())
        else:
            fecha_activa = st.date_input("📅 Selecciona la Fecha del Reporte:", date.today())
    
    with col_filter:
        plantas_disponibles = ["Todas", "Baena", "Cabra", "Marchena", "Palenciana", "Pedro Abad", "Espejo", "Bogarre", "Mancha Real", "Algodonales", "Vetejar", "El Tejar"]
        if is_v2:
            planta_activa = st.selectbox("📍 Filtro de Análisis (Barras vs Líneas de Tendencia):", plantas_disponibles)
        else:
            planta_activa = st.selectbox("📍 Filtro Global por Planta/Centro:", plantas_disponibles)

    # EXTRACCIÓN AUTOMÁTICA
    msg_carga = '☁️ Descargando histórico semanal desde Neon...' if is_v2 else '☁️ Conectando con la base de datos en producción...'
    with st.spinner(msg_carga):
        dias_a_descargar = 6 if is_v2 else 0
        has_data, df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, df_cons_secado, df_cons_ext, df_cons_elec = get_data_from_db(fecha_activa, dias_a_descargar)

    if not has_data:
        st.warning(f"⚠️ No hay datos en los últimos 7 días hasta el **{fecha_activa.strftime('%d/%m/%Y')}**.")
    else:
        st.success(f"☁️ Datos sincronizados. Analizando periodo hasta el **{fecha_activa.strftime('%d/%m/%Y')}**.")
        
        df_obj = load_objectives()
        df_cent, df_secado, df_ext, df_elec = apply_objectives(df_cent, df_secado, df_ext, df_elec, df_obj)
        
        df_aport_filt = filter_dataframe(df_aport, ["Planta", "Centro"], planta_activa)
        df_cent_filt = filter_dataframe(df_cent, ["Centro", "Planta"], planta_activa)
        df_secado_filt = filter_dataframe(df_secado, ["Centro", "Planta"], planta_activa)
        df_ext_filt = filter_dataframe(df_ext, ["Extractora", "Centro"], planta_activa)
        df_elec_filt = filter_dataframe(df_elec, ["Centro", "Planta"], planta_activa)
        df_obj_filtered = filter_dataframe(df_obj, ["Centro", "Planta"], planta_activa)

        # Extraer DataFrames ESPECÍFICOS para el día de hoy (Para los KPIs)
        fecha_hoy_str = fecha_activa.strftime('%Y-%m-%d')
        
        def get_today(df):
            if df.empty or 'fecha' not in df.columns: return df
            return df[df['fecha'] == fecha_hoy_str]

        df_aport_hoy = get_today(df_aport_filt)
        df_cent_hoy = get_today(df_cent_filt)
        df_secado_hoy = get_today(df_secado_filt)
        df_ext_hoy = get_today(df_ext_filt)
        df_elec_hoy = get_today(df_elec_filt)

        tabs = st.tabs(["👁️ Visión General", "📦 Aportaciones", "🌀 Centrifugación", "🔥 Secado", "⚗️ Extracción", "⚡ Electricidad", "🎯 Mis Objetivos"])

        # --- PESTAÑA 1: VISIÓN GENERAL (Basada en el Día Actual) ---
        with tabs[0]:
            if not df_aport_hoy.empty or not df_elec_hoy.empty:
                col_resumen, col_noticias = st.columns([2, 1])
                with col_resumen:
                    st.subheader(f"Resumen Ejecutivo Diario - {planta_activa.upper()}")
                    
                    total_orujo = df_aport_hoy['Hoy (kg)'].sum() if not df_aport_hoy.empty and 'Hoy (kg)' in df_aport_hoy.columns else 0
                    total_alperujo_sec = df_secado_hoy['Entrada_Alperujo'].sum() if not df_secado_hoy.empty and 'Entrada_Alperujo' in df_secado_hoy.columns else 0
                    total_ogs_sec = df_secado_hoy['OGS_Salida'].sum() if not df_secado_hoy.empty and 'OGS_Salida' in df_secado_hoy.columns else 0
                    total_elec = df_elec_hoy['Generada_kWh'].sum() if not df_elec_hoy.empty and 'Generada_kWh' in df_elec_hoy.columns else 0
                    total_aceite_cent = df_cent_hoy['Aceite_Prod'].sum() if not df_cent_hoy.empty and 'Aceite_Prod' in df_cent_hoy.columns else 0
                    total_aceite_ext = df_ext_hoy['Aceite_Prod'].sum() if not df_ext_hoy.empty and 'Aceite_Prod' in df_ext_hoy.columns else 0
                    
                    total_orujo_mes = df_aport_hoy['Acum. Mensual'].sum() if not df_aport_hoy.empty and 'Acum. Mensual' in df_aport_hoy.columns else 0
                    total_ogs_sec_mes = df_secado_hoy['Acum. Mensual'].sum() if not df_secado_hoy.empty and 'Acum. Mensual' in df_secado_hoy.columns else 0
                    total_elec_mes = df_elec_hoy['Acum. Mensual'].sum() if not df_elec_hoy.empty and 'Acum. Mensual' in df_elec_hoy.columns else 0
                    
                    target_elec = df_obj_filtered[df_obj_filtered['Area']=='Electricidad']['Objetivo_Diario'].sum()
                    target_cent = df_obj_filtered[df_obj_filtered['Area']=='Centrifugacion']['Objetivo_Diario'].sum()
                    target_sec = df_obj_filtered[df_obj_filtered['Area']=='Secado']['Objetivo_Diario'].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(get_kpi_card_html("Orujo Recibido", "📦", total_orujo, "kg", "", ""), unsafe_allow_html=True)
                    with c2: st.markdown(get_kpi_card_html("OGS Producido", "🏭", total_ogs_sec, "kg", get_delta_html(total_ogs_sec, target_sec), "orange"), unsafe_allow_html=True)
                    with c3: st.markdown(get_kpi_card_html("Electricidad", "⚡", total_elec, "kWh", get_delta_html(total_elec, target_elec), "blue"), unsafe_allow_html=True)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    
                    st.markdown("#### 📊 Producción Acumulada Mensual")
                    m1, m2, m3 = st.columns(3)
                    with m1: st.markdown(get_monthly_card_html("Orujo Recibido", "📦", total_orujo_mes, "kg", ""), unsafe_allow_html=True)
                    with m2: st.markdown(get_monthly_card_html("OGS Producido", "🏭", total_ogs_sec_mes, "kg", "orange"), unsafe_allow_html=True)
                    with m3: st.markdown(get_monthly_card_html("Electricidad", "⚡", total_elec_mes, "kWh", "blue"), unsafe_allow_html=True)

                with col_noticias:
                    st.subheader("📈 Mercado: Aceite de Orujo")
                    st.markdown("""
                    <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                        <div style="font-size: 0.85rem; color: #64748b; font-weight: bold; text-transform: uppercase;">Precio Medio (Crudo)</div>
                        <div style="font-size: 2rem; font-weight: 800; color: #0f172a;">1.24 <span style="font-size: 1rem; color: #94a3b8;">€/kg</span></div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- PESTAÑA 2: APORTACIONES ---
        with tabs[1]:
            st.subheader("Orujo Aportado (kg)")
            if not df_aport_filt.empty and 'Hoy (kg)' in df_aport_filt.columns:
                if not is_v2 or planta_activa == "Todas":
                    # Muestra barras del día actual
                    fig_aport = px.bar(df_aport_hoy, x="Planta", y="Hoy (kg)", color_discrete_sequence=['#8d6e63'])
                else:
                    # Muestra línea de tendencia de 7 días
                    df_trend = df_aport_filt.groupby('fecha', as_index=False)['Hoy (kg)'].sum().sort_values('fecha')
                    fig_aport = px.line(df_trend, x="fecha", y="Hoy (kg)", markers=True, line_shape="spline", color_discrete_sequence=['#8d6e63'], title=f"Tendencia Semanal - {planta_activa}")
                
                fig_aport.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_aport, use_container_width=True)
            else: st.info("Faltan datos de Aportaciones.")
            
            with st.expander("📊 Ver tabla de datos"):
                display_styled_table(df_aport_hoy, download_name="aportaciones_hoy.csv")

        # --- PESTAÑA 3: CENTRIFUGACIÓN ---
        with tabs[2]:
            st.subheader("🌀 Producción Aceite Centrifugación (kg)")
            if not df_cent_filt.empty and 'Aceite_Prod' in df_cent_filt.columns:
                if not is_v2 or planta_activa == "Todas":
                    fig_cent = px.bar(df_cent_hoy, x="Centro", y="Aceite_Prod", color_discrete_sequence=['#fbbf24'])
                else:
                    df_trend = df_cent_filt.groupby('fecha', as_index=False)['Aceite_Prod'].sum().sort_values('fecha')
                    fig_cent = px.line(df_trend, x="fecha", y="Aceite_Prod", markers=True, line_shape="spline", color_discrete_sequence=['#fbbf24'], title=f"Evolución Semanal de Aceite - {planta_activa}")
                
                fig_cent.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_cent, use_container_width=True)
            else: st.info("Faltan datos de Centrifugación.")

        # --- PESTAÑA 4: SECADO ---
        with tabs[3]:
            st.subheader("🏭 Producción de OGS (kg)")
            if not df_secado_filt.empty and 'OGS_Salida' in df_secado_filt.columns:
                if not is_v2 or planta_activa == "Todas":
                    fig_ogs = px.bar(df_secado_hoy, x="Centro", y="OGS_Salida", color_discrete_sequence=['#d97706'])
                else:
                    df_trend = df_secado_filt.groupby('fecha', as_index=False)['OGS_Salida'].sum().sort_values('fecha')
                    fig_ogs = px.line(df_trend, x="fecha", y="OGS_Salida", markers=True, line_shape="spline", color_discrete_sequence=['#d97706'], title=f"Evolución OGS - {planta_activa}")
                
                fig_ogs.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_ogs, use_container_width=True)

        # --- PESTAÑA 5: EXTRACCIÓN ---
        with tabs[4]:
            st.subheader("⚗️ Producción de Aceite de Extracción (kg)")
            if not df_ext_filt.empty and 'Aceite_Prod' in df_ext_filt.columns:
                if not is_v2 or planta_activa == "Todas":
                    fig_ext = px.bar(df_ext_hoy, x="Extractora", y="Aceite_Prod", color_discrete_sequence=['#eab308'])
                else:
                    df_trend = df_ext_filt.groupby('fecha', as_index=False)['Aceite_Prod'].sum().sort_values('fecha')
                    fig_ext = px.line(df_trend, x="fecha", y="Aceite_Prod", markers=True, line_shape="spline", color_discrete_sequence=['#eab308'], title=f"Evolución Semanal de Extracción - {planta_activa}")
                
                fig_ext.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_ext, use_container_width=True)

        # --- PESTAÑA 6: ELECTRICIDAD ---
        with tabs[5]:
            st.subheader("⚡ Generación Eléctrica (kWh)")
            if not df_elec_filt.empty and 'Generada_kWh' in df_elec_filt.columns:
                if not is_v2 or planta_activa == "Todas":
                    fig_elec = px.bar(df_elec_hoy, x="Planta", y="Generada_kWh", color_discrete_sequence=['#3b82f6'])
                else:
                    df_trend = df_elec_filt.groupby('fecha', as_index=False)['Generada_kWh'].sum().sort_values('fecha')
                    fig_elec = px.line(df_trend, x="fecha", y="Generada_kWh", markers=True, line_shape="spline", color_discrete_sequence=['#3b82f6'], title=f"Curva de Generación Eléctrica Semanal - {planta_activa}")
                
                fig_elec.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_elec, use_container_width=True)

        # --- PESTAÑA 7: OBJETIVOS ---
        with tabs[6]:
            st.subheader("🎯 Configuración Estratégica de Objetivos")
            if role == "presidente":
                edited_obj = st.data_editor(df_obj, num_rows="dynamic", use_container_width=True, hide_index=True)
                if st.button("💾 Guardar y Aplicar Cambios", type="primary"):
                    save_objectives(edited_obj)
                    st.success("¡Objetivos actualizados! Recargando...")
                    st.rerun()
            else:
                st.dataframe(df_obj.style.format(thousands=","), hide_index=True, use_container_width=True)
