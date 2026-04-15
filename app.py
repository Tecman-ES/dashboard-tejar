import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

# --- ESTILOS PERSONALIZADOS (CSS) PARA NOTICIAS Y TARJETAS ---
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
    
    /* Estilo para las tablas de Streamlit (dataframe) */
    .stDataFrame [data-testid="stTable"] {
        font-variant-numeric: tabular-nums;
    }
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

# --- FUNCIONES DE FORMATO ---
def format_df_numbers(df):
    """Formatea todas las columnas numéricas de un DataFrame para mostrar separadores de miles"""
    styled_df = df.copy()
    for col in styled_df.columns:
        if pd.api.types.is_numeric_dtype(styled_df[col]):
            # Aplicar formato solo a números enteros o flotantes grandes (no a rendimientos pequeños como 0.41)
            if styled_df[col].mean() > 100:
                styled_df[col] = styled_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else x)
    return styled_df

# --- CARGA DE DATOS (EXCEL O DEMO) ---
def extract_table(df_raw, marker):
    """Extrae una sub-tabla de una hoja única buscando su marcador"""
    try:
        idx = df_raw[df_raw[0].astype(str).str.strip() == marker].index
        if len(idx) == 0: return pd.DataFrame()
        start_idx = idx[0]
        
        end_idx = len(df_raw)
        for i in range(start_idx + 1, len(df_raw)):
            val = str(df_raw.iloc[i, 0]).strip()
            if val.startswith('#') and val != marker:
                end_idx = i
                break
                
        df_sub = df_raw.iloc[start_idx+1:end_idx].dropna(how='all')
        if df_sub.empty: return pd.DataFrame()
        
        df_sub.columns = df_sub.iloc[0]
        df_sub = df_sub[1:]
        
        df_sub = df_sub.loc[:, df_sub.columns.notna()]
        for col in df_sub.columns:
            df_sub[col] = pd.to_numeric(df_sub[col], errors='ignore')
            
        return df_sub.dropna(how='all').reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file, header=None)
            else:
                df_raw = pd.read_excel(uploaded_file, header=None)
            
            df_aport = extract_table(df_raw, "# APORTACIONES")
            df_existencias = extract_table(df_raw, "# EXISTENCIAS")
            df_cent = extract_table(df_raw, "# CENTRIFUGACION")
            df_secado = extract_table(df_raw, "# SECADO")
            df_ext = extract_table(df_raw, "# EXTRACCION")
            df_elec = extract_table(df_raw, "# ELECTRICIDAD")
            
            st.sidebar.success("✅ Datos cargados correctamente")
            return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec
        except Exception as e:
            st.sidebar.error(f"Error al procesar el archivo. Detalle: {e}")
            st.sidebar.warning("Cargando datos de demostración como respaldo...")

    # DATOS DE DEMOSTRACIÓN (Fallback)
    st.sidebar.info("📊 Mostrando datos de demostración.")
    
    df_aport = pd.DataFrame({
        "Planta": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"],
        "Hoy (kg)": [682620, 76600, 882900, 107840, 333060, 228700, 54160, 64780],
        "Acum. Mensual": [10362240, 0, 9152660, 173220, 3579480, 2918540, 0, 2281940]
    })
    
    df_existencias = pd.DataFrame({
        "Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"],
        "Total Kilos": [27694950, 17150820, 57655131] # Cambiado a numérico para poder formatear
    })

    df_cent = pd.DataFrame({
        "Centro": ["Marchena", "Cabra", "Baena"],
        "Entrada_Alperujo": [461201, 67426, 631151],
        "Aceite_Prod": [1870, 632, 771],
        "Rdto_Obtenido": [0.41, 0.94, 0.12],
        "Media_Mensual": [0.46, 0.40, 0.30],
        "Optimo": [5251, 442, 1906],
        "Acidez": [2.92, 11.15, 7.81]
    })

    df_secado = pd.DataFrame({
        "Centro": ["Palenciana", "Marchena", "Cabra", "Baena", "Espejo"],
        "Entrada_Alperujo": [444668, 904664, 595175, 457958, 157546],
        "Obj_Entrada": [366157, 442175, 405077, 693266, 743865],
        "OGS_Salida": [134400, 221140, 161380, 110000, 22298],
        "Obj_OGS": [148900, 272720, 288560, 313160, 181020]
    })

    df_ext = pd.DataFrame({
        "Extractora": ["El Tejar", "Baena"],
        "OGS_Procesado": [570400, 110000],
        "Salida_Orujillo": [443740, 101700],
        "Aceite_Prod": [31800, 8300],
        "Obj_Aceite": [43400, 18900]
    })

    df_elec = pd.DataFrame({
        "Planta": ["Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW"],
        "Generada_kWh": [226344, 450634, 119229],
        "Optimo_kWh": [223608, 416169, 105737]
    })

    return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    
    # --- MENÚ LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.subheader("⚙️ Configuración del Reporte")
        fecha_reporte = st.date_input("Fecha del Parte Diario", date(2026, 4, 14))
        
        st.markdown("---")
        st.write("**Actualizar Datos:**")
        archivo_subido = st.file_uploader("Sube tu Archivo (.csv o .xlsx)", type=["csv", "xlsx", "xls"])
        
    df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec = load_data(archivo_subido)

    # --- HEADER ---
    st.title("📊 Panel Operativo - Oleícola El Tejar SCA")
    st.markdown(f"**Fecha de reporte:** {fecha_reporte.strftime('%d de %B de %Y')}")
    st.markdown("---")

    tabs = st.tabs([
        "👁️ Visión General", 
        "📦 Aportaciones y Existencias", 
        "🌀 Centrifugación", 
        "🔥 Secado", 
        "🗜️ Extracción", 
        "⚡ Electricidad"
    ])

    # ==========================================
    # PESTAÑA 1: VISIÓN GENERAL & NOTICIAS
    # ==========================================
    with tabs[0]:
        col_resumen, col_noticias = st.columns([2, 1])
        
        with col_resumen:
            st.subheader("Resumen Ejecutivo")
            c1, c2, c3 = st.columns(3)
            
            total_orujo = df_aport['Hoy (kg)'].sum() if not df_aport.empty and 'Hoy (kg)' in df_aport.columns else 2299900
            total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 870065
            total_aceite = (df_cent['Aceite_Prod'].sum() if not df_cent.empty and 'Aceite_Prod' in df_cent.columns else 0) + \
                           (df_ext['Aceite_Prod'].sum() if not df_ext.empty and 'Aceite_Prod' in df_ext.columns else 0)
            
            c1.metric("Orujo Aportado (Hoy)", f"{total_orujo:,.0f} kg")
            c2.metric("Electricidad Generada", f"{total_elec:,.0f} kWh")
            c3.metric("Aceite Obtenido Total", f"{total_aceite:,.0f} kg")
            
            st.write("<br>", unsafe_allow_html=True)
            st.write("**Alertas de Producción:**")
            st.warning("⚠️ **Centrifugación Cabra:** Acidez detectada del 11.15% (Rdto: 0.94%).")
            st.info("ℹ️ **Secado:** Parada técnica reportada en plantas Pedro Abad y Bogarre.")
            st.success("✅ **Electricidad:** Baena 25MW supera el rendimiento óptimo mensual esperado.")

        with col_noticias:
            st.subheader("📰 Actualidad del Sector")
            st.markdown("""
            <div class="news-card">
                <div class="news-title">El precio del AOVE se estabiliza en origen por encima de los 4 euros</div>
                <div class="news-source">Fuente: OleoMerca | 14 Abr 2026</div>
                <div class="news-snippet">
                    Tras semanas de volatilidad debido a las previsiones de lluvia en la cuenca del Guadalquivir, el mercado de origen muestra una estabilización. Las operaciones en picual de alta calidad se cierran en torno a los 4,20€/kg, dando un respiro a las extractoras...
                </div>
                <a href="#" class="read-more">Leer noticia completa →</a>
            </div>
            
            <div class="news-card">
                <div class="news-title">Nuevas regulaciones para la biomasa de orujillo en plantas de cogeneración</div>
                <div class="news-source">Fuente: Revista Alcuza | 13 Abr 2026</div>
                <div class="news-snippet">
                    El Ministerio de Transición Ecológica prepara un borrador que afectará a los consumos térmicos de las plantas andaluzas. Se premiará con incentivos fiscales a las cooperativas que mantengan un rendimiento energético superior al 85%...
                </div>
                <a href="#" class="read-more">Leer noticia completa →</a>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # PESTAÑA 2: APORTACIONES Y EXISTENCIAS
    # ==========================================
    with tabs[1]:
        st.subheader("Aportaciones de Socias y Acopios (Orujo)")
        
        c1, c2 = st.columns([3, 2])
        with c1:
            if not df_aport.empty and 'Hoy (kg)' in df_aport.columns and 'Planta' in df_aport.columns:
                fig_aport = px.bar(df_aport, x="Planta", y="Hoy (kg)", title="Orujo Aportado Hoy (kg)")
                # Formatear el texto de las barras para que tenga separadores de miles
                fig_aport.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8d6e63')
                # Formatear el eje Y
                fig_aport.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_aport, use_container_width=True)
            else:
                st.error("Falta la columna 'Hoy (kg)' o 'Planta' en la tabla Aportaciones.")
                
        with c2:
            st.write("**Total de Existencias Estratégicas:**")
            if not df_existencias.empty:
                st.dataframe(format_df_numbers(df_existencias), hide_index=True, use_container_width=True)
            st.metric("Total Aportado Hoy", f"{total_orujo:,.0f} kg")

    # ==========================================
    # PESTAÑA 3: CENTRIFUGACIÓN
    # ==========================================
    with tabs[2]:
        st.subheader("Rendimientos de Centrifugación")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Aceite Producido vs Óptimo Industrial (kg)**")
            if not df_cent.empty and all(col in df_cent.columns for col in ['Centro', 'Aceite_Prod', 'Optimo']):
                fig_cent_comp = go.Figure()
                fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Aceite_Prod'], name='Producido Real', marker_color='#fbbf24', text=df_cent['Aceite_Prod'], texttemplate='%{text:,.0f}', textposition='auto'))
                fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Optimo'], name='Óptimo Industrial', marker_color='#94a3b8', text=df_cent['Optimo'], texttemplate='%{text:,.0f}', textposition='auto'))
                fig_cent_comp.update_layout(barmode='group', yaxis=dict(tickformat=","))
                st.plotly_chart(fig_cent_comp, use_container_width=True)
            
        with col2:
            st.write("**Métricas Detalladas & Consumos**")
            if not df_cent.empty:
                cols_to_show = [col for col in ["Centro", "Entrada_Alperujo", "Rdto_Obtenido", "Media_Mensual", "Acidez"] if col in df_cent.columns]
                st.dataframe(format_df_numbers(df_cent[cols_to_show]), hide_index=True, use_container_width=True)
            
            st.write("**Consumos Diarios (Centrifugación):**")
            st.info("🔥 **Cabra:** 24,920 kg (Hueso) | **Baena:** 894 kg (Hueso)")

    # ==========================================
    # PESTAÑA 4: SECADO
    # ==========================================
    with tabs[3]:
        st.subheader("Líneas de Secado")

        c1, c2 = st.columns([2,1])
        with c1:
            st.write("**Orujo Graso Seco (OGS) - Salida vs Objetivo Diario (kg)**")
            if not df_secado.empty and all(col in df_secado.columns for col in ["Centro", "OGS_Salida", "Obj_OGS"]):
                fig_ogs = px.bar(df_secado, x="Centro", y=["OGS_Salida", "Obj_OGS"], barmode="group",
                                 labels={"value": "Kilos OGS", "variable": "Indicador"}, color_discrete_sequence=['#d97706', '#fcd34d'])
                fig_ogs.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_ogs, use_container_width=True)
        
        with c2:
            st.write("**Consumo Diario en Secado**")
            st.markdown("""
            * **Palenciana:** 79,240 kg (Hueso)
            * **Marchena:** 76,560 kg (Hueso)
            * **Baena:** 17,300 kg (Hueso)
            * **Espejo:** 6,700 kg (Hueso) + 177,000 kg (Poda)
            """)
            total_ogs = df_secado['OGS_Salida'].sum() if not df_secado.empty and 'OGS_Salida' in df_secado.columns else 649219
            st.metric("Disponibilidad Total Secado", f"{total_ogs:,.0f} kg OGS")

    # ==========================================
    # PESTAÑA 5: EXTRACCIÓN
    # ==========================================
    with tabs[4]:
        st.subheader("Extractora (Procesado Físico/Químico)")

        col_izq, col_der = st.columns(2)
        with col_izq:
            st.write("**Balance de Masas: OGS vs Orujillo Desgrasado (kg)**")
            if not df_ext.empty and all(col in df_ext.columns for col in ["Extractora", "OGS_Procesado", "Salida_Orujillo"]):
                fig_bal = px.bar(df_ext, x="Extractora", y=["OGS_Procesado", "Salida_Orujillo"], barmode="group",
                                 labels={"value": "Kilos", "variable": "Flujo"}, color_discrete_sequence=['#84cc16', '#4d7c0f'])
                fig_bal.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_bal, use_container_width=True)
            
        with col_der:
            st.write("**Producción de Aceite Industrial vs Objetivo (kg)**")
            if not df_ext.empty and all(col in df_ext.columns for col in ["Extractora", "Aceite_Prod", "Obj_Aceite"]):
                fig_aceite = px.bar(df_ext, x="Extractora", y=["Aceite_Prod", "Obj_Aceite"], barmode="group",
                                    labels={"value": "Kilos Aceite", "variable": "Indicador"}, color_discrete_sequence=['#eab308', '#fef08a'])
                fig_aceite.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_aceite, use_container_width=True)
            
            st.write("**Consumos Extractoras:**")
            st.info("🔥 **El Tejar:** 45,000 kg (Hueso)")

    # ==========================================
    # PESTAÑA 6: ELECTRICIDAD
    # ==========================================
    with tabs[5]:
        st.subheader("Generación y Cogeneración Eléctrica")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Producción kWh vs Objetivo Diario**")
            if not df_elec.empty and all(col in df_elec.columns for col in ["Planta", "Generada_kWh", "Optimo_kWh"]):
                fig_kwh = px.bar(df_elec, x="Planta", y=["Generada_kWh", "Optimo_kWh"], barmode="group",
                                 labels={"value": "Energía (kWh)", "variable": "Indicador"}, color_discrete_sequence=['#3b82f6', '#93c5fd'])
                fig_kwh.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig_kwh, use_container_width=True)
            
        with col2:
            st.write("**Consumo de Combustible**")
            st.error("🔥 **Baena 25 MW:** 66,033 kg (Orujillo)")
            
            st.metric("Total Generado Hoy", f"{total_elec:,.0f} kWh")
