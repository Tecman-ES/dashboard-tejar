import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard Producción | El Tejar", layout="wide")

# --- 2. SISTEMA DE LOGIN PARA EL PRESIDENTE ---
def check_password():
    """Devuelve True si el usuario ingresó la contraseña correcta."""
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False

    if not st.session_state["login_ok"]:
        st.markdown("### 🔒 Acceso Restringido")
        st.write("Por favor, introduzca sus credenciales para ver el informe.")
        
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar"):
            # Aquí definimos el usuario y clave (Cámbialos a tu gusto)
            if usuario == "presidente" and password == "Tejar2026":
                st.session_state["login_ok"] = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        return False
    return True

# --- 3. APLICACIÓN PRINCIPAL (Solo se ve si hay login) ---
if check_password():
    
    st.title("📊 Panel de Control Directivo - Oleícola El Tejar")
    st.write("Datos actualizados al: **14/04/2026**")
    st.markdown("---")

    # DATOS SIMULADOS (Luego los cambiaremos por tu Google Sheet)
    datos_electricidad = pd.DataFrame({
        "Planta": ["Vetejar 12,6 MW", "Baena 25 MW", "Algodonales 5,3 MW"],
        "Produccion_Hoy": [226344, 450634, 119229],
        "Optimo": [223608, 416169, 105737]
    })

    datos_aceite = pd.DataFrame({
        "Planta": ["Marchena", "Cabra", "Baena"],
        "Produccion_Hoy": [1870, 632, 771],
        "Optimo": [5251, 442, 1906]
    })

    # --- SECCIÓN A: KPIs PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Orujo Aportado (Hoy)", value="2,299,900 kg")
    with col2:
        st.metric(label="Total Existencias Hueso", value="27,694,950 kg")
    with col3:
        st.metric(label="Electricidad Baena 25MW", value="450,634 kWh", delta="34,465 kWh (Sobre óptimo)")
    with col4:
        st.metric(label="Aceite Extractora Tejar", value="31,800 kg", delta="-11,600 kg (Bajo óptimo)", delta_color="inverse")

    st.markdown("---")

    # --- SECCIÓN B: GRÁFICOS Y ANÁLISIS ---
    col_graf1, col_graf2 = st.columns([2, 1]) # La columna izquierda es más grande

    with col_graf1:
        st.subheader("⚡ Generación Eléctrica vs Óptimo")
        # Gráfico de barras comparativo
        fig_elec = px.bar(datos_electricidad, x="Planta", y=["Produccion_Hoy", "Optimo"], 
                          barmode="group",
                          labels={"value": "kWh", "variable": "Indicador"})
        st.plotly_chart(fig_elec, use_container_width=True)

        st.subheader("🫒 Producción de Aceite vs Óptimo")
        fig_aceite = px.bar(datos_aceite, x="Planta", y=["Produccion_Hoy", "Optimo"], 
                            barmode="group",
                            labels={"value": "Kg", "variable": "Indicador"})
        st.plotly_chart(fig_aceite, use_container_width=True)

    with col_graf2:
        st.subheader("📰 Noticias del Sector")
        st.info("**Análisis de IA del día:** La planta de Baena ha tenido un rendimiento eléctrico excepcional hoy, superando el óptimo esperado. Sin embargo, se requiere revisión en la extractora de Marchena.")
        
        st.markdown("""
        **Últimas novedades:**
        * [Los precios del aceite de oliva virgen extra en origen...](#)
        * [Nuevas normativas para la quema de biomasa en Andalucía...](#)
        * [El mercado del orujillo prevé un alza para el próximo trimestre...](#)
        """)	
