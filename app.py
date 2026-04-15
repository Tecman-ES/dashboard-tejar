import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import io
import csv
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

# --- ESTILOS PERSONALIZADOS (CSS) ---
st.markdown("""
<style>
    /* Estilos para Noticias */
    .news-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #eab308;
        margin-bottom: 15px;
        color: #f8fafc;
    }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #fbbf24; margin-bottom: 5px; }
    .news-source { font-size: 0.8rem; color: #94a3b8; margin-bottom: 10px; }
    .news-snippet { font-size: 0.9rem; line-height: 1.4; }
    
    /* Estilos para Tablas */
    .stDataFrame [data-testid="stTable"] { font-variant-numeric: tabular-nums; }
    
    /* NUEVO: Estilos para Tarjetas KPI (Visión General) */
    .kpi-card {
        background-color: #1e293b;
        padding: 20px 10px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border-top: 4px solid #65a30d; /* Verde por defecto */
        margin-bottom: 20px;
    }
    .kpi-card.blue { border-top-color: #3b82f6; }
    .kpi-card.yellow { border-top-color: #eab308; }
    .kpi-card.orange { border-top-color: #f97316; }
    
    .kpi-icon { font-size: 28px; margin-bottom: 10px; }
    .kpi-title { color: #94a3b8; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
    .kpi-value { color: #f8fafc; font-size: 2.2rem; font-weight: 800; line-height: 1.1; }
    .kpi-unit { font-size: 1rem; color: #cbd5e1; font-weight: 500; }
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
            st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
            usuario = st.text_input("Usuario (oficina / presidente)")
            password = st.text_input("Contraseña", type="password")
            if st.button("Entrar", use_container_width=True):
                if usuario == "presidente" and password == "Tejar2026":
                    st.session_state["login_ok"] = True
                    st.session_state["role"] = "presidente"
                    st.rerun()
                elif usuario == "oficina" and password == "Tejar2026":
                    st.session_state["login_ok"] = True
                    st.session_state["role"] = "oficina"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        return False
    return True

# --- FUNCIONES DE MEMORIA (EXCEL) ---
def save_file_to_disk(uploaded_file):
    with open("ultimo_parte.dat", "wb") as f:
        f.write(uploaded_file.getvalue())
    with open("ultimo_parte_name.txt", "w") as f:
        f.write(uploaded_file.name)

def load_file_from_disk():
    if os.path.exists("ultimo_parte.dat") and os.path.exists("ultimo_parte_name.txt"):
        with open("ultimo_parte_name.txt", "r") as f:
            name = f.read().strip()
        with open("ultimo_parte.dat", "rb") as f:
            content = f.read()
        file_obj = io.BytesIO(content)
        file_obj.name = name
        return file_obj
    return None

def save_date_to_disk(selected_date):
    with open("ultima_fecha.txt", "w") as f:
        f.write(selected_date.isoformat())

def load_date_from_disk():
    if os.path.exists("ultima_fecha.txt"):
        try:
            with open("ultima_fecha.txt", "r") as f:
                return date.fromisoformat(f.read().strip())
        except: pass
    return date(2026, 4, 14)

# --- SISTEMA DE OBJETIVOS ---
def load_objectives():
    if os.path.exists("objetivos_tejar.csv"):
        return pd.read_csv("objetivos_tejar.csv")
    else:
        return pd.DataFrame({
            "Area": ["Centrifugacion", "Centrifugacion", "Centrifugacion", "Secado", "Secado", "Secado", "Secado", "Secado", "Extraccion", "Extraccion", "Electricidad", "Electricidad", "Electricidad"],
            "Planta": ["Marchena", "Cabra", "Baena", "Palenciana", "Marchena", "Cabra", "Baena", "Espejo", "El Tejar", "Baena", "Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW"],
            "Metrica": ["Aceite (kg)", "Aceite (kg)", "Aceite (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "Aceite (kg)", "Aceite (kg)", "Energia (kWh)", "Energia (kWh)", "Energia (kWh)"],
            "Objetivo_Diario": [5251, 442, 1906, 148900, 272720, 288560, 313160, 181020, 43400, 18900, 223608, 416169, 105737]
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

# --- FUNCIONES DE LIMPIEZA, FORMATO Y DESCARGA ---
def format_kpi_number(num):
    """NUEVO: Acorta números gigantes a M (Millones) o k (Miles) para que quepan perfectos"""
    try:
        val = float(num)
        if val >= 1_000_000:
            return f"{val/1_000_000:.2f}M"
        elif val >= 1_000:
            return f"{val/1_000:.1f}k"
        else:
            return f"{val:,.0f}"
    except:
        return "0"

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

def display_styled_table(df, area="", download_name="datos.csv"):
    if df.empty: return
    df_clean = df.dropna(axis=1, how='all')
    
    if area == "Centrifugacion":
        def highlight(row):
            styles = [''] * len(row)
            if 'Acidez' in df.columns:
                val = row['Acidez']
                if pd.notnull(val) and isinstance(val, (int, float)) and val > 3:
                    styles[df.columns.get_loc('Acidez')] = 'background-color: rgba(239, 68, 68, 0.4); color: white;'
            return styles
        st.dataframe(df_clean.style.apply(highlight, axis=1).format(thousands=","), hide_index=True, use_container_width=True)
    else:
        st.dataframe(df_clean.style.format(thousands=","), hide_index=True, use_container_width=True)
        
    csv_data = convert_df(df_clean)
    st.download_button(label="📥 Descargar a CSV", data=csv_data, file_name=download_name, mime='text/csv')

def fix_number(x):
    if pd.isna(x): return x
    if isinstance(x, str):
        x = x.strip()
        test_str = x.replace('-', '').replace(',', '').replace('.', '')
        if test_str.isdigit() and len(test_str) > 0:
            if x.count(',') > 1: x = x.replace(',', '')
            elif x.count('.') > 1: x = x.replace('.', '')
            elif ',' in x and '.' in x:
                if x.rfind(',') > x.rfind('.'): x = x.replace('.', '').replace(',', '.')
                else: x = x.replace(',', '')
            elif ',' in x: x = x.replace(',', '.')
    return x

def extract_table(df_raw, marker):
    try:
        col0 = df_raw.iloc[:, 0].astype(str).str.strip()
        idx = df_raw[col0 == marker].index
        if len(idx) == 0: return pd.DataFrame()
        
        start_idx = idx[0]
        end_idx = len(df_raw)
        for i in range(start_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            if val.startswith('#') and val != marker:
                end_idx = i
                break
                
        df_sub = df_raw.iloc[start_idx+1:end_idx].copy()
        df_sub = df_sub.replace(r'^\s*$', pd.NA, regex=True).dropna(how='all').reset_index(drop=True)
        if df_sub.empty: return pd.DataFrame()
        
        headers = df_sub.iloc[0].fillna('').astype(str).str.strip()
        df_sub.columns = headers
        df_sub = df_sub.iloc[1:].reset_index(drop=True)
        
        valid_cols = [c for c in df_sub.columns if c != '']
        if not valid_cols: return pd.DataFrame()
        df_sub = df_sub[valid_cols]
        
        for col in df_sub.columns:
            df_sub[col] = df_sub[col].apply(fix_number)
            s_num = pd.to_numeric(df_sub[col], errors='coerce')
            if s_num.isna().sum() <= df_sub[col].isna().sum():
                df_sub[col] = s_num
                
        return df_sub
    except:
        return pd.DataFrame()

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            if uploaded_file.name.endswith('.csv'):
                content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                sep = ','
                first_line = content.split('\n')[0] if content else ''
                if first_line.count(';') > first_line.count(','): sep = ';'
                reader = csv.reader(io.StringIO(content), delimiter=sep)
                df_raw = pd.DataFrame(list(reader)).fillna('')
            else:
                df_raw = pd.read_excel(uploaded_file, header=None, dtype=str).fillna('')
            
            df_aport = extract_table(df_raw, "# APORTACIONES")
            df_existencias = extract_table(df_raw, "# EXISTENCIAS")
            df_cent = extract_table(df_raw, "# CENTRIFUGACION")
            df_secado = extract_table(df_raw, "# SECADO")
            df_ext = extract_table(df_raw, "# EXTRACCION")
            df_elec = extract_table(df_raw, "# ELECTRICIDAD")
            
            return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec
        except: pass
            
    df_aport = pd.DataFrame({"Planta": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"], "Hoy (kg)": [682620, 76600, 882900, 107840, 333060, 228700, 54160, 64780], "Acum. Mensual": [10362240, 0, 9152660, 173220, 3579480, 2918540, 0, 2281940]})
    df_existencias = pd.DataFrame({"Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"], "Total Kilos": [27694950, 17150820, 57655131]})
    df_cent = pd.DataFrame({"Centro": ["Marchena", "Cabra", "Baena"], "Entrada_Alperujo": [461201, 67426, 631151], "Aceite_Prod": [1870, 632, 771], "Rdto_Obtenido": [0.41, 0.94, 0.12], "Acidez": [2.92, 11.15, 7.81]})
    df_secado = pd.DataFrame({"Centro": ["Palenciana", "Marchena", "Cabra", "Baena", "Espejo"], "Entrada_Alperujo": [444668, 904664, 595175, 457958, 157546], "OGS_Salida": [134400, 221140, 161380, 110000, 22298]})
    df_ext = pd.DataFrame({"Extractora": ["El Tejar", "Baena"], "OGS_Procesado": [570400, 110000], "Salida_Orujillo": [443740, 101700], "Aceite_Prod": [31800, 8300]})
    df_elec = pd.DataFrame({"Planta": ["Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW"], "Generada_kWh": [226344, 450634, 119229]})
    return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec

def filter_dataframe(df, column_name, planta_seleccionada):
    if df.empty or planta_seleccionada == "Todas" or column_name not in df.columns:
        return df
    return df[df[column_name].astype(str).str.contains(planta_seleccionada, case=False, na=False)].reset_index(drop=True)

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    role = st.session_state["role"]
    
    col_titulo, col_logout = st.columns([10, 1])
    with col_titulo:
        st.title("📊 Panel Operativo - Oleícola El Tejar SCA")
    with col_logout:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🚪 Salir"):
            st.session_state["login_ok"] = False
            st.session_state["role"] = None
            st.rerun()
    
    if role == "oficina":
        st.info("👋 **Modo Oficina:** Selecciona la fecha y sube el parte diario.")
        with st.container():
            col_fecha, col_archivo = st.columns([1, 2])
            with col_fecha:
                fecha_seleccionada = st.date_input("📅 Fecha del Parte", load_date_from_disk())
                if fecha_seleccionada != load_date_from_disk():
                    save_date_to_disk(fecha_seleccionada)
            with col_archivo:
                archivo_subido = st.file_uploader("📂 Sube tu Archivo (.csv, .xlsx)", type=["xlsx", "xls", "csv"], label_visibility="visible")
                if archivo_subido is not None:
                    save_file_to_disk(archivo_subido)
                    st.success("✅ Archivo guardado correctamente en la base de datos.")
    
    fecha_reporte = load_date_from_disk()
    archivo_compartido = load_file_from_disk()
    if archivo_compartido is None and role == "presidente":
        st.warning("⚠️ Aún no se ha subido el parte diario de hoy. Mostrando datos de prueba.")
        
    df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec = load_data(archivo_compartido)
    df_obj = load_objectives()
    
    df_cent, df_secado, df_ext, df_elec = apply_objectives(df_cent, df_secado, df_ext, df_elec, df_obj)
    
    st.markdown("---")
    col_date, col_filter = st.columns([1, 2])
    with col_date:
        st.markdown(f"**Fecha de reporte activo:** {fecha_reporte.strftime('%d de %B de %Y')}")
    with col_filter:
        plantas_disponibles = ["Todas", "Baena", "Cabra", "Marchena", "Palenciana", "Pedro Abad", "Espejo", "Bogarre", "Mancha Real", "Algodonales", "Vetejar", "El Tejar"]
        planta_activa = st.selectbox("📍 Filtro Global por Planta/Centro:", plantas_disponibles)

    df_aport = filter_dataframe(df_aport, "Planta", planta_activa)
    df_cent = filter_dataframe(df_cent, "Centro", planta_activa)
    df_secado = filter_dataframe(df_secado, "Centro", planta_activa)
    df_ext = filter_dataframe(df_ext, "Extractora", planta_activa)
    df_elec = filter_dataframe(df_elec, "Planta", planta_activa)

    tabs = st.tabs(["👁️ Visión General", "📦 Aportaciones", "🌀 Centrifugación", "🔥 Secado", "🗜️ Extracción", "⚡ Electricidad", "🎯 Mis Objetivos"])

    # --- PESTAÑA 1: VISIÓN GENERAL (REDISEÑADA) ---
    with tabs[0]:
        col_resumen, col_noticias = st.columns([2, 1])
        with col_resumen:
            st.subheader(f"Resumen Ejecutivo - {planta_activa.upper()}")
            
            # Cálculos de totales
            total_orujo = df_aport['Hoy (kg)'].sum() if not df_aport.empty and 'Hoy (kg)' in df_aport.columns else 0
            total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 0
            total_aceite_cent = df_cent['Aceite_Prod'].sum() if not df_cent.empty and 'Aceite_Prod' in df_cent.columns else 0
            total_aceite_ext = df_ext['Aceite_Prod'].sum() if not df_ext.empty and 'Aceite_Prod' in df_ext.columns else 0
            
            # NUEVO: Tarjetas KPI con CSS (Sin puntos suspensivos y super visuales)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-icon">📦</div>
                    <div class="kpi-title">Orujo Recibido</div>
                    <div class="kpi-value">{format_kpi_number(total_orujo)}<span class="kpi-unit"> kg</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="kpi-card blue">
                    <div class="kpi-icon">⚡</div>
                    <div class="kpi-title">Electricidad</div>
                    <div class="kpi-value">{format_kpi_number(total_elec)}<span class="kpi-unit"> kWh</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="kpi-card yellow">
                    <div class="kpi-icon">💧</div>
                    <div class="kpi-title">Aceite Centrif.</div>
                    <div class="kpi-value">{format_kpi_number(total_aceite_cent)}<span class="kpi-unit"> kg</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
                <div class="kpi-card orange">
                    <div class="kpi-icon">🗜️</div>
                    <div class="kpi-title">Aceite Extrac.</div>
                    <div class="kpi-value">{format_kpi_number(total_aceite_ext)}<span class="kpi-unit"> kg</span></div>
                </div>
                """, unsafe_allow_html=True)
            
            st.write("<br>", unsafe_allow_html=True)
            st.write("### 🤖 Análisis Operativo IA")
            
            alertas = []
            if not df_cent.empty and 'Acidez' in df_cent.columns:
                for _, row in df_cent.iterrows():
                    val_acidez = row['Acidez']
                    if pd.notnull(val_acidez) and isinstance(val_acidez, (int, float)) and val_acidez > 3:
                        alertas.append(f"⚠️ **Centrifugación {row.get('Centro', '')}:** Acidez crítica detectada ({val_acidez}%)")
            
            if not df_elec.empty and 'Generada_kWh' in df_elec.columns and 'Optimo_kWh' in df_elec.columns:
                for _, row in df_elec.iterrows():
                    val_gen, val_opt = row['Generada_kWh'], row['Optimo_kWh']
                    if pd.notnull(val_gen) and pd.notnull(val_opt) and val_gen > val_opt:
                        alertas.append(f"✅ **Electricidad {row.get('Planta', '')}:** Rendimiento supera el objetivo estratégico.")

            if not alertas:
                st.success(f"✅ **Operaciones Normales en {planta_activa}:** Todos los parámetros se encuentran dentro de los límites esperados hoy.")
            else:
                for a in alertas:
                    if "⚠️" in a: st.error(a)
                    else: st.success(a)

        with col_noticias:
            st.subheader("📰 Actualidad del Sector")
            st.markdown("""
            <div class="news-card">
                <div class="news-title">El precio del AOVE se estabiliza en origen</div>
                <div class="news-source">Fuente: OleoMerca | 14 Abr 2026</div>
                <div class="news-snippet">Las operaciones en picual de alta calidad se cierran en torno a los 4,20€/kg, marcando un freno a las caídas de las últimas tres semanas...</div>
            </div>
            
            <div class="news-card">
                <div class="news-title">Nuevo marco normativo para la cogeneración</div>
                <div class="news-source">Fuente: Revista Alcuza | 13 Abr 2026</div>
                <div class="news-snippet">El Ministerio de Transición Ecológica ha publicado el borrador que bonificará a las plantas extractoras que demuestren una alta eficiencia...</div>
            </div>
            """, unsafe_allow_html=True)

    # --- PESTAÑA 2: APORTACIONES ---
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
            
        with st.expander("📊 Ver tabla de datos detallada (Aportaciones)"):
            display_styled_table(df_aport, download_name="aportaciones_tejar.csv")
            
        if planta_activa == "Todas":
            with st.expander("📊 Ver tabla de datos detallada (Existencias)"):
                display_styled_table(df_existencias, download_name="existencias_tejar.csv")

    # --- PESTAÑA 3: CENTRIFUGACIÓN ---
    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Entrada de Alperujo (kg)")
            if not df_cent.empty and 'Centro' in df_cent.columns and 'Entrada_Alperujo' in df_cent.columns:
                fig_entrada_cent = px.bar(df_cent, x="Centro", y="Entrada_Alperujo")
                fig_entrada_cent.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#4ade80')
                fig_entrada_cent.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_entrada_cent, use_container_width=True)
            else: st.info("Faltan datos de Entrada de Alperujo.")
            
        with col2:
            st.subheader("Aceite Producido vs Óptimo Industrial (kg)")
            if not df_cent.empty and 'Centro' in df_cent.columns and 'Aceite_Prod' in df_cent.columns:
                fig_cent_comp = go.Figure()
                fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Aceite_Prod'], name='Producido', marker_color='#fbbf24', text=df_cent['Aceite_Prod'], texttemplate='%{text:,.0f}'))
                if 'Optimo' in df_cent.columns:
                    fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Optimo'], name='Óptimo', marker_color='#94a3b8', text=df_cent['Optimo'], texttemplate='%{text:,.0f}'))
                fig_cent_comp.update_layout(barmode='group', yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_cent_comp, use_container_width=True)
            else: st.info("Faltan datos de Aceite Producido.")
        
        with st.expander("📊 Ver tabla de datos detallada (Semaforización Activa)"):
            display_styled_table(df_cent, "Centrifugacion", download_name="centrifugacion_tejar.csv")

    # --- PESTAÑA 4: SECADO ---
    with tabs[3]:
        st.subheader("Orujo Graso Seco (OGS) - Salida vs Objetivo (kg)")
        if not df_secado.empty and 'Centro' in df_secado.columns and 'OGS_Salida' in df_secado.columns:
            fig_ogs = px.bar(df_secado, x="Centro", y=["OGS_Salida", "Obj_OGS"] if 'Obj_OGS' in df_secado.columns else "OGS_Salida", barmode="group", color_discrete_sequence=['#d97706', '#fcd34d'])
            fig_ogs.update_layout(yaxis=dict(tickformat=","))
            st.plotly_chart(fig_ogs, use_container_width=True)
        else: st.info(f"Sin datos de Secado para: {planta_activa}")
    
        total_ogs = df_secado['OGS_Salida'].sum() if not df_secado.empty and 'OGS_Salida' in df_secado.columns else 0
        st.metric("Total Secado Generado", f"{total_ogs:,.0f} kg")
        
        with st.expander("📊 Ver tabla de datos detallada"):
            display_styled_table(df_secado, download_name="secado_tejar.csv")

    # --- PESTAÑA 5: EXTRACCIÓN ---
    with tabs[4]:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.subheader("Balance de Masas: OGS vs Orujillo (kg)")
            if not df_ext.empty and 'Extractora' in df_ext.columns and 'OGS_Procesado' in df_ext.columns:
                fig_bal = px.bar(df_ext, x="Extractora", y=["OGS_Procesado", "Salida_Orujillo"] if 'Salida_Orujillo' in df_ext.columns else "OGS_Procesado", barmode="group", color_discrete_sequence=['#84cc16', '#4d7c0f'])
                fig_bal.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_bal, use_container_width=True)
            else: st.info(f"Sin datos de balance para: {planta_activa}")
            
        with col_der:
            st.subheader("Producción de Aceite vs Objetivo (kg)")
            if not df_ext.empty and 'Aceite_Prod' in df_ext.columns:
                fig_aceite = px.bar(df_ext, x="Extractora", y=["Aceite_Prod", "Obj_Aceite"] if 'Obj_Aceite' in df_ext.columns else "Aceite_Prod", barmode="group", color_discrete_sequence=['#eab308', '#fef08a'])
                fig_aceite.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_aceite, use_container_width=True)
                
        with st.expander("📊 Ver tabla de datos detallada"):
            display_styled_table(df_ext, download_name="extraccion_tejar.csv")

    # --- PESTAÑA 6: ELECTRICIDAD ---
    with tabs[5]:
        st.subheader("Rendimiento Eléctrico Diario")
        
        if not df_elec.empty and 'Planta' in df_elec.columns and 'Generada_kWh' in df_elec.columns and 'Optimo_kWh' in df_elec.columns:
            st.write("*(Los gráficos de bala muestran la producción en azul y tu objetivo como una línea blanca vertical)*")
            
            for i, row in df_elec.iterrows():
                gen = row['Generada_kWh'] if pd.notnull(row['Generada_kWh']) else 0
                opt = row['Optimo_kWh'] if pd.notnull(row['Optimo_kWh']) else 1 
                
                fig_bullet = go.Figure(go.Indicator(
                    mode = "number+gauge+delta",
                    value = gen,
                    domain = {'x': [0.25, 1], 'y': [0.1, 0.9]},
                    title = {'text': str(row['Planta']), 'font': {'size': 18, 'color': '#f8fafc'}},
                    delta = {'reference': opt, 'position': "top", 'increasing': {'color': "#4ade80"}, 'decreasing': {'color': "#ef4444"}},
                    number = {'font': {'size': 26, 'color': '#f8fafc'}, 'valueformat': ",.0f"},
                    gauge = {
                        'shape': "bullet",
                        'axis': {'range': [None, max(opt, gen) * 1.2], 'tickcolor': "white", 'tickfont': {'color': 'white'}},
                        'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': opt},
                        'bar': {'color': "#3b82f6"},
                        'bgcolor': "rgba(0,0,0,0)",
                        'steps': [
                            {'range': [0, opt*0.8], 'color': '#451a1a'},      
                            {'range': [opt*0.8, opt], 'color': '#422006'},    
                            {'range': [opt, max(opt, gen)*1.2], 'color': '#14532d'} 
                        ]
                    }
                ))
                fig_bullet.update_layout(margin=dict(t=30, b=20, l=10, r=30), height=140, paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
                st.plotly_chart(fig_bullet, use_container_width=True)
                
        else: st.info(f"Faltan datos eléctricos para calcular rendimientos de: {planta_activa}")
        
        st.metric("Total Generado Hoy", f"{total_elec:,.0f} kWh")
        
        with st.expander("📊 Ver tabla de datos detallada"):
            display_styled_table(df_elec, download_name="electricidad_tejar.csv")

    # --- PESTAÑA 7: CONFIGURACIÓN DE OBJETIVOS ---
    with tabs[6]:
        st.subheader("🎯 Configuración Estratégica de Objetivos")
        st.info("Estos son los objetivos que se inyectan automáticamente en los gráficos y velocímetros.")
        
        if role == "presidente":
            st.write("Haz doble clic en la columna **'Objetivo_Diario'** para modificarlos y pulsa en Guardar.")
            edited_obj = st.data_editor(df_obj, num_rows="dynamic", use_container_width=True, hide_index=True)
            
            if st.button("💾 Guardar y Aplicar Nuevos Objetivos", type="primary"):
                save_objectives(edited_obj)
                st.success("¡Objetivos actualizados! Recargando gráficas...")
                st.rerun()
        else:
            st.write("*(Modo solo lectura. Solo Presidencia puede editar los objetivos).*")
            st.dataframe(df_obj.style.format(thousands=","), hide_index=True, use_container_width=True)
