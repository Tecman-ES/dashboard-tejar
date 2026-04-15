import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN CORPORATIVA ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🫒")

# --- 2. LOGIN DE ACCESO ---
def check_password():
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False
    if not st.session_state["login_ok"]:
        st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if usuario == "presidente" and password == "Tejar2026":
                st.session_state["login_ok"] = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

# --- 3. APLICACIÓN PRINCIPAL ---
if check_password():
    
    st.title("📊 Panel de Control Operativo - Oleícola El Tejar")
    st.markdown("**Cierre de operaciones: 14/04/2026**")
    st.markdown("---")

    # --- DATOS (Extraídos de tu Excel) ---
    # Existencias
    df_existencias = pd.DataFrame({
        "Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"],
        "Cantidad (kg)": [27694950, 17150820, 57655131]
    })
    
    # Centrifugación
    df_centrifugacion = pd.DataFrame({
        "Centro": ["Palenciana", "Marchena", "Cabra", "Baena"],
        "Alperujo_Entrada": [0, 461201, 67426, 631151],
        "Aceite_Salida": [0, 1870, 632, 771]
    })

    # Secado
    df_secado = pd.DataFrame({
        "Centro": ["Palenciana", "Marchena", "Cabra", "Baena", "Espejo"],
        "Orujo_Entrada": [444668, 904664, 595175, 457958, 157546],
        "Salida_Secado": [134400, 221140, 161380, 110000, 22298]
    })

    # Extracción
    df_extraccion = pd.DataFrame({
        "Extractora": ["El Tejar", "Baena", "Espejo", "P. Abad"],
        "Orujo_Entrada": [570400, 110000, 50578, 41317],
        "Prod_Aceite": [31800, 8300, 0, 0]
    })

    # Energía
    df_energia = pd.DataFrame({
        "Planta": ["Vetejar 12.6 MW", "Autogen 5.7 MW", "Baena 25 MW", "Algodonales 5.3 MW"],
        "Generado_kWh": [226344, 73858, 450634, 119229],
        "Optimo": [223608, 74199, 416169, 105737]
    })

    # --- CREACIÓN DE PESTAÑAS (TABS) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👁️ Visión General", 
        "🌀 Centrifugación", 
        "🔥 Secado", 
        "🗜️ Extracción", 
        "⚡ Generación Energía"
    ])

    # ==========================================
    # PESTAÑA 1: VISIÓN GENERAL
    # ==========================================
    with tab1:
        st.subheader("Resumen Ejecutivo Diario")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Aportación Total de Orujo", "2,299,900 kg")
        c2.metric("Total Electricidad Generada", "870,065 kWh", "+49,852 kWh s/óptimo")
        c3.metric("Aceite Total Extraído", "188,960 kg")
        c4.metric("Consumo Combustible Térmicas", "66,033 kg")

        st.markdown("---")
        col_graf, col_noticias = st.columns([2, 1])
        
        with col_graf:
            st.write("#### 📦 Distribución de Existencias (Stock Total)")
            fig_pie = px.pie(df_existencias, values='Cantidad (kg)', names='Material', hole=0.4,
                             color_discrete_sequence=['#eab308', '#475569', '#65a30d'])
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_noticias:
            st.write("#### 📰 Noticias del Sector")
            st.info("**IA Operativa:** La campaña muestra un sólido rendimiento energético, compensando paradas técnicas en extracción en P. Abad y Espejo.")
            st.markdown("""
            * [Análisis de los mercados del aceite de orujo](#)
            * [Cotización actual de la biomasa en Andalucía](#)
            * [Previsión meteorológica para la semana](#)
            """)

    # ==========================================
    # PESTAÑA 2: CENTRIFUGACIÓN
    # ==========================================
    with tab2:
        st.subheader("Área de Centrifugación")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("**Entrada de Alperujo por Centro (kg)**")
            fig_cent = px.bar(df_centrifugacion, x="Centro", y="Alperujo_Entrada", text_auto=True, color_discrete_sequence=['#2E7D32'])
            st.plotly_chart(fig_cent, use_container_width=True)
        with c2:
            st.write("**Salida de Aceite (kg) y Acidez**")
            st.dataframe(df_centrifugacion[["Centro", "Aceite_Salida"]], hide_index=True, use_container_width=True)
            st.warning("⚠️ Cabra: Acidez detectada del 11.15% (Rendimiento 0.94%).")
            st.metric("Consumo Diario Hueso (Centrif.)", "25,814 kg")

    # ==========================================
    # PESTAÑA 3: SECADO
    # ==========================================
    with tab3:
        st.subheader("Área de Secado")
        st.write("**Comparativa: Entrada de Orujo vs Salida de Secado (kg)**")
        fig_secado = px.bar(df_secado, x="Centro", y=["Orujo_Entrada", "Salida_Secado"], barmode="group",
                            labels={"value": "Kilos", "variable": "Fase"},
                            color_discrete_sequence=['#8d6e63', '#d7ccc8'])
        st.plotly_chart(fig_secado, use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entrada Secado", "2,560,015 kg")
        c2.metric("Total Salida Secado", "649,219 kg")
        c3.metric("Consumo Poda (Diario)", "177,000 kg", "Solo Espejo")

    # ==========================================
    # PESTAÑA 4: EXTRACCIÓN
    # ==========================================
    with tab4:
        st.subheader("Área de Extracción (Extractoras Químicas/Físicas)")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Producción de Aceite (kg)**")
            fig_ext = px.bar(df_extraccion, x="Extractora", y="Prod_Aceite", text_auto=True, color_discrete_sequence=['#eab308'])
            st.plotly_chart(fig_ext, use_container_width=True)
        with col2:
            st.write("**Detalle de Entradas de Orujo (kg)**")
            st.dataframe(df_extraccion[["Extractora", "Orujo_Entrada"]], hide_index=True, use_container_width=True)
            st.error("Extractora Espejo y P. Abad: 0 kg de Producción de Aceite reportada hoy.")
            st.metric("Consumo Diario Hueso (Extracción)", "45,000 kg", "Solo El Tejar")

    # ==========================================
    # PESTAÑA 5: GENERACIÓN DE ENERGÍA
    # ==========================================
    with tab5:
        st.subheader("Rendimiento de Plantas Eléctricas")
        st.write("**Generación Real vs Óptimo Teórico (kWh)**")
        
        fig_energia = px.bar(df_energia, x="Planta", y=["Generado_kWh", "Optimo"], barmode="group",
                             labels={"value": "kWh", "variable": "Métrica"},
                             color_discrete_sequence=['#1565C0', '#90CAF9'])
        st.plotly_chart(fig_energia, use_container_width=True)

        st.success("✅ **Excelencia Operativa:** La planta Baena 25 MW ha superado su óptimo por más de 34,000 kWh.")
        
        st.write("**Detalles Acumulados Anuales (kWh):**")
        df_acumulado = pd.DataFrame({
            "Planta": ["Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW", "Autogen 5.7 MW"],
            "Acumulado Anual": ["18,306,443", "39,646,324", "9,787,450", "6,769,072"]
        })
        st.table(df_acumulado)
