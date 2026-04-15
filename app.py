import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

if check_password():
    # --- HEADER ---
    st.title("📊 Panel Operativo - Oleícola El Tejar SCA")
    st.markdown("**Fecha de reporte:** 14 de Abril de 2026")
    st.markdown("---")

    # --- PESTAÑAS ---
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
            c1.metric("Orujo Aportado (Hoy)", "2,299,900 kg")
            c2.metric("Electricidad Generada", "870,065 kWh", "+49,852 s/óptimo")
            c3.metric("Aceite Obtenido Total", "35,073 kg") # Suma de centrif + extracción
            
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
        df_aport = pd.DataFrame({
            "Planta": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"],
            "Hoy (kg)": [682620, 76600, 882900, 107840, 333060, 228700, 54160, 64780],
            "Acum. Mensual": [10362240, 0, 9152660, 173220, 3579480, 2918540, 0, 2281940]
        })
        
        c1, c2 = st.columns([3, 2])
        with c1:
            fig_aport = px.bar(df_aport, x="Planta", y="Hoy (kg)", text_auto='.2s', title="Orujo Aportado Hoy (kg)")
            fig_aport.update_traces(marker_color='#8d6e63')
            st.plotly_chart(fig_aport, use_container_width=True)
        with c2:
            st.write("**Total de Existencias Estratégicas:**")
            st.dataframe(pd.DataFrame({
                "Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"],
                "Total Kilos": ["27,694,950", "17,150,820", "57,655,131"]
            }), hide_index=True, use_container_width=True)
            st.metric("Total Aportado Hoy", "2,299,900 kg")

    # ==========================================
    # PESTAÑA 3: CENTRIFUGACIÓN
    # ==========================================
    with tabs[2]:
        st.subheader("Rendimientos de Centrifugación")
        
        df_cent = pd.DataFrame({
            "Centro": ["Marchena", "Cabra", "Baena"],
            "Entrada_Alperujo": [461201, 67426, 631151],
            "Aceite_Prod": [1870, 632, 771],
            "Rdto_Obtenido": [0.41, 0.94, 0.12],
            "Media_Mensual": [0.46, 0.40, 0.30],
            "Optimo": [5251, 442, 1906],
            "Acidez": [2.92, 11.15, 7.81]
        })

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Aceite Producido vs Óptimo Industrial**")
            fig_cent_comp = go.Figure()
            fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Aceite_Prod'], name='Producido Real', marker_color='#fbbf24'))
            fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Optimo'], name='Óptimo Industrial', marker_color='#94a3b8'))
            fig_cent_comp.update_layout(barmode='group')
            st.plotly_chart(fig_cent_comp, use_container_width=True)
            
        with col2:
            st.write("**Métricas Detalladas & Consumos**")
            st.dataframe(df_cent[["Centro", "Entrada_Alperujo", "Rdto_Obtenido", "Media_Mensual", "Acidez"]], hide_index=True, use_container_width=True)
            
            st.write("**Consumos Diarios (Centrifugación):**")
            st.info("🔥 **Cabra:** 24,920 kg (Hueso) | **Baena:** 894 kg (Hueso)")

    # ==========================================
    # PESTAÑA 4: SECADO
    # ==========================================
    with tabs[3]:
        st.subheader("Líneas de Secado")
        
        df_secado = pd.DataFrame({
            "Centro": ["Palenciana", "Marchena", "Cabra", "Baena", "Espejo"],
            "Entrada_Alperujo": [444668, 904664, 595175, 457958, 157546],
            "Obj_Entrada": [366157, 442175, 405077, 693266, 743865],
            "OGS_Salida": [134400, 221140, 161380, 110000, 22298],
            "Obj_OGS": [148900, 272720, 288560, 313160, 181020]
        })

        c1, c2 = st.columns([2,1])
        with c1:
            st.write("**Orujo Graso Seco (OGS) - Salida vs Objetivo Diario**")
            fig_ogs = px.bar(df_secado, x="Centro", y=["OGS_Salida", "Obj_OGS"], barmode="group",
                             labels={"value": "Kilos OGS"}, color_discrete_sequence=['#d97706', '#fcd34d'])
            st.plotly_chart(fig_ogs, use_container_width=True)
        
        with c2:
            st.write("**Consumo Diario en Secado**")
            st.markdown("""
            * **Palenciana:** 79,240 kg (Hueso)
            * **Marchena:** 76,560 kg (Hueso)
            * **Baena:** 17,300 kg (Hueso)
            * **Espejo:** 6,700 kg (Hueso) + 177,000 kg (Poda)
            """)
            st.metric("Disponibilidad Total Secado", "649,219 kg OGS", "Acumulado: 11,519,457 kg")

    # ==========================================
    # PESTAÑA 5: EXTRACCIÓN
    # ==========================================
    with tabs[4]:
        st.subheader("Extractora (Procesado Físico/Químico)")
        
        df_ext = pd.DataFrame({
            "Extractora": ["El Tejar", "Baena"],
            "OGS_Procesado": [570400, 110000],
            "Salida_Orujillo": [443740, 101700],
            "Aceite_Prod": [31800, 8300],
            "Obj_Aceite": [43400, 18900]
        })

        col_izq, col_der = st.columns(2)
        with col_izq:
            st.write("**Balance de Masas (OGS vs Orujillo Desgrasado)**")
            fig_bal = px.bar(df_ext, x="Extractora", y=["OGS_Procesado", "Salida_Orujillo"], barmode="group",
                             color_discrete_sequence=['#84cc16', '#4d7c0f'])
            st.plotly_chart(fig_bal, use_container_width=True)
            
        with col_der:
            st.write("**Producción de Aceite Industrial vs Objetivo**")
            fig_aceite = px.bar(df_ext, x="Extractora", y=["Aceite_Prod", "Obj_Aceite"], barmode="group",
                                color_discrete_sequence=['#eab308', '#fef08a'])
            st.plotly_chart(fig_aceite, use_container_width=True)
            
            st.write("**Consumos Extractoras:**")
            st.info("🔥 **El Tejar:** 45,000 kg (Hueso)")

    # ==========================================
    # PESTAÑA 6: ELECTRICIDAD
    # ==========================================
    with tabs[5]:
        st.subheader("Generación y Cogeneración Eléctrica")
        
        df_elec = pd.DataFrame({
            "Planta": ["Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW"],
            "Generada_kWh": [226344, 450634, 119229],
            "Optimo_kWh": [223608, 416169, 105737]
        })

        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Producción kWh vs Objetivo Diario**")
            fig_kwh = px.bar(df_elec, x="Planta", y=["Generada_kWh", "Optimo_kWh"], barmode="group",
                             color_discrete_sequence=['#3b82f6', '#93c5fd'])
            st.plotly_chart(fig_kwh, use_container_width=True)
            
        with col2:
            st.write("**Consumo de Combustible**")
            st.error("🔥 **Baena 25 MW:** 66,033 kg (Orujillo)")
            
            st.write("**Acumulado Mensual:**")
            st.dataframe(pd.DataFrame({
                "Planta": ["Vetejar", "Baena", "Algodonales"],
                "Mes (kWh)": ["2,635,700", "6,224,221", "1,389,457"]
            }), hide_index=True)
            st.metric("Total Generado Hoy", "870,065 kWh")
