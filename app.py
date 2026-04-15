import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import io
import csv

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

# --- ESTILOS PERSONALIZADOS (CSS) ---
st.markdown("""
<style>
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
    .read-more { color: #38bdf8; text-decoration: none; font-size: 0.85rem; font-weight: bold;}
    .stDataFrame [data-testid="stTable"] { font-variant-numeric: tabular-nums; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
def check_password():
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False
    if not st.session_state["login_ok"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.button("Entrar", use_container_width=True):
                if usuario == "presidente" and password == "Tejar2026":
                    st.session_state["login_ok"] = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        return False
    return True

# --- FUNCIONES DE FORMATO Y LIMPIEZA ---
def format_df_numbers(df):
    """Formatea columnas numéricas para mostrar separadores de miles"""
    styled_df = df.copy()
    for col in styled_df.columns:
        if pd.api.types.is_numeric_dtype(styled_df[col]):
            if styled_df[col].mean() > 100:
                styled_df[col] = styled_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")
    return styled_df

def fix_number(x):
    """Convierte números españoles y limpia comas fantasma de Excel"""
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

# --- CARGA ANTI-FALLOS ---
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
    except Exception as e:
        st.warning(f"Error procesando {marker}: {e}")
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
                data = list(reader)
                df_raw = pd.DataFrame(data).fillna('')
            else:
                df_raw = pd.read_excel(uploaded_file, header=None, dtype=str).fillna('')
            
            df_aport = extract_table(df_raw, "# APORTACIONES")
            df_existencias = extract_table(df_raw, "# EXISTENCIAS")
            df_cent = extract_table(df_raw, "# CENTRIFUGACION")
            df_secado = extract_table(df_raw, "# SECADO")
            df_ext = extract_table(df_raw, "# EXTRACCION")
            df_elec = extract_table(df_raw, "# ELECTRICIDAD")
            
            st.success("✅ Archivo leído y sincronizado perfectamente")
            return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec
        except Exception as e:
            st.error(f"Error grave: {e}")
            
    # DATOS DE DEMOSTRACIÓN
    st.info("📊 Mostrando datos de prueba. Sube tu archivo para ver los datos reales.")
    df_aport = pd.DataFrame({"Planta": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"], "Hoy (kg)": [682620, 76600, 882900, 107840, 333060, 228700, 54160, 64780]})
    df_existencias = pd.DataFrame({"Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"], "Total Kilos": [27694950, 17150820, 57655131]})
    df_cent = pd.DataFrame({"Centro": ["Marchena", "Cabra", "Baena"], "Entrada_Alperujo": [461201, 67426, 631151], "Aceite_Prod": [1870, 632, 771], "Rdto_Obtenido": [0.41, 0.94, 0.12], "Optimo": [5251, 442, 1906], "Acidez": [2.92, 11.15, 7.81]})
    df_secado = pd.DataFrame({"Centro": ["Palenciana", "Marchena", "Cabra", "Baena", "Espejo"], "Entrada_Alperujo": [444668, 904664, 595175, 457958, 157546], "OGS_Salida": [134400, 221140, 161380, 110000, 22298], "Obj_OGS": [148900, 272720, 288560, 313160, 181020]})
    df_ext = pd.DataFrame({"Extractora": ["El Tejar", "Baena"], "OGS_Procesado": [570400, 110000], "Salida_Orujillo": [443740, 101700], "Aceite_Prod": [31800, 8300], "Obj_Aceite": [43400, 18900]})
    df_elec = pd.DataFrame({"Planta": ["Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW"], "Generada_kWh": [226344, 450634, 119229], "Optimo_kWh": [223608, 416169, 105737]})
    return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    
    st.title("📊 Panel Operativo - Oleícola El Tejar SCA")
    
    # --- ÁREA DE CARGA DE DATOS ESTÁTICA ARRIBA ---
    with st.container():
        col_fecha, col_archivo = st.columns([1, 2])
        with col_fecha:
            fecha_reporte = st.date_input("📅 Fecha del Parte", date(2026, 4, 14))
        with col_archivo:
            archivo_subido = st.file_uploader("📂 Sube tu Archivo (.csv, .xlsx)", type=["xlsx", "xls", "csv"], label_visibility="visible")
    
    # Cargar datos
    df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec = load_data(archivo_subido)
    st.markdown("---")

    tabs = st.tabs(["👁️ Visión General", "📦 Aportaciones", "🌀 Centrifugación", "🔥 Secado", "🗜️ Extracción", "⚡ Electricidad"])

    # --- PESTAÑA 1: VISIÓN GENERAL ---
    with tabs[0]:
        col_resumen, col_noticias = st.columns([2, 1])
        with col_resumen:
            st.subheader("Resumen Ejecutivo")
            c1, c2, c3 = st.columns(3)
            
            total_orujo = df_aport['Hoy (kg)'].sum() if not df_aport.empty and 'Hoy (kg)' in df_aport.columns else 0
            total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 0
            total_aceite = (df_cent['Aceite_Prod'].sum() if not df_cent.empty and 'Aceite_Prod' in df_cent.columns else 0) + \
                           (df_ext['Aceite_Prod'].sum() if not df_ext.empty and 'Aceite_Prod' in df_ext.columns else 0)
            
            c1.metric("Orujo Aportado (Hoy)", f"{total_orujo:,.0f} kg")
            c2.metric("Electricidad Generada", f"{total_elec:,.0f} kWh")
            c3.metric("Aceite Obtenido Total", f"{total_aceite:,.0f} kg")
            
            st.write("<br>", unsafe_allow_html=True)
            st.warning("⚠️ **Centrifugación Cabra:** Revisar acidez en los rendimientos.")
            st.info("ℹ️ **Secado:** Analizar paradas en Pedro Abad y Bogarre.")

        with col_noticias:
            st.subheader("📰 Actualidad del Sector")
            st.markdown("""
            <div class="news-card">
                <div class="news-title">El precio del AOVE se estabiliza en origen</div>
                <div class="news-source">Fuente: OleoMerca | 14 Abr 2026</div>
                <div class="news-snippet">Las operaciones en picual de alta calidad se cierran en torno a los 4,20€/kg...</div>
            </div>
            """, unsafe_allow_html=True)

    # --- PESTAÑA 2: APORTACIONES ---
    with tabs[1]:
        st.subheader("Orujo Aportado Hoy (kg)")
        if not df_aport.empty and 'Planta' in df_aport.columns and 'Hoy (kg)' in df_aport.columns:
            fig_aport = px.bar(df_aport, x="Planta", y="Hoy (kg)")
            fig_aport.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8d6e63')
            fig_aport.update_layout(yaxis=dict(tickformat=","))
            st.plotly_chart(fig_aport, use_container_width=True)
        else: st.info("Faltan datos de Aportaciones en tu archivo.")
            
        st.write("### Tabla General de Aportaciones y Acumulados")
        if not df_aport.empty:
            st.dataframe(format_df_numbers(df_aport), hide_index=True, use_container_width=True)

        st.write("### Existencias Estratégicas")
        if not df_existencias.empty:
            st.dataframe(format_df_numbers(df_existencias), hide_index=True, use_container_width=True)

    # --- PESTAÑA 3: CENTRIFUGACIÓN ---
    with tabs[2]:
        st.subheader("Aceite Producido vs Óptimo Industrial (kg)")
        if not df_cent.empty and 'Centro' in df_cent.columns and 'Aceite_Prod' in df_cent.columns:
            fig_cent_comp = go.Figure()
            fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Aceite_Prod'], name='Producido', marker_color='#fbbf24', text=df_cent['Aceite_Prod'], texttemplate='%{text:,.0f}'))
            if 'Optimo' in df_cent.columns:
                fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Optimo'], name='Óptimo', marker_color='#94a3b8', text=df_cent['Optimo'], texttemplate='%{text:,.0f}'))
            fig_cent_comp.update_layout(barmode='group', yaxis=dict(tickformat=","))
            st.plotly_chart(fig_cent_comp, use_container_width=True)
        else: st.info("Faltan datos de Centrifugación en tu archivo.")
        
        st.markdown("---")
        st.write("### Métricas Detalladas (Tabla Completa)")
        st.write("*(Esta tabla ocupará todo el ancho y mostrará automáticamente cualquier columna nueva que añadas al Excel)*")
        if not df_cent.empty:
            st.dataframe(format_df_numbers(df_cent), hide_index=True, use_container_width=True)

    # --- PESTAÑA 4: SECADO ---
    with tabs[3]:
        st.subheader("Orujo Graso Seco (OGS) - Salida vs Objetivo (kg)")
        if not df_secado.empty and 'Centro' in df_secado.columns and 'OGS_Salida' in df_secado.columns:
            fig_ogs = px.bar(df_secado, x="Centro", y=["OGS_Salida", "Obj_OGS"] if 'Obj_OGS' in df_secado.columns else "OGS_Salida", barmode="group", color_discrete_sequence=['#d97706', '#fcd34d'])
            fig_ogs.update_layout(yaxis=dict(tickformat=","))
            st.plotly_chart(fig_ogs, use_container_width=True)
        else: st.info("Faltan datos de Secado en tu archivo.")
    
        total_ogs = df_secado['OGS_Salida'].sum() if not df_secado.empty and 'OGS_Salida' in df_secado.columns else 0
        st.metric("Total Secado Generado", f"{total_ogs:,.0f} kg")
        
        st.markdown("---")
        st.write("### Datos Completos de Secado")
        if not df_secado.empty:
            st.dataframe(format_df_numbers(df_secado), hide_index=True, use_container_width=True)

    # --- PESTAÑA 5: EXTRACCIÓN ---
    with tabs[4]:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.write("### Balance de Masas: OGS vs Orujillo (kg)")
            if not df_ext.empty and 'Extractora' in df_ext.columns and 'OGS_Procesado' in df_ext.columns:
                fig_bal = px.bar(df_ext, x="Extractora", y=["OGS_Procesado", "Salida_Orujillo"] if 'Salida_Orujillo' in df_ext.columns else "OGS_Procesado", barmode="group", color_discrete_sequence=['#84cc16', '#4d7c0f'])
                fig_bal.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_bal, use_container_width=True)
            
        with col_der:
            st.write("### Producción de Aceite vs Objetivo (kg)")
            if not df_ext.empty and 'Aceite_Prod' in df_ext.columns:
                fig_aceite = px.bar(df_ext, x="Extractora", y=["Aceite_Prod", "Obj_Aceite"] if 'Obj_Aceite' in df_ext.columns else "Aceite_Prod", barmode="group", color_discrete_sequence=['#eab308', '#fef08a'])
                fig_aceite.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_aceite, use_container_width=True)
                
        st.markdown("---")
        st.write("### Tabla de Extracción")
        if not df_ext.empty:
            st.dataframe(format_df_numbers(df_ext), hide_index=True, use_container_width=True)

    # --- PESTAÑA 6: ELECTRICIDAD ---
    with tabs[5]:
        st.subheader("Producción kWh vs Objetivo Diario")
        if not df_elec.empty and 'Planta' in df_elec.columns and 'Generada_kWh' in df_elec.columns:
            fig_kwh = px.bar(df_elec, x="Planta", y=["Generada_kWh", "Optimo_kWh"] if 'Optimo_kWh' in df_elec.columns else "Generada_kWh", barmode="group", color_discrete_sequence=['#3b82f6', '#93c5fd'])
            fig_kwh.update_layout(yaxis=dict(tickformat=","))
            st.plotly_chart(fig_kwh, use_container_width=True)
        else: st.info("Faltan datos eléctricos en tu archivo.")
        
        st.metric("Total Generado Hoy", f"{total_elec:,.0f} kWh")
        
        st.markdown("---")
        st.write("### Tabla de Electricidad")
        if not df_elec.empty:
            st.dataframe(format_df_numbers(df_elec), hide_index=True, use_container_width=True)
