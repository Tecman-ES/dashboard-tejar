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
# La clave ahora se lee de forma segura y oculta desde el archivo .env
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
            # Intenta cargar el logo real, con un tamaño máximo fijo para que no se pixele
            try:
                st.image("logo.png", width=250) 
            except Exception:
                st.markdown("<div style='text-align: center; font-size: 4rem;'>🏭</div>", unsafe_allow_html=True)
                
            st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            
            if st.button("Entrar", use_container_width=True):
                # Extraer lista de usuarios desde la caja fuerte
                users_env = os.getenv("USUARIOS_AUTORIZADOS", "")
                usuarios_validos = {}
                
                if users_env:
                    # El formato en la caja fuerte será: usuario:contraseña:rol,usuario2:contraseña2:rol2
                    for u in users_env.split(","):
                        partes = u.split(":")
                        if len(partes) == 3:
                            user, pwd, role = partes
                            usuarios_validos[user.strip()] = {"pwd": pwd.strip(), "role": role.strip()}
                
                # Comprobar si el usuario existe y la contraseña cuadra
                if usuario in usuarios_validos and password == usuarios_validos[usuario]["pwd"]:
                    st.session_state["login_ok"] = True
                    st.session_state["role"] = usuarios_validos[usuario]["role"]
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no autorizado")
        return False
    return True

# --- MAPEO DE JERARQUÍAS ---
def get_centro_from_planta(planta_name):
    """Asigna instalaciones específicas a su Centro Matriz"""
    p_upper = str(planta_name).upper()
    if "BAENA" in p_upper: return "Baena"
    if "VETEJAR" in p_upper or "ALGODONALES" in p_upper or "AUTOGENERACI" in p_upper: return "Palenciana"
    if "TEJAR" in p_upper: return "El Tejar"
    return planta_name

# --- SISTEMA DE OBJETIVOS EN MEMORIA ---
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
        if obj_col_name in df.columns:
            df = df.drop(columns=[obj_col_name])
        return pd.merge(df, sub_obj, on=join_col, how="left")

    df_cent = merge_obj(df_cent, "Centro", "Centrifugacion", "Optimo")
    df_secado = merge_obj(df_secado, "Centro", "Secado", "Obj_OGS")
    df_ext = merge_obj(df_ext, "Extractora", "Extraccion", "Obj_Aceite")
    df_elec = merge_obj(df_elec, "Planta", "Electricidad", "Optimo_kWh")
    return df_cent, df_secado, df_ext, df_elec

# --- FUNCIONES DE LIMPIEZA Y HTML ---
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
# MOTOR DE CONEXIÓN A BASE DE DATOS (NUBE)
# ==============================================================================
@st.cache_data(ttl=60) # Cache para no saturar la base de datos cada segundo
def get_data_from_db(fecha_reporte):
    try:
        engine = create_engine(DATABASE_URL)
        fecha_str = fecha_reporte.strftime('%Y-%m-%d')
        
        # Leer todas las tablas para ese día específico
        with engine.connect() as conn:
            df_aport = pd.read_sql(f"SELECT * FROM aportaciones WHERE fecha = '{fecha_str}'", conn)
            df_ex = pd.read_sql(f"SELECT * FROM existencias WHERE fecha = '{fecha_str}'", conn)
            df_cent = pd.read_sql(f"SELECT * FROM centrifugacion WHERE fecha = '{fecha_str}'", conn)
            df_sec = pd.read_sql(f"SELECT * FROM secado WHERE fecha = '{fecha_str}'", conn)
            df_ext = pd.read_sql(f"SELECT * FROM extraccion WHERE fecha = '{fecha_str}'", conn)
            df_elec = pd.read_sql(f"SELECT * FROM electricidad WHERE fecha = '{fecha_str}'", conn)
            df_cons_sec = pd.read_sql(f"SELECT * FROM consumo_secado WHERE fecha = '{fecha_str}'", conn)
            df_cons_ext = pd.read_sql(f"SELECT * FROM consumo_extraccion WHERE fecha = '{fecha_str}'", conn)
            df_cons_elec = pd.read_sql(f"SELECT * FROM consumo_electricidad WHERE fecha = '{fecha_str}'", conn)

        # Renombrar columnas para mantener compatibilidad visual con los gráficos de Streamlit
        if not df_aport.empty: df_aport.rename(columns={'planta':'Planta', 'centro':'Centro', 'hoy_kg':'Hoy (kg)', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_ex.empty: df_ex.rename(columns={'material':'Material', 'total_kilos':'Total Kilos'}, inplace=True)
        if not df_cent.empty: df_cent.rename(columns={'centro':'Centro', 'entrada_alperujo':'Entrada_Alperujo', 'aceite_prod':'Aceite_Prod', 'rdto_obtenido':'Rdto_Obtenido', 'acidez':'Acidez', 'acidez_mensual':'Acidez_Mensual', 'acidez_campana':'Acidez_Campana', 'media_mensual':'Media_Mensual', 'rdto_campana':'Rdto_Campana', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_sec.empty: df_sec.rename(columns={'centro':'Centro', 'entrada_alperujo':'Entrada_Alperujo', 'entrada_alperujo_mes':'Entrada_Alperujo_Mes', 'ogs_salida':'OGS_Salida', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_ext.empty: df_ext.rename(columns={'extractora':'Extractora', 'centro':'Centro', 'ogs_procesado':'OGS_Procesado', 'aceite_prod':'Aceite_Prod', 'acum_mensual':'Acum. Mensual', 'optimo_subifor':'Optimo_Subifor', 'salida_aceite':'Salida_Aceite'}, inplace=True)
        if not df_elec.empty: df_elec.rename(columns={'planta':'Planta', 'centro':'Centro', 'generada_kwh':'Generada_kWh', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_cons_sec.empty: df_cons_sec.rename(columns={'centro':'Centro', 'consumo_hueso':'Consumo_Hueso', 'consumo_orujillo':'Consumo_Orujillo', 'consumo_poda':'Consumo_Poda', 'consumo_hoja':'Consumo_Hoja'}, inplace=True)
        if not df_cons_ext.empty: df_cons_ext.rename(columns={'extractora':'Extractora', 'centro':'Centro', 'consumo_hueso':'Consumo_Hueso', 'consumo_orujillo':'Consumo_Orujillo', 'consumo_poda':'Consumo_Poda', 'consumo_hoja':'Consumo_Hoja'}, inplace=True)
        if not df_cons_elec.empty: df_cons_elec.rename(columns={'planta':'Planta', 'centro':'Centro', 'consumo_biomasa':'Consumo_Biomasa', 'consumo_biomasa_mes':'Consumo_Biomasa_Mes'}, inplace=True)

        # Retornar True (hay datos) y las tablas
        has_data = not df_aport.empty
        return has_data, df_aport, df_ex, df_cent, df_sec, df_ext, df_elec, df_cons_sec, df_cons_ext, df_cons_elec
        
    except Exception as e:
        print(f"Error base de datos: {e}")
        return False, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- SMART FILTER MULTI-COLUMNA ---
def filter_dataframe(df, column_names, planta_seleccionada):
    if df.empty or planta_seleccionada == "Todas":
        return df
    if isinstance(column_names, str):
        column_names = [column_names]
    mask = pd.Series(False, index=df.index)
    for col in column_names:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(planta_seleccionada, case=False, na=False)
    return df[mask].reset_index(drop=True)

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    role = st.session_state["role"]
    
    col_logo, col_titulo, col_logout = st.columns([1, 8, 1])
    with col_logo:
        # Intenta cargar el logo real en la cabecera, más pequeñito
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
        fecha_activa = st.date_input("📅 Selecciona la Fecha del Reporte:", date(2026, 4, 14)) # Por defecto, la fecha de la prueba
    
    with col_filter:
        plantas_disponibles = ["Todas", "Baena", "Cabra", "Marchena", "Palenciana", "Pedro Abad", "Espejo", "Bogarre", "Mancha Real", "Algodonales", "Vetejar", "El Tejar"]
        planta_activa = st.selectbox("📍 Filtro Global por Planta/Centro:", plantas_disponibles)

    # 🚀 EXTRACCIÓN AUTOMÁTICA DESDE LA NUBE
    with st.spinner('☁️ Conectando con la base de datos en producción (Neon)...'):
        has_data, df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, df_cons_secado, df_cons_ext, df_cons_elec = get_data_from_db(fecha_activa)

    if not has_data:
        st.warning(f"⚠️ Aún no hay ningún parte subido a la base de datos para el día **{fecha_activa.strftime('%d/%m/%Y')}**.")
        if role == "oficina":
            st.info("ℹ️ Recuerda ejecutar el script de extracción local ('extractor_tejar.py') para enviar los datos de hoy.")
    else:
        st.success(f"☁️ Datos sincronizados correctamente desde la nube para el **{fecha_activa.strftime('%d/%m/%Y')}**.")
        
        # Cargar y aplicar objetivos
        df_obj = load_objectives()
        df_cent, df_secado, df_ext, df_elec = apply_objectives(df_cent, df_secado, df_ext, df_elec, df_obj)
        
        # Aplicar filtros globales
        df_aport = filter_dataframe(df_aport, ["Planta", "Centro"], planta_activa)
        df_cent = filter_dataframe(df_cent, ["Centro", "Planta"], planta_activa)
        df_secado = filter_dataframe(df_secado, ["Centro", "Planta"], planta_activa)
        df_ext = filter_dataframe(df_ext, ["Extractora", "Centro"], planta_activa)
        df_elec = filter_dataframe(df_elec, ["Centro", "Planta"], planta_activa)
        df_obj_filtered = filter_dataframe(df_obj, ["Centro", "Planta"], planta_activa)

        tabs = st.tabs(["👁️ Visión General", "📦 Aportaciones", "🌀 Centrifugación", "🔥 Secado", "⚗️ Extracción", "⚡ Electricidad", "🎯 Mis Objetivos"])

        # --- PESTAÑA 1: VISIÓN GENERAL ---
        with tabs[0]:
            if not df_aport.empty or not df_elec.empty:
                col_resumen, col_noticias = st.columns([2, 1])
                with col_resumen:
                    st.subheader(f"Resumen Ejecutivo - {planta_activa.upper()}")
                    
                    total_orujo = df_aport['Hoy (kg)'].sum() if not df_aport.empty and 'Hoy (kg)' in df_aport.columns else 0
                    total_alperujo_sec = df_secado['Entrada_Alperujo'].sum() if not df_secado.empty and 'Entrada_Alperujo' in df_secado.columns else 0
                    total_ogs_sec = df_secado['OGS_Salida'].sum() if not df_secado.empty and 'OGS_Salida' in df_secado.columns else 0
                    total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 0
                    total_aceite_cent = df_cent['Aceite_Prod'].sum() if not df_cent.empty and 'Aceite_Prod' in df_cent.columns else 0
                    total_aceite_ext = df_ext['Aceite_Prod'].sum() if not df_ext.empty and 'Aceite_Prod' in df_ext.columns else 0
                    
                    total_orujo_mes = df_aport['Acum. Mensual'].sum() if not df_aport.empty and 'Acum. Mensual' in df_aport.columns else 0
                    total_alperujo_sec_mes = df_secado['Entrada_Alperujo_Mes'].sum() if not df_secado.empty and 'Entrada_Alperujo_Mes' in df_secado.columns else 0
                    total_ogs_sec_mes = df_secado['Acum. Mensual'].sum() if not df_secado.empty and 'Acum. Mensual' in df_secado.columns else 0
                    total_elec_mes = df_elec['Acum. Mensual'].sum() if not df_elec.empty and 'Acum. Mensual' in df_elec.columns else 0
                    total_aceite_cent_mes = df_cent['Acum. Mensual'].sum() if not df_cent.empty and 'Acum. Mensual' in df_cent.columns else 0
                    total_aceite_ext_mes = df_ext['Acum. Mensual'].sum() if not df_ext.empty and 'Acum. Mensual' in df_ext.columns else 0
                    
                    target_elec = df_obj_filtered[df_obj_filtered['Area']=='Electricidad']['Objetivo_Diario'].sum()
                    target_cent = df_obj_filtered[df_obj_filtered['Area']=='Centrifugacion']['Objetivo_Diario'].sum()
                    target_ext = df_obj_filtered[df_obj_filtered['Area']=='Extraccion']['Objetivo_Diario'].sum()
                    target_sec = df_obj_filtered[df_obj_filtered['Area']=='Secado']['Objetivo_Diario'].sum()
                    
                    st.markdown("#### 📅 Producción Diaria (Hoy)")
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(get_kpi_card_html("Orujo Recibido", "📦", total_orujo, "kg", "<div class='kpi-delta delta-neutral'>Materia prima cruda</div>", ""), unsafe_allow_html=True)
                    with c2: st.markdown(get_kpi_card_html("Alperujo Procesado", "🔄", total_alperujo_sec, "kg", "<div class='kpi-delta delta-neutral'>Entrada a secaderos</div>", ""), unsafe_allow_html=True)
                    with c3: st.markdown(get_kpi_card_html("OGS Producido", "🏭", total_ogs_sec, "kg", get_delta_html(total_ogs_sec, target_sec), "orange"), unsafe_allow_html=True)
                    
                    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    
                    c4, c5, c6 = st.columns(3)
                    with c4: st.markdown(get_kpi_card_html("Aceite Centrif.", "💧", total_aceite_cent, "kg", get_delta_html(total_aceite_cent, target_cent), "yellow"), unsafe_allow_html=True)
                    with c5: st.markdown(get_kpi_card_html("Aceite Extrac.", "⚗️", total_aceite_ext, "kg", get_delta_html(total_aceite_ext, target_ext), "orange"), unsafe_allow_html=True)
                    with c6: st.markdown(get_kpi_card_html("Electricidad", "⚡", total_elec, "kWh", get_delta_html(total_elec, target_elec), "blue"), unsafe_allow_html=True)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    
                    st.markdown("#### 📊 Producción Acumulada Mensual")
                    m1, m2, m3 = st.columns(3)
                    with m1: st.markdown(get_monthly_card_html("Orujo Recibido", "📦", total_orujo_mes, "kg", ""), unsafe_allow_html=True)
                    with m2: st.markdown(get_monthly_card_html("Alperujo Procesado", "🔄", total_alperujo_sec_mes, "kg", ""), unsafe_allow_html=True)
                    with m3: st.markdown(get_monthly_card_html("OGS Producido", "🏭", total_ogs_sec_mes, "kg", "orange"), unsafe_allow_html=True)
                    
                    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    
                    m4, m5, m6 = st.columns(3)
                    with m4: st.markdown(get_monthly_card_html("Aceite Centrif.", "💧", total_aceite_cent_mes, "kg", "yellow"), unsafe_allow_html=True)
                    with m5: st.markdown(get_monthly_card_html("Aceite Extrac.", "⚗️", total_aceite_ext_mes, "kg", "orange"), unsafe_allow_html=True)
                    with m6: st.markdown(get_monthly_card_html("Electricidad", "⚡", total_elec_mes, "kWh", "blue"), unsafe_allow_html=True)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    st.write("### 🤖 Análisis Operativo IA")
                    
                    alertas = []
                    if not df_cent.empty and 'Acidez' in df_cent.columns:
                        for _, row in df_cent.iterrows():
                            val_acidez = row.get('Acidez', pd.NA)
                            if pd.notnull(val_acidez) and isinstance(val_acidez, (int, float)) and val_acidez > 3:
                                alertas.append(f"⚠️ **Centrifugación {row.get('Centro', '')}:** Acidez crítica detectada ({val_acidez}%)")
                    
                    if not df_elec.empty and 'Generada_kWh' in df_elec.columns and 'Optimo_kWh' in df_elec.columns:
                        for _, row in df_elec.iterrows():
                            val_gen, val_opt = row['Generada_kWh'], row['Optimo_kWh']
                            if pd.notnull(val_gen) and pd.notnull(val_opt) and val_gen > val_opt:
                                alertas.append(f"✅ **Electricidad {row.get('Planta', '')}:** Rendimiento supera el objetivo estratégico.")

                    if not alertas:
                        st.success(f"✅ **Operaciones Normales en {planta_activa}:** Todos los parámetros monitorizados están dentro de la normalidad.")
                    else:
                        for a in alertas:
                            if "⚠️" in a: st.error(a)
                            else: st.success(a)

                with col_noticias:
                    st.subheader("📈 Mercado: Aceite de Orujo")
                    
                    st.markdown("""
                    <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                        <div style="font-size: 0.85rem; color: #64748b; font-weight: bold; text-transform: uppercase;">Precio Medio (Crudo)</div>
                        <div style="font-size: 2rem; font-weight: 800; color: #0f172a;">1.24 <span style="font-size: 1rem; color: #94a3b8;">€/kg</span> <span style="font-size: 1rem; color: #16a34a;">▲ +0.01</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    df_precio = pd.DataFrame({
                        "Día": ["09/04", "10/04", "11/04", "12/04", "13/04", "14/04", "15/04"],
                        "Precio": [1.15, 1.16, 1.18, 1.17, 1.20, 1.23, 1.24]
                    })
                    
                    fig_precio = go.Figure()
                    fig_precio.add_trace(go.Scatter(
                        x=df_precio["Día"], y=df_precio["Precio"],
                        mode='lines+markers',
                        line=dict(color='#eab308', width=3),
                        marker=dict(size=6, color='#d97706'),
                        fill='tozeroy',
                        fillcolor='rgba(234, 179, 8, 0.1)',
                        name="Precio €/kg"
                    ))
                    fig_precio.update_layout(
                        margin=dict(l=0, r=0, t=10, b=20),
                        height=120,
                        xaxis=dict(showgrid=False, showticklabels=True, tickfont=dict(size=10, color='#64748b'), fixedrange=True),
                        yaxis=dict(showgrid=False, showticklabels=False, range=[1.1, 1.3], fixedrange=True),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_precio, use_container_width=True, config={'displayModeBar': False})

                    st.write("<br>", unsafe_allow_html=True)
                    st.subheader("📰 Actualidad del Sector")
                    st.markdown("""
                    <div class="news-card">
                        <div class="news-title">El precio del AOVE se estabiliza en origen</div>
                        <div class="news-source">Fuente: OleoMerca | Abril 2026</div>
                        <div class="news-snippet">Las operaciones en picual de alta calidad se cierran en torno a los 4,20€/kg, marcando un freno a las caídas de las últimas tres semanas...</div>
                        <a href="https://www.olimerca.com/" target="_blank" class="read-more" style="display: inline-block; margin-top: 8px;">Leer completa →</a>
                    </div>
                    <div class="news-card">
                        <div class="news-title">Nuevo marco normativo para la cogeneración</div>
                        <div class="news-source">Fuente: Revista Alcuza | Abril 2026</div>
                        <div class="news-snippet">El Ministerio de Transición Ecológica ha publicado el borrador que bonificará a las plantas extractoras que demuestren una alta eficiencia...</div>
                        <a href="https://www.mercacei.com/" target="_blank" class="read-more" style="display: inline-block; margin-top: 8px;">Leer completa →</a>
                    </div>
                    """, unsafe_allow_html=True)

        # --- PESTAÑA 2: APORTACIONES Y EXISTENCIAS ---
        with tabs[1]:
            col_hoy, col_mes = st.columns(2)
            with col_hoy:
                st.subheader("Orujo Aportado Hoy (kg)")
                if not df_aport.empty and 'Planta' in df_aport.columns and 'Hoy (kg)' in df_aport.columns:
                    fig_aport = px.bar(df_aport, x="Planta", y="Hoy (kg)")
                    fig_aport.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8d6e63')
                    fig_aport.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_aport, use_container_width=True)
                else: st.info("Faltan datos de Aportaciones diarias.")
                
            with col_mes:
                st.subheader("Acumulado Mensual (kg)")
                if not df_aport.empty and 'Planta' in df_aport.columns and 'Acum. Mensual' in df_aport.columns:
                    fig_aport_mes = px.bar(df_aport, x="Planta", y="Acum. Mensual")
                    fig_aport_mes.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#60a5fa')
                    fig_aport_mes.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_aport_mes, use_container_width=True)
                else: st.info("Faltan datos de Acumulado Mensual.")
                
            if planta_activa == "Todas":
                st.markdown("---")
                st.subheader("📦 Estado General de Existencias")
                if not df_existencias.empty:
                    cols_ex = st.columns(len(df_existencias))
                    for i, row in df_existencias.iterrows():
                        with cols_ex[i]:
                            mat_name = row['Material']
                            icon = "📦"
                            if "Hueso" in mat_name: icon = "🫒"
                            elif "Orujillo" in mat_name: icon = "🟤"
                            elif "Hoja" in mat_name: icon = "🍃"
                            
                            st.markdown(get_kpi_card_html(mat_name, icon, row['Total Kilos'], "kg", "", "blue"), unsafe_allow_html=True)
                else:
                    st.info("Sin datos de existencias.")
                    
            with st.expander("📊 Ver tabla de datos detallada (Aportaciones)"):
                display_styled_table(df_aport, download_name="aportaciones_tejar.csv")

        # --- PESTAÑA 3: CENTRIFUGACIÓN ---
        with tabs[2]:
            st.subheader("🌀 Análisis Detallado de Centrifugación")
            
            col1, col2 = st.columns(2)
            with col1:
                if not df_cent.empty and 'Centro' in df_cent.columns and 'Entrada_Alperujo' in df_cent.columns:
                    fig_entrada_cent = px.bar(df_cent, x="Centro", y="Entrada_Alperujo", title="Entrada de Alperujo (kg)")
                    fig_entrada_cent.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#4ade80')
                    fig_entrada_cent.update_layout(yaxis=dict(tickformat=","), margin=dict(t=40))
                    st.plotly_chart(fig_entrada_cent, use_container_width=True)
                else: st.info("Faltan datos de Entrada de Alperujo.")
                
            with col2:
                if not df_cent.empty and 'Centro' in df_cent.columns and 'Aceite_Prod' in df_cent.columns:
                    fig_cent_comp = go.Figure()
                    fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Aceite_Prod'], name='Producido', marker_color='#fbbf24', text=df_cent['Aceite_Prod'], texttemplate='%{text:,.0f}'))
                    if 'Optimo' in df_cent.columns:
                        fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Optimo'], name='Óptimo', marker_color='#94a3b8', text=df_cent['Optimo'], texttemplate='%{text:,.0f}'))
                    fig_cent_comp.update_layout(title="Aceite Producido vs Óptimo Industrial (kg)", barmode='group', yaxis=dict(tickformat=","), margin=dict(t=40))
                    st.plotly_chart(fig_cent_comp, use_container_width=True)
                else: st.info("Faltan datos de Aceite Producido.")
                
            col3, col4 = st.columns(2)
            with col3:
                if not df_cent.empty and 'Rdto_Obtenido' in df_cent.columns:
                    fig_rdto = go.Figure()
                    
                    if 'Media_Mensual' in df_cent.columns and df_cent['Media_Mensual'].notna().any():
                        colors = ['#22c55e' if r >= m else '#ef4444' for r, m in zip(df_cent['Rdto_Obtenido'], df_cent['Media_Mensual'].fillna(0))]
                    else:
                        colors = ['#3b82f6'] * len(df_cent)
                        
                    fig_rdto.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Rdto_Obtenido'], name='Rdto. Diario (%)', marker_color=colors, text=df_cent['Rdto_Obtenido'], texttemplate='%{text:.2f}%', textposition='auto'))
                    
                    if 'Media_Mensual' in df_cent.columns and df_cent['Media_Mensual'].notna().any():
                        fig_rdto.add_trace(go.Scatter(x=df_cent['Centro'], y=df_cent['Media_Mensual'], mode='markers+text', name='Media Mensual (%)', text=df_cent['Media_Mensual'], texttemplate='%{text:.2f}%', textposition='top center', textfont=dict(color='#0f172a', size=14, weight='bold'), marker=dict(symbol='line-ew', size=45, color='#0f172a', line=dict(width=3))))
                        
                    fig_rdto.update_layout(title="Rendimiento Diario vs Media Mensual (%)<br><sup><span style='color:#22c55e'>Verde</span>: Supera media | <span style='color:#ef4444'>Rojo</span>: Por debajo de media</sup>", yaxis_title="Rendimiento (%)", margin=dict(t=60))
                    st.plotly_chart(fig_rdto, use_container_width=True)
                    
            with col4:
                if not df_cent.empty and 'Acidez' in df_cent.columns and df_cent['Acidez'].notna().any():
                    df_acidez = df_cent.dropna(subset=['Acidez']).copy()
                    if not df_acidez.empty:
                        colors = ['#ef4444' if val > 3 else '#22c55e' for val in df_acidez['Acidez']]
                        fig_acidez = go.Figure(data=[go.Bar(x=df_acidez['Centro'], y=df_acidez['Acidez'], marker_color=colors, text=df_acidez['Acidez'], texttemplate='%{text:.2f}%', textposition='auto')])
                        fig_acidez.add_hline(y=3, line_dash="dash", line_color="#ef4444", annotation_text="Límite (3%)", annotation_position="top right")
                        fig_acidez.update_layout(title="Control de Calidad: Acidez del Aceite (%)", yaxis_title="Acidez (%)", margin=dict(t=40))
                        st.plotly_chart(fig_acidez, use_container_width=True)
                else:
                    st.info("No hay datos de acidez registrados para graficar.")
                    
            st.markdown("#### 📈 Producción Acumulada")
            if not df_cent.empty and 'Acum. Mensual' in df_cent.columns:
                fig_acum = px.bar(df_cent, x="Centro", y="Acum. Mensual", title="Aceite Acumulado Mensual (kg)")
                fig_acum.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8b5cf6')
                fig_acum.update_layout(yaxis=dict(tickformat=","), margin=dict(t=40))
                st.plotly_chart(fig_acum, use_container_width=True)

            with st.expander("📊 Ver tabla de datos detallada (Centrifugación)"):
                display_styled_table(df_cent, "Centrifugacion", download_name="centrifugacion_tejar.csv")

        # --- PESTAÑA 4: SECADO ---
        with tabs[3]:
            total_ogs = df_secado['OGS_Salida'].sum() if not df_secado.empty and 'OGS_Salida' in df_secado.columns else 0
            st.markdown(f"### 🏭 Total Orujo Graso Seco (OGS) Generado: **{total_ogs:,.0f} kg**")
            st.write("<hr>", unsafe_allow_html=True)
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.subheader("Entrada Alperujo Procesado (kg)")
                if not df_secado.empty and 'Entrada_Alperujo' in df_secado.columns and df_secado['Entrada_Alperujo'].sum() > 0:
                    fig_alperujo_sec = px.bar(df_secado, x="Centro", y="Entrada_Alperujo")
                    fig_alperujo_sec.update_traces(marker_color='#4ade80', texttemplate='%{y:,.0f}', textposition='outside')
                    fig_alperujo_sec.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_alperujo_sec, use_container_width=True)
                else:
                    st.info("Sin datos de entrada de alperujo.")
                    
            with col_s2:
                st.subheader("OGS Salida vs Objetivo (kg)")
                if not df_secado.empty and 'Centro' in df_secado.columns and 'OGS_Salida' in df_secado.columns:
                    fig_ogs = px.bar(df_secado, x="Centro", y=["OGS_Salida", "Obj_OGS"] if 'Obj_OGS' in df_secado.columns else "OGS_Salida", barmode="group", color_discrete_sequence=['#d97706', '#fcd34d'])
                    fig_ogs.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_ogs, use_container_width=True)
                else: st.info(f"Sin datos de Secado para: {planta_activa}")

            st.markdown("#### 📊 Acumulado Mensual (OGS)")
            if not df_secado.empty and 'Acum. Mensual' in df_secado.columns and df_secado['Acum. Mensual'].sum() > 0:
                fig_ogs_mes = px.bar(df_secado, x="Centro", y="Acum. Mensual")
                fig_ogs_mes.update_traces(marker_color='#f59e0b', texttemplate='%{y:,.0f}', textposition='outside')
                fig_ogs_mes.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_ogs_mes, use_container_width=True)
        
            if not df_cons_secado.empty:
                df_cons_secado_filt = filter_dataframe(df_cons_secado, ["Centro", "Planta"], planta_activa)
                if not df_cons_secado_filt.empty:
                    st.markdown("#### 🔥 Consumo Térmico Mensual en Secaderos")
                    df_melted = df_cons_secado_filt.melt(id_vars=["Centro"], value_vars=["Consumo_Hueso", "Consumo_Orujillo", "Consumo_Poda", "Consumo_Hoja"], var_name="Material", value_name="Kilos")
                    df_melted = df_melted[df_melted["Kilos"] > 0]
                    
                    if not df_melted.empty:
                        df_melted['Material'] = df_melted['Material'].str.replace('Consumo_', '')
                        fig_cons = px.bar(df_melted, x="Centro", y="Kilos", color="Material", 
                                          title="Acumulado Mensual de Biomasa (kg)", 
                                          color_discrete_map={"Hueso": "#78350f", "Orujillo": "#475569", "Poda": "#4d7c0f", "Hoja": "#84cc16"})
                        st.plotly_chart(fig_cons, use_container_width=True)
                    else:
                        st.info("Sin consumos térmicos mensuales registrados.")

            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_secado, download_name="secado_tejar.csv")

        # --- PESTAÑA 5: EXTRACCIÓN ---
        with tabs[4]:
            col_ext1, col_ext2 = st.columns(2)
            with col_ext1:
                st.subheader("Entrada de Orujo a Extractora (kg)")
                if not df_ext.empty and 'OGS_Procesado' in df_ext.columns and df_ext['OGS_Procesado'].sum() > 0:
                    fig_ogs_ext = px.bar(df_ext, x="Extractora", y="OGS_Procesado")
                    fig_ogs_ext.update_traces(marker_color='#8d6e63', texttemplate='%{y:,.0f}', textposition='outside')
                    fig_ogs_ext.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_ogs_ext, use_container_width=True)
                else:
                    st.info("No hay datos de entrada de orujo registrados.")
                    
            with col_ext2:
                st.subheader("Producción de Aceite vs Objetivo (kg)")
                if not df_ext.empty and 'Aceite_Prod' in df_ext.columns:
                    opt_col = "Optimo_Subifor" if "Optimo_Subifor" in df_ext.columns and df_ext["Optimo_Subifor"].sum() > 0 else "Obj_Aceite"
                    fig_aceite = px.bar(df_ext, x="Extractora", y=["Aceite_Prod", opt_col] if opt_col in df_ext.columns else "Aceite_Prod", barmode="group", color_discrete_sequence=['#eab308', '#fef08a'])
                    fig_aceite.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_aceite, use_container_width=True)
                    
            if not df_ext.empty and 'Salida_Aceite' in df_ext.columns and df_ext['Salida_Aceite'].sum() > 0:
                st.markdown("#### 🚢 Ventas y Salidas de Aceite (kg)")
                fig_ventas = px.bar(df_ext, x="Extractora", y="Salida_Aceite")
                fig_ventas.update_traces(marker_color='#0ea5e9', texttemplate='%{y:,.0f}', textposition='outside')
                fig_ventas.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_ventas, use_container_width=True)
                
            if not df_cons_ext.empty:
                df_cons_ext_filt = filter_dataframe(df_cons_ext, ["Extractora", "Centro"], planta_activa)
                if not df_cons_ext_filt.empty:
                    st.markdown("#### 🔥 Consumo Térmico Mensual en Extracción")
                    df_melted_ext = df_cons_ext_filt.melt(id_vars=["Extractora"], value_vars=["Consumo_Hueso", "Consumo_Orujillo", "Consumo_Poda", "Consumo_Hoja"], var_name="Material", value_name="Kilos")
                    df_melted_ext = df_melted_ext[df_melted_ext["Kilos"] > 0]
                    
                    if not df_melted_ext.empty:
                        df_melted_ext['Material'] = df_melted_ext['Material'].str.replace('Consumo_', '')
                        fig_cons_ext = px.bar(df_melted_ext, x="Extractora", y="Kilos", color="Material", 
                                          title="Acumulado Mensual de Biomasa (kg)", 
                                          color_discrete_map={"Hueso": "#78350f", "Orujillo": "#475569", "Poda": "#4d7c0f", "Hoja": "#84cc16"})
                        st.plotly_chart(fig_cons_ext, use_container_width=True)
                    else:
                        st.info("Sin consumos térmicos mensuales registrados en Extracción.")
                    
            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_ext, download_name="extraccion_tejar.csv")

        # --- PESTAÑA 6: ELECTRICIDAD ---
        with tabs[5]:
            total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 0
            st.markdown(f"### ⚡ Total Generado Hoy: **{total_elec:,.0f} kWh**")
            st.write("<hr>", unsafe_allow_html=True)
            
            st.subheader("Rendimiento Eléctrico Diario")
            
            def_opts = {'BAENA': 358330, 'VETEJAR': 190270, 'ALGODONALES': 91400, 'AUTOGENERACIÓN': 60000, 'AUTOGENERACION': 60000}
            
            if not df_elec.empty and 'Planta' in df_elec.columns and 'Generada_kWh' in df_elec.columns:
                st.write("*(Los velocímetros muestran la producción en azul y la línea oscura marca el objetivo estratégico)*")
                
                plantas_records = df_elec.to_dict('records')
                for i in range(0, len(plantas_records), 4):
                    cols_velocimetros = st.columns(4)
                    for j in range(4):
                        if i + j < len(plantas_records):
                            row = plantas_records[i + j]
                            gen = row['Generada_kWh'] if pd.notnull(row['Generada_kWh']) else 0
                            
                            opt = row.get('Optimo_kWh', 0)
                            if pd.isna(opt) or opt == 0:
                                planta_str = str(row['Planta']).upper()
                                for k, v in def_opts.items():
                                    if k in planta_str:
                                        opt = v
                                        break
                            if opt == 0: opt = 1
                            
                            fig_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = gen,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': str(row['Planta']), 'font': {'size': 20, 'color': '#0f172a'}},
                                delta = {'reference': opt, 'increasing': {'color': "#16a34a"}, 'decreasing': {'color': "#dc2626"}, 'valueformat': ",.0f"},
                                number = {'font': {'size': 28, 'color': '#0f172a'}, 'valueformat': ",.0f"},
                                gauge = {
                                    'axis': {'range': [None, max(opt, gen) * 1.2], 'tickwidth': 1, 'tickcolor': "#0f172a", 'tickfont': {'color': '#0f172a'}},
                                    'bar': {'color': "#3b82f6", 'thickness': 0.7}, 
                                    'bgcolor': "rgba(0,0,0,0)",
                                    'borderwidth': 1,
                                    'bordercolor': "#cbd5e1",
                                    'steps': [
                                        {'range': [0, opt*0.8], 'color': '#fee2e2'},      
                                        {'range': [opt*0.8, opt], 'color': '#fef08a'},    
                                        {'range': [opt, max(opt, gen)*1.2], 'color': '#dcfce3'} 
                                    ],
                                    'threshold': {'line': {'color': "#0f172a", 'width': 4}, 'thickness': 0.85, 'value': opt}
                                }
                            ))
                            fig_gauge.update_layout(margin=dict(t=60, b=20, l=20, r=20), height=320, paper_bgcolor="rgba(0,0,0,0)")
                            
                            with cols_velocimetros[j]:
                                st.plotly_chart(fig_gauge, use_container_width=True)
                    
            else: st.info(f"Faltan datos eléctricos para la planta: {planta_activa}")
            
            if not df_cons_elec.empty:
                df_cons_elec_filt = filter_dataframe(df_cons_elec, ["Centro", "Planta"], planta_activa)
                if not df_cons_elec_filt.empty:
                    st.markdown("#### 🔥 Consumo Térmico Mensual en Generación (Biomasa)")
                    fig_cons_elec = px.bar(df_cons_elec_filt, x="Planta", y="Consumo_Biomasa_Mes", 
                                           title="Acumulado Mensual de Combustible (kg)", 
                                           color_discrete_sequence=["#78350f"])
                    fig_cons_elec.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                    fig_cons_elec.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                    st.plotly_chart(fig_cons_elec, use_container_width=True)
            
            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_elec, download_name="electricidad_tejar.csv")

        # --- PESTAÑA 7: OBJETIVOS ---
        with tabs[6]:
            st.subheader("🎯 Configuración Estratégica de Objetivos")
            st.info("Estos objetivos se aplican localmente. En una versión final, también se guardarían en la base de datos de Neon.")
            
            if role == "presidente":
                st.write("Doble clic en la columna **'Objetivo_Diario'** para modificarlos.")
                edited_obj = st.data_editor(df_obj, num_rows="dynamic", use_container_width=True, hide_index=True)
                
                if st.button("💾 Guardar y Aplicar Cambios", type="primary"):
                    save_objectives(edited_obj)
                    st.success("¡Objetivos actualizados! Recargando...")
                    st.rerun()
            else:
                st.write("*(Modo solo lectura. Solo Presidencia puede editar).*")
                st.dataframe(df_obj.style.format(thousands=","), hide_index=True, use_container_width=True)
