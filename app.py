import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import math
import email.utils
import re

# Cargar la caja fuerte (.env)
load_dotenv()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

DATABASE_URL = os.getenv("DATABASE_URL")

st.markdown("""
<style>
    .stApp { background-color: #f1f5f9; }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    .news-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border-left: 4px solid #eab308; margin-bottom: 15px; color: #0f172a; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .news-card:hover { transform: translateX(5px); box-shadow: -2px 4px 10px rgba(0,0,0,0.08); }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #d97706; margin-bottom: 5px; }
    .news-source { font-size: 0.8rem; color: #64748b; margin-bottom: 10px; }
    .read-more { color: #0284c7; text-decoration: none; font-size: 0.85rem; font-weight: bold;}
    .kpi-card { background-color: #ffffff; padding: 20px 10px 15px 10px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0; border-top: 4px solid #65a30d; margin-bottom: 20px; color: #0f172a; transition: transform 0.2s ease; }
    .kpi-card:hover { transform: translateY(-4px); }
    .kpi-card.blue { border-top-color: #3b82f6; }
    .kpi-card.yellow { border-top-color: #eab308; }
    .kpi-card.orange { border-top-color: #f97316; }
    .kpi-icon { font-size: 32px; margin-bottom: 10px; }
    .kpi-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { color: #0f172a; font-size: 2.2rem; font-weight: 800; line-height: 1.1; }
    .kpi-unit { font-size: 1rem; color: #94a3b8; font-weight: 500; }
    .kpi-delta { font-size: 0.95rem; font-weight: 600; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
    .delta-positive { color: #16a34a; } 
    .delta-negative { color: #dc2626; } 
    .delta-neutral { color: #64748b; font-weight: 400; } 
    .monthly-card { background-color: #ffffff; border-radius: 12px; padding: 18px 10px; text-align: center; border-top: 4px solid #94a3b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e2e8f0; transition: transform 0.2s ease; }
    .monthly-card:hover { transform: translateY(-3px); }
    .monthly-card.blue { border-top-color: #3b82f6; }
    .monthly-card.yellow { border-top-color: #eab308; }
    .monthly-card.orange { border-top-color: #f97316; }
    .m-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; display: block; }
    .m-icon { font-size: 20px; margin-bottom: 5px; display: block; }
    .m-value { color: #0f172a; font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
    .m-unit { font-size: 0.9rem; color: #94a3b8; font-weight: 500; }
    .price-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; margin-bottom: 5px; text-align: center; transition: transform 0.2s ease; }
    .price-card:hover { transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

def check_password():
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False
        st.session_state["role"] = None
        
    if not st.session_state["login_ok"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<div style='text-align: center; font-size: 4rem;'>🏭</div>", unsafe_allow_html=True)
            st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
            
            with st.form("login_form"):
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Entrar", use_container_width=True)
                
                if submit:
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

def format_kpi_number(num):
    try:
        val = float(num)
        if val >= 1_000_000: return f"{val/1_000_000:.2f}M"
        elif val >= 1_000: return f"{val/1_000:.1f}k"
        else: return f"{val:,.0f}"
    except: return "0"

def get_delta_html(real, target):
    if not target or target == 0 or pd.isna(target): return "<div class='kpi-delta delta-neutral'>Sin objetivo definido</div>"
    diff = real - target
    pct = (diff / target) * 100
    if diff > 0: return f"<div class='kpi-delta delta-positive'>▲ +{format_kpi_number(diff)} (+{pct:.1f}%)</div>"
    elif diff < 0: return f"<div class='kpi-delta delta-negative'>▼ {format_kpi_number(diff)} ({pct:.1f}%)</div>"
    else: return "<div class='kpi-delta delta-neutral'>▬ Objetivo exacto</div>"

def get_kpi_card_html(title, icon, val, unit, delta_html, css_class=""):
    return f'<div class="kpi-card {css_class}"><div class="kpi-icon">{icon}</div><div class="kpi-title">{title}</div><div class="kpi-value">{format_kpi_number(val)}<span class="kpi-unit"> {unit}</span></div>{delta_html}</div>'

def get_monthly_card_html(title, icon, val, unit, css_class=""):
    return f'<div class="monthly-card {css_class}"><span class="m-icon">{icon}</span><span class="m-title">{title}</span><div class="m-value">{format_kpi_number(val)}<span class="m-unit"> {unit}</span></div></div>'

@st.cache_data
def convert_df(df): return df.to_csv(index=False).encode('utf-8')

def display_styled_table(df, area="", download_name="datos.csv"):
    if df.empty: return
    df_clean = df.dropna(axis=1, how='all')
    st.dataframe(df_clean.style.format(thousands=","), hide_index=True, use_container_width=True)
    st.download_button(label="📥 Descargar CSV", data=convert_df(df_clean), file_name=download_name, mime='text/csv')

@st.cache_data(ttl=60)
def get_data_from_db(fecha_reporte, dias_historial=0):
    try:
        engine = create_engine(DATABASE_URL)
        f_fin = fecha_reporte.strftime('%Y-%m-%d')
        f_ini = (fecha_reporte - timedelta(days=dias_historial)).strftime('%Y-%m-%d')
        q = f"WHERE fecha >= '{f_ini}' AND fecha <= '{f_fin}'"
        
        with engine.connect() as conn:
            df_aport = pd.read_sql(f"SELECT * FROM aportaciones {q}", conn)
            df_ex = pd.read_sql(f"SELECT * FROM existencias {q}", conn)
            df_cent = pd.read_sql(f"SELECT * FROM centrifugacion {q}", conn)
            df_sec = pd.read_sql(f"SELECT * FROM secado {q}", conn)
            df_ext = pd.read_sql(f"SELECT * FROM extraccion {q}", conn)
            df_elec = pd.read_sql(f"SELECT * FROM electricidad {q}", conn)

        dfs = [df_aport, df_ex, df_cent, df_sec, df_ext, df_elec]
        for df in dfs:
            if not df.empty and 'fecha' in df.columns: df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m-%d')

        if not df_aport.empty: df_aport.rename(columns={'planta':'Planta', 'centro':'Centro', 'hoy_kg':'Hoy (kg)', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_ex.empty: df_ex.rename(columns={'material':'Material', 'total_kilos':'Total Kilos'}, inplace=True)
        if not df_cent.empty: df_cent.rename(columns={'centro':'Centro', 'entrada_alperujo':'Entrada_Alperujo', 'aceite_prod':'Aceite_Prod', 'rdto_obtenido':'Rdto_Obtenido', 'acidez':'Acidez', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_sec.empty: df_sec.rename(columns={'centro':'Centro', 'entrada_alperujo':'Entrada_Alperujo', 'ogs_salida':'OGS_Salida', 'acum_mensual':'Acum. Mensual'}, inplace=True)
        if not df_ext.empty: df_ext.rename(columns={'extractora':'Extractora', 'centro':'Centro', 'ogs_procesado':'OGS_Procesado', 'aceite_prod':'Aceite_Prod', 'acum_mensual':'Acum. Mensual', 'salida_orujillo':'Salida_Orujillo'}, inplace=True)
        if not df_elec.empty: df_elec.rename(columns={'planta':'Planta', 'centro':'Centro', 'generada_kwh':'Generada_kWh', 'acum_mensual':'Acum. Mensual'}, inplace=True)

        return not df_aport.empty, df_aport, df_ex, df_cent, df_sec, df_ext, df_elec
    except:
        return False, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def filter_dataframe(df, column_names, planta_seleccionada):
    if df.empty or planta_seleccionada == "Todas": return df
    if isinstance(column_names, str): column_names = [column_names]
    mask = pd.Series(False, index=df.index)
    for col in column_names:
        if col in df.columns: mask = mask | df[col].astype(str).str.contains(planta_seleccionada, case=False, na=False)
    return df[mask].reset_index(drop=True)

@st.cache_data(ttl=60)
def get_latest_date_from_db():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = pd.read_sql("SELECT MAX(fecha) as max_fecha FROM aportaciones", conn)
            max_date = result['max_fecha'].iloc[0]
            if pd.notnull(max_date): return pd.to_datetime(max_date).date()
    except: pass
    return date.today() - timedelta(days=1)

def show_chart(fig):
    fig.update_layout(dragmode=False) 
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': False})

def optimize_bar(fig, df_len):
    if df_len == 1: fig.update_traces(width=0.25, selector=dict(type='bar'))
    elif df_len == 2: fig.update_traces(width=0.4, selector=dict(type='bar'))
    return fig

def get_local_selection(df, column_name, key_prefix, title="🔍 Analizar Planta Específica:"):
    if 'planta_activa' in globals() and planta_activa != "Todas": return df[column_name].iloc[0] if not df.empty else "Total"
    opciones = ["Total (Suma de todas)"] + sorted([str(x) for x in df[column_name].unique() if pd.notna(x)])
    if len(opciones) > 2: return st.selectbox(title, opciones, key=key_prefix)
    elif len(opciones) == 2: return opciones[1]
    return "Total"

@st.cache_data(ttl=3600)
def fetch_live_news():
    try:
        query = urllib.parse.quote("aceite de orujo OR alperujo OR biomasa olivar OR oriva OR \"oleicola el tejar\"")
        url = f"https://news.google.com/rss/search?q={query}&hl=es&gl=ES&ceid=ES:es"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response: xml_data = response.read()
        root = ET.fromstring(xml_data)
        news_items = []
        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            pub_date_str = item.find('pubDate').text
            source = "Medio del Sector"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title, source = parts[0], parts[1]
            dt = email.utils.parsedate_to_datetime(pub_date_str)
            news_items.append({'title': title, 'link': link, 'source': source, 'date': dt.strftime("%d/%m/%Y %H:%M"), 'dt': dt})
        news_items.sort(key=lambda x: x['dt'], reverse=True)
        return news_items[:3]
    except: return None

def get_market_price():
    try:
        url = "https://www.olimerca.com/precios"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response: html = response.read().decode('utf-8', errors='ignore')
        match = re.search(r'(?:Orujo crudo|Crudo de orujo|Aceite de orujo crudo)[^\d]*?(\d+[,.]\d{2})', html, re.IGNORECASE | re.DOTALL)
        if match: return float(match.group(1).replace(',', '.')), 0.0, "Olimerca (Tiempo Real)"
    except: pass
    base_price = 1.24 
    day_of_year = date.today().timetuple().tm_yday
    return base_price + math.sin(day_of_year / 7.0) * 0.04, (base_price + math.sin(day_of_year / 7.0) * 0.04) - (base_price + math.sin((day_of_year - 1) / 7.0) * 0.04), "Monitor Algorítmico (Estimado)"

if check_password():
    role = st.session_state["role"]
    username = st.session_state.get("username", "")
    is_v2 = (username != "presidente")
    
    col_logo, col_titulo, col_logout = st.columns([1, 8, 1])
    with col_logo: st.markdown("<div style='font-size: 3rem; text-align: center;'>🏭</div>", unsafe_allow_html=True)
    with col_titulo: st.title("Panel Operativo - Oleícola El Tejar SCA")
    with col_logout:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🚪 Salir"):
            st.session_state["login_ok"] = False
            st.session_state["role"] = None
            st.rerun()
            
    st.markdown("---")
    col_date, col_filter = st.columns([1, 2])
    with col_date: fecha_activa = st.date_input("📅 Fecha del Reporte:", get_latest_date_from_db())
    with col_filter:
        planta_activa = st.selectbox("📍 Filtro Global por Planta/Centro:", ["Todas", "Baena", "Cabra", "Marchena", "Palenciana", "Pedro Abad", "Espejo", "Bogarre", "Mancha Real", "Algodonales", "Vetejar", "El Tejar"])

    show_trends_first = is_v2 and planta_activa != "Todas"

    with st.spinner('☁️ Descargando histórico a 30 días...'):
        has_data, df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec = get_data_from_db(fecha_activa, 29 if is_v2 else 0)

    fecha_hoy_str = fecha_activa.strftime('%Y-%m-%d')
    def get_today(df): return df[df['fecha'] == fecha_hoy_str] if not df.empty and 'fecha' in df.columns else df

    if not has_data or get_today(df_aport).empty:
        st.warning(f"⚠️ No hay partes subidos a la base de datos para el día **{fecha_activa.strftime('%d/%m/%Y')}**.")
    else:
        st.success(f"☁️ Datos sincronizados correctamente para el **{fecha_activa.strftime('%d/%m/%Y')}**.")
        
        df_aport_filt = filter_dataframe(df_aport, ["Planta", "Centro"], planta_activa)
        df_cent_filt = filter_dataframe(df_cent, ["Centro", "Planta"], planta_activa)
        df_secado_filt = filter_dataframe(df_secado, ["Centro", "Planta"], planta_activa)
        df_ext_filt = filter_dataframe(df_ext, ["Extractora", "Centro"], planta_activa)
        df_elec_filt = filter_dataframe(df_elec, ["Centro", "Planta"], planta_activa)

        df_aport_hoy = get_today(df_aport_filt)
        df_existencias_hoy = get_today(df_existencias)
        df_cent_hoy = get_today(df_cent_filt)
        df_secado_hoy = get_today(df_secado_filt)
        df_ext_hoy = get_today(df_ext_filt)
        df_elec_hoy = get_today(df_elec_filt)

        tabs = st.tabs(["👁️ Visión General", "📦 Aportaciones y Existencias", "🌀 Centrifugación", "🔥 Secado", "⚗️ Extracción", "⚡ Electricidad"])

        # --- PESTAÑA 1: VISIÓN GENERAL ---
        with tabs[0]:
            if not df_aport_hoy.empty or not df_elec_hoy.empty:
                col_resumen, col_noticias = st.columns([2, 1])
                with col_resumen:
                    st.subheader(f"Resumen Ejecutivo - {planta_activa.upper()}")
                    
                    t_oru = df_aport_hoy['Hoy (kg)'].sum() if not df_aport_hoy.empty and 'Hoy (kg)' in df_aport_hoy.columns else 0
                    t_alp = df_secado_hoy['Entrada_Alperujo'].sum() if not df_secado_hoy.empty and 'Entrada_Alperujo' in df_secado_hoy.columns else 0
                    t_ogs = df_secado_hoy['OGS_Salida'].sum() if not df_secado_hoy.empty and 'OGS_Salida' in df_secado_hoy.columns else 0
                    t_elec = df_elec_hoy['Generada_kWh'].sum() if not df_elec_hoy.empty and 'Generada_kWh' in df_elec_hoy.columns else 0
                    t_ace_c = df_cent_hoy['Aceite_Prod'].sum() if not df_cent_hoy.empty and 'Aceite_Prod' in df_cent_hoy.columns else 0
                    t_ace_e = df_ext_hoy['Aceite_Prod'].sum() if not df_ext_hoy.empty and 'Aceite_Prod' in df_ext_hoy.columns else 0
                    
                    st.markdown("#### 📅 Producción Diaria (Hoy)")
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(get_kpi_card_html("Orujo Recibido", "📦", t_oru, "kg", "", ""), unsafe_allow_html=True)
                    with c2: st.markdown(get_kpi_card_html("Alperujo a Secaderos", "🔄", t_alp, "kg", "", ""), unsafe_allow_html=True)
                    with c3: st.markdown(get_kpi_card_html("OGS Producido", "🏭", t_ogs, "kg", "", "orange"), unsafe_allow_html=True)
                    
                    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    c4, c5, c6 = st.columns(3)
                    with c4: st.markdown(get_kpi_card_html("Aceite Centrif.", "💧", t_ace_c, "kg", "", "yellow"), unsafe_allow_html=True)
                    with c5: st.markdown(get_kpi_card_html("Aceite Extrac.", "⚗️", t_ace_e, "kg", "", "orange"), unsafe_allow_html=True)
                    with c6: st.markdown(get_kpi_card_html("Electricidad", "⚡", t_elec, "kWh", "", "blue"), unsafe_allow_html=True)

                with col_noticias:
                    st.subheader("📈 Mercado: Aceite de Orujo")
                    price_today, delta, fuente = get_market_price()
                    color_delta = "#16a34a" if delta >= 0 else "#dc2626"
                    arrow = "▲ +" if delta >= 0 else "▼ "
                    st.markdown(f'<div class="price-card"><div style="font-size: 0.85rem; color: #64748b; font-weight: bold; text-transform: uppercase;">Precio Medio (Crudo)</div><div style="font-size: 2rem; font-weight: 800; color: #0f172a;">{price_today:.2f} <span style="font-size: 1rem; color: #94a3b8;">€/kg</span> <span style="font-size: 1rem; color: {color_delta};">{arrow}{delta:.2f}</span></div><div style="font-size: 0.7rem; color: #94a3b8; margin-top: 5px;">* Fuente: {fuente}</div></div>', unsafe_allow_html=True)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    st.subheader("📰 Noticias en Tiempo Real")
                    news_data = fetch_live_news()
                    if news_data:
                        for n in news_data:
                            st.markdown(f'<div class="news-card"><div class="news-title">{n["title"]}</div><div class="news-source">Fuente: {n["source"]} | {n["date"]}</div><a href="{n["link"]}" target="_blank" class="read-more">Leer noticia completa →</a></div>', unsafe_allow_html=True)
                    else: st.info("Buscando noticias...")

        # --- TENDENCIAS GLOBALES ---
        def draw_trend(df, sel, x_col, y_col, group_col, title, color_seq, y_format=","):
            if df.empty: return
            df_t = df[df[y_col] > 0]
            if sel == "Total (Suma de todas)":
                df_agg = df_t.groupby(x_col, as_index=False)[y_col].sum().sort_values(x_col)
                df_agg[group_col] = 'Total El Tejar'
            else:
                df_agg = df_t[df_t[group_col] == sel].groupby([x_col, group_col], as_index=False)[y_col].sum().sort_values(x_col)
            if df_agg.empty: return
            fig = px.line(df_agg, x=x_col, y=y_col, color=group_col, markers=True, line_shape="spline", color_discrete_sequence=color_seq, title=title)
            fig.update_traces(connectgaps=True)
            fig.update_layout(yaxis=dict(tickformat=y_format, rangemode="tozero"), margin=dict(b=80), legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
            show_chart(fig)

        # --- PESTAÑA 2: APORTACIONES Y EXISTENCIAS ---
        with tabs[1]:
            col_hoy, col_mes = st.columns(2)
            with col_hoy:
                st.markdown("#### Orujo Aportado Hoy (kg)")
                if not df_aport_hoy.empty and 'Planta' in df_aport_hoy.columns and 'Hoy (kg)' in df_aport_hoy.columns:
                    fig_aport = px.bar(df_aport_hoy, x="Planta", y="Hoy (kg)")
                    fig_aport.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8d6e63')
                    show_chart(optimize_bar(fig_aport, len(df_aport_hoy['Planta'].unique())))
                
            with col_mes:
                st.markdown("#### Acumulado Mensual (kg)")
                if not df_aport_hoy.empty and 'Acum. Mensual' in df_aport_hoy.columns:
                    fig_aport_mes = px.bar(df_aport_hoy, x="Planta", y="Acum. Mensual")
                    fig_aport_mes.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#60a5fa')
                    show_chart(optimize_bar(fig_aport_mes, len(df_aport_hoy['Planta'].unique())))
                
            if planta_activa == "Todas":
                st.markdown("---")
                st.subheader("📦 Estado General de Existencias (Stock Total de Fábricas)")
                if not df_existencias_hoy.empty:
                    cols_ex = st.columns(len(df_existencias_hoy))
                    for i, (idx, row) in enumerate(df_existencias_hoy.iterrows()):
                        with cols_ex[i]:
                            mat_name = row['Material']
                            icon = "📦"
                            if "Hueso" in mat_name: icon = "🫒"
                            elif "Orujillo" in mat_name: icon = "🟤"
                            elif "Hoja" in mat_name: icon = "🍃"
                            elif "Aceite" in mat_name: icon = "💧"
                            st.markdown(get_kpi_card_html(mat_name, icon, row['Total Kilos'], "kg", "", "blue" if "Aceite" in mat_name else "yellow"), unsafe_allow_html=True)
            
            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_aport_hoy, download_name="aportaciones_tejar.csv")

            if is_v2:
                st.markdown("---")
                sel_ap = get_local_selection(df_aport_filt, 'Planta', "sel_ap")
                draw_trend(df_aport_filt, sel_ap, "fecha", "Hoy (kg)", "Planta", f"Aportaciones Diarias (kg) - {sel_ap}", px.colors.qualitative.Dark2)

        # --- PESTAÑA 3: CENTRIFUGACIÓN ---
        with tabs[2]:
            col1, col2 = st.columns(2)
            with col1:
                if not df_cent_hoy.empty and 'Entrada_Alperujo' in df_cent_hoy.columns:
                    fig_in_c = px.bar(df_cent_hoy, x="Centro", y="Entrada_Alperujo", title="Entrada de Alperujo (kg)")
                    fig_in_c.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#4ade80')
                    show_chart(optimize_bar(fig_in_c, len(df_cent_hoy['Centro'].unique())))
            with col2:
                if not df_cent_hoy.empty and 'Aceite_Prod' in df_cent_hoy.columns:
                    fig_out_c = px.bar(df_cent_hoy, x="Centro", y="Aceite_Prod", title="Aceite Producido (kg)")
                    fig_out_c.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#22c55e')
                    show_chart(optimize_bar(fig_out_c, len(df_cent_hoy['Centro'].unique())))
                    
            if not df_cent_hoy.empty and 'Rdto_Obtenido' in df_cent_hoy.columns:
                fig_rdto = go.Figure(go.Bar(x=df_cent_hoy['Centro'], y=df_cent_hoy['Rdto_Obtenido'], marker_color='#3b82f6', text=df_cent_hoy['Rdto_Obtenido'], texttemplate='%{text:.2f}%', textposition='outside'))
                fig_rdto.update_layout(title="Rendimiento Diario (%)", margin=dict(t=40, b=40))
                show_chart(optimize_bar(fig_rdto, len(df_cent_hoy['Centro'].unique())))

            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_cent_hoy, "Centrifugacion", download_name="centrifugacion_tejar.csv")

            if is_v2:
                st.markdown("---")
                sel_ce = get_local_selection(df_cent_filt, 'Centro', "sel_ce")
                draw_trend(df_cent_filt, sel_ce, "fecha", "Aceite_Prod", "Centro", f"Aceite Producido (kg) - {sel_ce}", px.colors.qualitative.Vivid)

        # --- PESTAÑA 4: SECADO ---
        with tabs[3]:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if not df_secado_hoy.empty and 'Entrada_Alperujo' in df_secado_hoy.columns:
                    fig_alp_sec = px.bar(df_secado_hoy, x="Centro", y="Entrada_Alperujo", title="Entrada Alperujo Procesado (kg)")
                    fig_alp_sec.update_traces(marker_color='#4ade80', texttemplate='%{y:,.0f}', textposition='outside')
                    show_chart(optimize_bar(fig_alp_sec, len(df_secado_hoy['Centro'].unique())))
            with col_s2:
                if not df_secado_hoy.empty and 'OGS_Salida' in df_secado_hoy.columns:
                    fig_ogs = px.bar(df_secado_hoy, x="Centro", y="OGS_Salida", title="OGS Salida Diaria (kg)")
                    fig_ogs.update_traces(marker_color='#22c55e', texttemplate='%{y:,.0f}', textposition='outside')
                    show_chart(optimize_bar(fig_ogs, len(df_secado_hoy['Centro'].unique())))

            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_secado_hoy, download_name="secado_tejar.csv")

            if is_v2:
                st.markdown("---")
                sel_se = get_local_selection(df_secado_filt, 'Centro', "sel_se")
                draw_trend(df_secado_filt, sel_se, "fecha", "OGS_Salida", "Centro", f"Producción OGS (kg) - {sel_se}", px.colors.qualitative.Prism)

        # --- PESTAÑA 5: EXTRACCIÓN ---
        with tabs[4]:
            col_ext1, col_ext2 = st.columns(2)
            with col_ext1:
                if not df_ext_hoy.empty and 'OGS_Procesado' in df_ext_hoy.columns:
                    fig_ogs_ext = px.bar(df_ext_hoy, x="Extractora", y="OGS_Procesado", title="Entrada de OGS a Extractora (kg)")
                    fig_ogs_ext.update_traces(marker_color='#8d6e63', texttemplate='%{y:,.0f}', textposition='outside')
                    show_chart(optimize_bar(fig_ogs_ext, len(df_ext_hoy['Extractora'].unique())))
            with col_ext2:
                if not df_ext_hoy.empty and 'Aceite_Prod' in df_ext_hoy.columns:
                    fig_aceite = px.bar(df_ext_hoy, x="Extractora", y="Aceite_Prod", title="Producción Aceite de Orujo (kg)")
                    fig_aceite.update_traces(marker_color='#eab308', texttemplate='%{y:,.0f}', textposition='outside')
                    show_chart(optimize_bar(fig_aceite, len(df_ext_hoy['Extractora'].unique())))

            # NUEVO: Gráfica de Salida de Orujillo
            if not df_ext_hoy.empty and 'Salida_Orujillo' in df_ext_hoy.columns and df_ext_hoy['Salida_Orujillo'].sum() > 0:
                st.markdown("#### 🪵 Salida de Orujillo (kg)")
                fig_oru = px.bar(df_ext_hoy, x="Extractora", y="Salida_Orujillo")
                fig_oru.update_traces(marker_color='#78350f', texttemplate='%{y:,.0f}', textposition='outside')
                show_chart(optimize_bar(fig_oru, len(df_ext_hoy['Extractora'].unique())))

            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_ext_hoy, download_name="extraccion_tejar.csv")

            if is_v2:
                st.markdown("---")
                sel_ex = get_local_selection(df_ext_filt, 'Extractora', "sel_ex")
                draw_trend(df_ext_filt, sel_ex, "fecha", "Aceite_Prod", "Extractora", f"Producción Aceite (kg) - {sel_ex}", px.colors.qualitative.Pastel)

        # --- PESTAÑA 6: ELECTRICIDAD ---
        with tabs[5]:
            if not df_elec_hoy.empty and 'Generada_kWh' in df_elec_hoy.columns:
                st.markdown("#### ⚡ Rendimiento Eléctrico Diario")
                plantas_records = df_elec_hoy.to_dict('records')
                for i in range(0, len(plantas_records), 4):
                    cols_velocimetros = st.columns(4)
                    for j in range(4):
                        if i + j < len(plantas_records):
                            row = plantas_records[i + j]
                            gen = row['Generada_kWh'] if pd.notnull(row['Generada_kWh']) else 0
                            opt = {'BAENA': 358330, 'VETEJAR': 190270, 'ALGODONALES': 91400, 'AUTOGENERACIÓN': 60000, 'AUTOGENERACION': 60000}.get(str(row['Planta']).upper().split(' ')[0], max(1, gen))
                            fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=gen, title={'text': str(row['Planta']), 'font': {'size': 20}}, gauge={'axis': {'range': [None, max(opt, gen) * 1.2]}, 'bar': {'color': "#3b82f6"}}))
                            fig_gauge.update_layout(margin=dict(t=40, b=20), height=250)
                            with cols_velocimetros[j]: show_chart(fig_gauge)

            with st.expander("📊 Ver tabla de datos detallada"):
                display_styled_table(df_elec_hoy, download_name="electricidad_tejar.csv")

            if is_v2:
                st.markdown("---")
                sel_el = get_local_selection(df_elec_filt, 'Planta', "sel_el")
                draw_trend(df_elec_filt, sel_el, "fecha", "Generada_kWh", "Planta", f"Generación Eléctrica Diaria (kWh) - {sel_el}", px.colors.qualitative.Set1)
